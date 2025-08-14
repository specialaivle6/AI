"""
통합 리포트 서비스
new_service의 report_service.py와 동일한 기능 구현
"""

import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional
import logging

from app.models.schemas import PanelRequest
from app.models.model_features import MODEL_FEATURES
from app.utils.performance_utils import (
    find_nearest_region, get_model_specs, canonicalize_model_name,
    estimate_cost, CostEstimate
)
from app.utils.report_generator import generate_report, estimate_lifespan
from app.core.exceptions import PerformanceAnalysisException

logger = logging.getLogger(__name__)

# 예측 모델의 피처 순서 (학습 시 원-핫 열 순서와 동일해야 함)
class ReportService:
    """통합 리포트 생성 서비스"""

    def __init__(self, model=None):
        """
        Args:
            model: 성능 예측 모델 (joblib로 로드된 모델)
        """
        self.model = model
        self.model_features = MODEL_FEATURES

    def _avg(self, v):
        """평균값 계산"""
        return (sum(v) / len(v)) if v else 0.0

    def preprocess_features(self, data: PanelRequest) -> Dict[str, float]:
        """입력 + CSV 스펙/지역정보로 학습 피처 한 줄 생성"""
        # 모델명 정규화(별칭 매핑)
        model_name = canonicalize_model_name(data.model_name)

        # 환경 평균치
        avg_temp = self._avg(data.temp)
        avg_humidity = self._avg(data.humidity)
        avg_windspeed = self._avg(data.windspeed)
        avg_sunshine = self._avg(data.sunshine)

        install_date = pd.to_datetime(data.installed_at)
        elapsed_months = (pd.Timestamp.now() - install_date).days // 30
        nearest_region = find_nearest_region(data.lat, data.lon)

        # 스펙 자동 보정 (0/None이면 CSV/엑셀에서 보강)
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

        # 원-핫 인코딩(모델/방향/지역)
        for col in self.model_features:
            if "Panel_Model_" in col:
                features[col] = 1 if col == f"Panel_Model_{model_name}" else 0
            elif "Region_" in col:
                features[col] = 1 if col == nearest_region else 0
            elif "Install_Direction_" in col:
                features[col] = 1 if col == f"Install_Direction_{data.installed_direction}" else 0

        return features

    def process_report(self, data: PanelRequest) -> Dict[str, Any]:
        """전처리 → 예측 → 상태판정 → 비용계산 → PDF 생성 → 응답"""
        try:
            if not self.model:
                raise PerformanceAnalysisException("모델이 로드되지 않았습니다", data.user_id)

            # 1. 전처리
            features = self.preprocess_features(data)
            df = pd.DataFrame([features]).reindex(columns=self.model_features).fillna(0)

            # 2. 예측
            predicted = float(self.model.predict(df)[0])
            actual = float(data.actual_generation)
            performance_ratio = (actual / predicted) if predicted > 0 else 0.0

            install_date = pd.to_datetime(data.installed_at)
            current_date = pd.Timestamp.now()

            # 3. 상태 판정 + 수명
            lifespan = None
            if actual > predicted:
                status = "Excellent (Performance above expected)"
                lifespan = estimate_lifespan(predicted, actual, install_date, current_date)
            elif performance_ratio >= 0.8:
                status = "Healthy (Performance within normal range)"
                lifespan = estimate_lifespan(predicted, actual, install_date, current_date)
            else:
                status = "Degraded (Requires image inspection)"

            # 4. 비용 계산 (정상/우수는 미래 예측, 성능저하는 즉시 비용)
            cost = estimate_cost(data.model_name, status, lifespan)

            # 5. PDF 생성
            report_path = generate_report(
                predicted=predicted,
                actual=actual,
                status=status,
                user_id=data.user_id,
                lifespan=lifespan,
                cost=cost
            )

            return {
                "user_id": data.user_id,
                "predicted_generation": predicted,
                "actual_generation": actual,
                "performance_ratio": performance_ratio,
                "status": status,
                "lifespan_years": lifespan,
                "cost_estimate": {
                    "immediate_cost": cost.immediate_cost,
                    "future_cost_year": cost.future_cost_year,
                    "future_cost_total": cost.future_cost_total,
                },
                "report_path": report_path,
                "created_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"리포트 처리 중 오류: {str(e)}")
            raise PerformanceAnalysisException(f"리포트 생성 실패: {str(e)}", data.user_id)
