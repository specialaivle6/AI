"""
태양광 패널 성능 예측 및 분석 서비스
개선된 설정 시스템과 예외 처리 적용
"""

import pandas as pd
import numpy as np
import joblib
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio
import time

# 개선된 임포트
from app.core.config import settings
from app.core.exceptions import (
    ModelLoadFailedException, PerformanceAnalysisException,
    TimeoutException
)
from app.core.logging_config import get_logger, log_analysis_result, log_performance

from app.models.schemas import PanelRequest, PerformanceAnalysisResult, PerformanceReportResponse
from app.models.model_features import MODEL_FEATURES

logger = get_logger(__name__)


class PerformanceAnalyzer:
    """태양광 패널 성능 예측 및 분석기"""

    def __init__(self):
        self.model = None
        self.is_model_loaded = False
        self.model_path = settings.performance_model_path
        self.model_features = MODEL_FEATURES

    async def initialize(self):
        """모델 초기화 및 로딩"""
        try:
            logger.info(f"성능 예측 모델 로딩 시작: {self.model_path}")

            if not Path(self.model_path).exists():
                raise ModelLoadFailedException(
                    "PerformanceAnalyzer",
                    self.model_path,
                    "모델 파일이 존재하지 않습니다"
                )

            # 비동기적으로 모델 로드
            loop = asyncio.get_event_loop()
            await asyncio.wait_for(
                loop.run_in_executor(None, self._load_model),
                timeout=settings.performance_analysis_timeout
            )

            self.is_model_loaded = True
            logger.info("✅ 성능 예측 모델 로딩 완료")

        except asyncio.TimeoutError:
            raise TimeoutException("성능 예측 모델 로딩", settings.performance_analysis_timeout)
        except Exception as e:
            logger.error(f"성능 예측 모델 로딩 실패: {str(e)}")
            raise ModelLoadFailedException("PerformanceAnalyzer", self.model_path, str(e))

    def _load_model(self):
        """실제 모델 로딩 (동기 함수)"""
        try:
            self.model = joblib.load(self.model_path)
            logger.info("성능 예측 모델 로드 완료")
        except Exception as e:
            raise Exception(f"성능 예측 모델 로드 실패: {str(e)}")

    def is_loaded(self) -> bool:
        """모델 로딩 상태 확인"""
        return self.is_model_loaded and self.model is not None

    async def analyze_performance(self, request: PanelRequest) -> Dict[str, Any]:
        """
        성능 예측 분석 수행

        Args:
            request: 패널 요청 데이터

        Returns:
            Dict: 분석 결과
        """
        start_time = time.time()

        if not self.is_loaded():
            raise PerformanceAnalysisException("모델이 로드되지 않았습니다", request.user_id)

        try:
            # 입력 데이터 전처리
            features_df = self._prepare_features(request)

            # 성능 예측 수행
            try:
                loop = asyncio.get_event_loop()
                predicted_generation = await asyncio.wait_for(
                    loop.run_in_executor(None, self._predict_performance, features_df),
                    timeout=settings.performance_analysis_timeout
                )
            except asyncio.TimeoutError:
                raise TimeoutException("성능 예측", settings.performance_analysis_timeout)

            # 성능 분석 및 평가
            analysis_result = self._analyze_performance_result(
                predicted_generation, request.actual_generation, request
            )

            processing_time = time.time() - start_time

            # 로깅
            log_analysis_result(
                "Performance Analysis",
                True,
                processing_time,
                user_id=request.user_id,
                panel_id=request.id,
                performance_ratio=f"{analysis_result['performance_ratio']:.2f}"
            )

            return analysis_result

        except (PerformanceAnalysisException, TimeoutException):
            raise
        except Exception as e:
            processing_time = time.time() - start_time
            log_analysis_result(
                "Performance Analysis",
                False,
                processing_time,
                user_id=request.user_id,
                error=str(e)
            )
            raise PerformanceAnalysisException(f"성능 분석 처리 중 오류: {str(e)}", request.user_id)

    def _prepare_features(self, request: PanelRequest) -> pd.DataFrame:
        """모델 입력을 위한 피처 준비"""
        try:
            # 기본 피처 준비
            base_features = {
                'PMPP_rated_W': request.pmp_rated_w,
                'Temp_Coeff_per_K': request.temp_coeff,
                'Annual_Degradation_Rate': request.annual_degradation_rate,
                'Install_Angle': request.installed_angle,
                'Avg_Temp': np.mean(request.temp),
                'Avg_Humidity': np.mean(request.humidity),
                'Avg_Windspeed': np.mean(request.windspeed),
                'Avg_Sunshine': np.mean(request.sunshine),
                'Elapsed_Months': self._calculate_elapsed_months(request.installed_at)
            }

            # 원-핫 인코딩된 피처들 초기화
            feature_vector = {feature: 0 for feature in self.model_features}

            # 기본 피처 설정
            for key, value in base_features.items():
                if key in feature_vector:
                    feature_vector[key] = value

            # 패널 모델 원-핫 인코딩
            panel_model_feature = f"Panel_Model_{request.model_name}"
            if panel_model_feature in feature_vector:
                feature_vector[panel_model_feature] = 1

            # 설치 방향 원-핫 인코딩
            direction_feature = f"Install_Direction_{request.installed_direction}"
            if direction_feature in feature_vector:
                feature_vector[direction_feature] = 1

            # 지역 원-핫 인코딩 (위도/경도 기반)
            region = self._determine_region(request.lat, request.lon)
            region_feature = f"Region_{region}"
            if region_feature in feature_vector:
                feature_vector[region_feature] = 1

            # DataFrame으로 변환 (모델이 기대하는 순서대로)
            feature_df = pd.DataFrame([feature_vector])
            feature_df = feature_df[self.model_features]  # 올바른 순서로 정렬

            return feature_df

        except Exception as e:
            raise Exception(f"피처 준비 실패: {str(e)}")

    def _predict_performance(self, features_df: pd.DataFrame) -> float:
        """성능 예측 실행"""
        try:
            prediction = self.model.predict(features_df)[0]
            return max(0.0, float(prediction))  # 음수 방지
        except Exception as e:
            raise Exception(f"성능 예측 실행 실패: {str(e)}")

    def _analyze_performance_result(
        self,
        predicted: float,
        actual: float,
        request: PanelRequest
    ) -> Dict[str, Any]:
        """성능 예측 결과 분석"""
        try:
            # 성능 비율 계산
            performance_ratio = actual / predicted if predicted > 0 else 0.0

            # 성능 상태 판정 (설정 기반)
            status = self._determine_performance_status(performance_ratio)

            # 수명 예측
            lifespan_months = self._estimate_lifespan(performance_ratio, request)

            # 비용 추정
            estimated_cost = self._estimate_replacement_cost(request.pmp_rated_w)

            # 메타데이터 구성
            panel_info = self._create_panel_info(request)
            environmental_data = self._create_environmental_data(request)

            return {
                "predicted_generation": round(predicted, 2),
                "actual_generation": round(actual, 2),
                "performance_ratio": round(performance_ratio, 3),
                "status": status,
                "lifespan_months": lifespan_months,
                "estimated_cost": estimated_cost,
                "panel_info": panel_info,
                "environmental_data": environmental_data
            }

        except Exception as e:
            raise Exception(f"성능 결과 분석 실패: {str(e)}")

    def _determine_performance_status(self, performance_ratio: float) -> str:
        """성능 상태 판정 (설정 기반)"""
        constants = settings.PerformanceConstants

        if performance_ratio >= constants.STATUS_EXCELLENT:
            return "우수"
        elif performance_ratio >= constants.STATUS_GOOD:
            return "양호"
        elif performance_ratio >= constants.STATUS_FAIR:
            return "보통"
        elif performance_ratio >= constants.STATUS_POOR:
            return "미흡"
        else:
            return "불량"

    def _estimate_lifespan(self, performance_ratio: float, request: PanelRequest) -> Optional[float]:
        """잔여 수명 예측"""
        try:
            elapsed_months = self._calculate_elapsed_months(request.installed_at)
            expected_lifespan = settings.PerformanceConstants.EXPECTED_LIFESPAN_MONTHS

            # 성능 기반 수명 조정
            if performance_ratio > 0.9:
                remaining = expected_lifespan - elapsed_months
            elif performance_ratio > 0.8:
                remaining = (expected_lifespan - elapsed_months) * 0.8
            elif performance_ratio > 0.7:
                remaining = (expected_lifespan - elapsed_months) * 0.6
            else:
                remaining = (expected_lifespan - elapsed_months) * 0.4

            return max(0.0, remaining)

        except Exception:
            return None

    def _estimate_replacement_cost(self, rated_power: float) -> Optional[int]:
        """교체 비용 추정"""
        try:
            # 와트당 비용 (원/W) - 설치비 포함 대략적 추정
            cost_per_watt = 2000  # 2,000원/W
            return int(rated_power * cost_per_watt)
        except Exception:
            return None

    def _calculate_elapsed_months(self, installed_at: str) -> float:
        """설치일로부터 경과 개월 수 계산"""
        try:
            install_date = datetime.strptime(installed_at, "%Y-%m-%d")
            current_date = datetime.now()
            delta = current_date - install_date
            return delta.days / 30.44  # 평균 월일 수
        except Exception:
            return 0.0

    def _determine_region(self, lat: float, lon: float) -> str:
        """위도/경도 기반 지역 판정"""
        # 간단한 지역 분류 (실제로는 더 정교한 로직 필요)
        if lat > 37.5:
            return "Seoul"
        elif lat > 36.0:
            return "Daejeon"
        elif lat > 35.0:
            return "Daegu"
        else:
            return "Busan"

    def _create_panel_info(self, request: PanelRequest) -> Dict[str, Any]:
        """패널 정보 메타데이터 생성"""
        return {
            "model_name": request.model_name,
            "serial_number": request.serial_number,
            "rated_power_w": request.pmp_rated_w,
            "temperature_coefficient": request.temp_coeff,
            "degradation_rate": request.annual_degradation_rate,
            "installation": {
                "date": request.installed_at,
                "angle": request.installed_angle,
                "direction": request.installed_direction,
                "location": {
                    "latitude": request.lat,
                    "longitude": request.lon
                }
            }
        }

    def _create_environmental_data(self, request: PanelRequest) -> Dict[str, Any]:
        """환경 데이터 메타데이터 생성"""
        return {
            "temperature": {
                "average": round(np.mean(request.temp), 1),
                "min": round(np.min(request.temp), 1),
                "max": round(np.max(request.temp), 1)
            },
            "humidity": {
                "average": round(np.mean(request.humidity), 1),
                "min": round(np.min(request.humidity), 1),
                "max": round(np.max(request.humidity), 1)
            },
            "wind_speed": {
                "average": round(np.mean(request.windspeed), 1),
                "min": round(np.min(request.windspeed), 1),
                "max": round(np.max(request.windspeed), 1)
            },
            "sunshine": {
                "average": round(np.mean(request.sunshine), 1),
                "total": round(np.sum(request.sunshine), 1)
            }
        }
