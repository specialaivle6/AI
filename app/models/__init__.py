"""
Models Package - AI 모델 관련 모듈

YOLOv8 모델 로더 및 관리 기능을 위한 패키지입니다.
향후 다양한 AI 모델들의 로더와 매니저가 추가될 예정입니다.
"""

# 향후 모델 로더들이 추가될 예정
__all__ = []

"""
Models Package - 데이터 모델 및 스키마

백엔드 연동을 위한 Pydantic 모델들과 API 스키마 정의를 포함합니다.
AI 서버는 순수 분석 기능에 집중하며, DB 연동은 백엔드에서 처리합니다.
"""

from .schemas import (
    # Enum 타입들
    PanelStatus,
    Decision,

    # API 통신용 모델들
    DamageAnalysisRequest,
    DamageAnalysisResponse,
    DamageAnalysisResult,
    BusinessAssessment,
    DetectionDetail,

    # 시스템 응답 모델들
    HealthCheckResponse,
    ErrorResponse
)

__all__ += [
    # Enum 타입들
    "PanelStatus",
    "Decision",

    # API 통신용 모델들
    "DamageAnalysisRequest",
    "DamageAnalysisResponse",
    "DamageAnalysisResult",
    "BusinessAssessment",
    "DetectionDetail",

    # 시스템 응답 모델들
    "HealthCheckResponse",
    "ErrorResponse"
]
