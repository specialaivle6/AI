"""
통합 리포트 서비스
new_service의 report_service.py와 동일한 기능 구현
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List, Tuple

import json
import os
import numpy as np
import pandas as pd

from app.schemas.schemas import PanelRequest
from app.schemas.model_features import MODEL_FEATURES
from app.utils.performance_utils import (
    find_nearest_region,
    get_model_specs,
    canonicalize_model_name,
    estimate_cost,
    CostEstimate,
)
from app.utils.report_generator import generate_report, estimate_lifespan
from app.core.exceptions import PerformanceAnalysisException

logger = logging.getLogger(__name__)


class ReportService:
    """통합 리포트 생성 서비스"""

    def __init__(self, model=None):
        self.model = model
        self.model_features = MODEL_FEATURES

    def _avg(self, v):
        return (sum(v) / len(v)) if v else 0.0

    def preprocess_features(self, data: PanelRequest) -> Dict[str, float]:
        """입력 + CSV 스펙/지역정보로 학습 피처 한 줄 생성"""
        model_name = canonicalize_model_name(data.model_name)

        avg_temp = self._avg(data.temp)
        avg_humidity = self._avg(data.humidity)
        avg_windspeed = self._avg(data.windspeed)
        avg_sunshine = self._avg(data.sunshine)

        install_date = pd.to_datetime(data.installed_at)
        elapsed_months = (pd.Timestamp.now() - install_date).days // 30
        nearest_region = find_nearest_region(data.lat, data.lon)

        pmp = data.pmp_rated_w or 0
        tcoef = data.temp_coeff or 0
        degr = data.annual_degradation_rate or 0

        if pmp == 0 or tcoef == 0 or degr == 0:
            spec = get_model_specs(model_name)
            if spec:
                pmp = pmp or spec.get("PMPP_rated_W", 0)
                tcoef = tcoef or spec.get("Temp_Coeff_per_K", 0)
                degr = degr or spec.get("Annual_Degradation_Rate", 0)

        features = {
            "PMPP_rated_W": pmp,
            "Temp_Coeff_per_K": tcoef,
            "Annual_Degradation_Rate": degr,
            "Install_Angle": data.installed_angle,
            "Avg_Temp": avg_temp,
            "Avg_Humidity": avg_humidity,
            "Avg_Windspeed": avg_windspeed,
            "Avg_Sunshine": avg_sunshine,
            "Elapsed_Months": elapsed_months,
        }

        # 원-핫 인코딩
        for col in self.model_features:
            if col.startswith("Panel_Model_"):
                features[col] = 1 if col == f"Panel_Model_{model_name}" else 0
            elif col.startswith("Region_"):
                features[col] = 1 if col == nearest_region else 0
            elif col.startswith("Install_Direction_"):
                features[col] = 1 if col == f"Install_Direction_{data.installed_direction}" else 0

        return features

    def _feature_snapshot(self, data: PanelRequest, features: dict) -> dict:
        return {
            "numeric": {
                "PMPP_rated_W": features.get("PMPP_rated_W"),
                "Temp_Coeff_per_K": features.get("Temp_Coeff_per_K"),
                "Annual_Degradation_Rate": features.get("Annual_Degradation_Rate"),
                "Install_Angle": features.get("Install_Angle"),
                "Avg_Temp": features.get("Avg_Temp"),
                "Avg_Humidity": features.get("Avg_Humidity"),
                "Avg_Windspeed": features.get("Avg_Windspeed"),
                "Avg_Sunshine": features.get("Avg_Sunshine"),
                "Elapsed_Months": features.get("Elapsed_Months"),
            },
            "categorical": {
                "Panel_Model": data.model_name,
                "Install_Direction": data.installed_direction,
                "Region": next(
                    (c.replace("Region_", "") for c, v in features.items() if c.startswith("Region_") and v == 1),
                    "",
                ),
            },
        }

    def _load_model_metrics(self) -> dict:
        meta_path = Path("models") / "voting_ensemble_model.meta.json"
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                m = json.load(f)
            return {
                "RMSE_kWh": m.get("rmse"),
                "MAE_kWh": m.get("mae"),
                "R2": m.get("r2"),
                "version": m.get("version"),
                "trained_at": m.get("trained_at"),
            }
        return {"RMSE_kWh": None, "MAE_kWh": None, "R2": None, "version": None, "trained_at": None}

    def _explain_top_impacts(self, df_row, k: int = 5, prefer_numeric: bool = True) -> list:
        """
        상위 중요 피처 산출.
        1) SHAP 사용
        2) 실패 시 국소 민감도(한 샘플에서 피처를 조금 변경)로 fallback
           - prefer_numeric=True : 원-핫(Panel_Model_/Install_Direction_/Region_) 제외
           - prefer_numeric=False: 원-핫은 활성된 카테고리만 고려
        반환: [(feature_name, signed_effect), ...]
        """
        import pandas as pd

        X = df_row if isinstance(df_row, pd.DataFrame) else pd.DataFrame(df_row).iloc[[0]]
        cols = list(X.columns)

        # 1) SHAP
        contrib = None
        try:
            import shap
            try:
                explainer = shap.TreeExplainer(self.model)
                sv = explainer.shap_values(X)
                values = np.array(sv[0]) if isinstance(sv, list) else np.array(sv)[0]
            except Exception:
                explainer = shap.Explainer(self.model)
                exp = explainer(X)
                values = np.array(exp.values)[0]
            contrib = {c: float(values[i]) for i, c in enumerate(cols)}
        except Exception:
            pass

        # 2) fallback
        if contrib is None:
            base_pred = float(self.model.predict(X)[0])

            def _pred_delta(x_alt):
                try:
                    return float(self.model.predict(x_alt)[0]) - base_pred
                except Exception:
                    return None

            contrib = {}
            for c in cols:
                is_onehot = c.startswith("Panel_Model_") or c.startswith("Install_Direction_") or c.startswith("Region_")

                if not is_onehot:
                    # 수치형
                    try:
                        val = float(X.iloc[0, X.columns.get_loc(c)])
                    except Exception:
                        continue
                    eps = 0.05 * (abs(val) if abs(val) > 1e-9 else 1.0)
                    x_alt = X.copy()
                    x_alt.iloc[0, x_alt.columns.get_loc(c)] = val + eps
                    d = _pred_delta(x_alt)
                    if d is not None:
                        contrib[c] = float(d)
                    continue

                # one-hot
                if prefer_numeric:
                    continue
                if X.iloc[0, X.columns.get_loc(c)] != 1:
                    continue
                prefix = "Panel_Model_" if c.startswith("Panel_Model_") else (
                    "Install_Direction_" if c.startswith("Install_Direction_") else "Region_"
                )
                group = [g for g in cols if g.startswith(prefix)]
                x_alt = X.copy()
                for g in group:
                    x_alt.iloc[0, x_alt.columns.get_loc(g)] = 1.0 if g == c else 0.0
                d = _pred_delta(x_alt)
                if d is not None:
                    contrib[c] = float(d)

        items = list(contrib.items())
        if prefer_numeric:
            items = [
                (k2, v2)
                for k2, v2 in items
                if not (k2.startswith("Panel_Model_") or k2.startswith("Install_Direction_") or k2.startswith("Region_"))
            ]
        items.sort(key=lambda t: abs(t[1]), reverse=True)
        return items[:k]

    def _decision_breakdown(self, predicted, actual, ratio) -> dict:
        return {
            "rules": [
                "actual ≥ predicted → 우수",
                "ratio ≥ 0.8 → 정상",
                "ratio < 0.8 → 불량(이미지 검사 권장)",
            ],
            "ratio": round(ratio, 3),
            "distance_to_threshold_0_8": round(ratio - 0.8, 3),
            "is_above_expected": actual >= predicted,
        }

    def process_report(self, data: PanelRequest) -> Dict[str, Any]:
        """전처리 → 예측 → 상태판정 → 비용계산 → PDF 생성 → 응답"""
        try:
            if not self.model:
                raise PerformanceAnalysisException("모델이 로드되지 않았습니다", data.user_id)

            # 1) 전처리
            features = self.preprocess_features(data)
            df = pd.DataFrame([features]).reindex(columns=self.model_features).fillna(0)

            # 2) 예측
            predicted = float(self.model.predict(df)[0])
            actual = float(data.actual_generation)
            ratio = (actual / predicted) if predicted > 0 else 0.0

            install_date = pd.to_datetime(data.installed_at)
            now = pd.Timestamp.now()

            # 3) 상태 + 수명
            if actual > predicted:
                status = "Excellent (Performance above expected)"
                lifespan = estimate_lifespan(predicted, actual, install_date, now)
            elif ratio >= 0.8:
                status = "Healthy (Performance within normal range)"
                lifespan = estimate_lifespan(predicted, actual, install_date, now)
            else:
                status = "Degraded (Requires image inspection)"
                lifespan = None

            # 4) 비용
            cost = estimate_cost(data.model_name, status, lifespan)

            # 5) extras (패널 정보/스냅샷/중요도)
            model_name = canonicalize_model_name(data.model_name)

            # 패널 스펙 보강
            pmp = data.pmp_rated_w or 0
            tcoef = data.temp_coeff or 0
            degr = data.annual_degradation_rate or 0
            if pmp == 0 or tcoef == 0 or degr == 0:
                spec = get_model_specs(model_name)
                if spec:
                    pmp = pmp or spec.get("PMPP_rated_W", 0)
                    tcoef = tcoef or spec.get("Temp_Coeff_per_K", 0)
                    degr = degr or spec.get("Annual_Degradation_Rate", 0)

            region_full = find_nearest_region(data.lat, data.lon)
            region_name = region_full.replace("Region_", "") if isinstance(region_full, str) else str(region_full)

            panel_info = {
                "model_name": model_name,
                "serial_number": data.serial_number,
                "rated_power_w": pmp,
                "temperature_coefficient": tcoef,
                "degradation_rate": degr,
                "installation": {
                    "date": data.installed_at,
                    "angle": data.installed_angle,
                    "direction": data.installed_direction,
                    "location": {"latitude": data.lat, "longitude": data.lon},
                },
            }

            feature_snapshot = {
                "numeric": {
                    "PMPP_rated_W": pmp,
                    "Temp_Coeff_per_K": tcoef,
                    "Annual_Degradation_Rate": degr,
                    "Install_Angle": data.installed_angle,
                    "Avg_Temp": self._avg(getattr(data, "temp", []) or []),
                    "Avg_Humidity": self._avg(getattr(data, "humidity", []) or []),
                    "Avg_Windspeed": self._avg(getattr(data, "windspeed", []) or []),
                    "Avg_Sunshine": self._avg(getattr(data, "sunshine", []) or []),
                },
                "categorical": {
                    "Panel_Model": model_name,
                    "Install_Direction": data.installed_direction,
                    "Region": region_name,
                },
            }

            top_impacts = self._explain_top_impacts(df, k=5, prefer_numeric=True)

            extras = {
                "panel_info": panel_info,
                "feature_snapshot": feature_snapshot,
                "top_impacts": top_impacts,
                # "model_metrics": self._load_model_metrics(),  # 필요시 활성화
            }

            # 6) 리포트 생성
            report_path = generate_report(
                predicted=predicted,
                actual=actual,
                status=status,
                user_id=data.user_id,
                lifespan=lifespan,
                cost=cost,
                extras=extras,
            )

            return {
                "user_id": data.user_id,
                "predicted_generation": predicted,
                "actual_generation": actual,
                "performance_ratio": ratio,
                "status": status,
                "lifespan_years": lifespan,
                "cost_estimate": {
                    "immediate_cost": cost.immediate_cost,
                    "future_cost_year": cost.future_cost_year,
                    "future_cost_total": cost.future_cost_total,
                },
                "report_path": report_path,
                "created_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"리포트 처리 중 오류: {str(e)}")
            raise PerformanceAnalysisException(f"리포트 생성 실패: {str(e)}", data.user_id)
