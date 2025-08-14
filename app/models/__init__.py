"""
Models Package - AI 모델 관련 모듈

YOLOv8 모델 로더 및 관리 기능을 위한 패키지입니다.
향후 다양한 AI 모델들의 로더와 매니저가 추가될 예정입니다.
"""

# 향후 모델 로더들이 추가될 예정
__all__ = []

"""
Models Package - 데이터 모델 및 스키마

태양광 패널 AI 서비스를 위한 Pydantic 모델들과 API 스키마를 포함합니다.
백엔드 연동, 손상 분석, 성능 예측을 위한 모든 데이터 구조를 정의합니다.
"""

from .schemas import (
    # Enum 타입들
    PanelStatus,
    Decision,

    # 손상 분석 관련 모델
    DamageAnalysisRequest,
    DamageAnalysisResponse,
    DamageAnalysisResult,
    DetectionDetail,
    BusinessAssessment,

    # 성능 예측 관련 모델
    PanelRequest,
    PerformanceReportResponse,
    PerformanceReportDetailResponse,
    PerformanceAnalysisResult,
    PerformanceReportRequest,

    # 공통 모델
    HealthCheckResponse,
    ErrorResponse
)

from .model_features import MODEL_FEATURES

__all__ = [
    # Enum 타입
    "PanelStatus",
    "Decision",

    # 손상 분석
    "DamageAnalysisRequest",
    "DamageAnalysisResponse",
    "DamageAnalysisResult",
    "DetectionDetail",
    "BusinessAssessment",

    # 성능 예측
    "PanelRequest",
    "PerformanceReportResponse",
    "PerformanceReportDetailResponse",
    "PerformanceAnalysisResult",
    "PerformanceReportRequest",

    # 공통
    "HealthCheckResponse",
    "ErrorResponse",

    # 모델 피처
    "MODEL_FEATURES"
]

# 패키지 메타데이터
__version__ = "3.0.0"
__description__ = "Solar Panel AI Service Data Models and Schemas"

# 스키마 검증 헬퍼 함수
def validate_request_schema(data: dict, schema_class):
    """
    요청 데이터를 지정된 스키마로 검증합니다.

    Args:
        data: 검증할 데이터
        schema_class: Pydantic 모델 클래스

    Returns:
        검증된 모델 인스턴스

    Raises:
        ValidationError: 스키마 검증 실패 시
    """
    return schema_class(**data)
