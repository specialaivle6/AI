"""
Models Package - AI 모델 관련 모듈

YOLOv8 모델 로더 및 관리 기능을 위한 패키지입니다.
향후 다양한 AI 모델들의 로더와 매니저가 추가될 예정입니다.
"""

# 향후 모델 로더들이 추가될 예정
__all__ = []

"""
Models Package - 데이터 모델 및 스키마

Pydantic 모델들과 DB 스키마 정의를 포함합니다.
"""

from .schemas import (
    PanelStatus, Decision, RequestStatus,
    PanelImageCreate, PanelImageResponse,
    PanelImageReportCreate, PanelImageReportResponse,
    AnalysisRequest, AnalysisResponse
)

__all__ += [
    "PanelStatus", "Decision", "RequestStatus",
    "PanelImageCreate", "PanelImageResponse", 
    "PanelImageReportCreate", "PanelImageReportResponse",
    "AnalysisRequest", "AnalysisResponse"
]
