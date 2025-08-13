"""
데이터 모델 정의 - Pydantic 모델들

DB 스키마와 매핑되는 API 요청/응답 모델들을 정의합니다.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
from enum import Enum


class PanelStatus(str, Enum):
    """패널 상태"""
    DAMAGE = "손상"
    CONTAMINATION = "오염"
    NORMAL = "정상"


class Decision(str, Enum):
    """조치 결정"""
    SIMPLE_CLEANING = "단순 오염"
    REPAIR = "수리"
    REPLACEMENT = "교체"


class RequestStatus(str, Enum):
    """요청 상태"""
    REQUESTING = "요청 중"
    CONFIRMED = "요청확인"
    PROCESSING = "처리중"
    COMPLETED = "처리 완료"


class PanelImageCreate(BaseModel):
    """패널 이미지 생성 요청"""
    panel_id: int
    user_id: UUID
    film_date: date
    panel_imageurl: str
    is_analysis: bool = False


class PanelImageResponse(BaseModel):
    """패널 이미지 응답"""
    id: int
    panel_id: int
    user_id: UUID
    film_date: date
    panel_imageurl: str
    is_analysis: bool


class PanelImageReportCreate(BaseModel):
    """패널 이미지 리포트 생성 요청"""
    panel_id: int
    user_id: UUID
    status: PanelStatus
    damage_degree: Optional[int] = None
    decision: Decision
    request_status: RequestStatus = RequestStatus.REQUESTING


class PanelImageReportResponse(BaseModel):
    """패널 이미지 리포트 응답"""
    id: int
    panel_id: int
    user_id: UUID
    status: PanelStatus
    damage_degree: Optional[int] = None
    decision: Decision
    request_status: RequestStatus
    created_at: date


class AnalysisRequest(BaseModel):
    """AI 분석 요청"""
    panel_id: int
    user_id: UUID
    panel_imageurl: Optional[str] = None  # URL로 이미지 제공하는 경우


class AnalysisResponse(BaseModel):
    """AI 분석 응답 (기존 + DB 연동 정보)"""
    # 기존 AI 분석 결과
    image_info: dict
    damage_analysis: dict
    business_assessment: dict
    detection_details: dict
    confidence_score: float
    timestamp: str

    # DB 연동 정보
    panel_image_id: Optional[int] = None
    panel_image_report_id: Optional[int] = None
    recommended_status: PanelStatus
    recommended_decision: Decision
