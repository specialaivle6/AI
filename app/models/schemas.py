"""
AI 서비스 데이터 모델 정의 - Pydantic 모델들

백엔드와의 API 통신을 위한 요청/응답 모델들을 정의합니다.
AI 서버는 DB 저장을 하지 않고, 순수 분석 기능에 집중합니다.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
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


# === 백엔드와의 API 통신용 모델들 ===

class DamageAnalysisRequest(BaseModel):
    """손상 분석 요청 (백엔드에서 AI 서버로)"""
    panel_id: int
    user_id: UUID
    panel_imageurl: str = Field(..., description="S3 이미지 URL")


class DetectionDetail(BaseModel):
    """개별 탐지 결과"""
    class_name: str
    confidence: float
    bbox: List[int] = Field(..., description="[x1, y1, x2, y2] 형태의 바운딩 박스")
    area_pixels: int


class BusinessAssessment(BaseModel):
    """비즈니스 평가 결과"""
    priority: str = Field(..., description="우선순위: HIGH, MEDIUM, LOW")
    risk_level: str = Field(..., description="위험도: HIGH, MEDIUM, LOW")
    recommendations: List[str] = Field(default_factory=list)
    estimated_repair_cost_krw: Optional[int] = None
    estimated_performance_loss_percent: Optional[float] = None
    maintenance_urgency_days: Optional[int] = None
    business_impact: Optional[str] = None


class DamageAnalysisResult(BaseModel):
    """손상 분석 결과"""
    overall_damage_percentage: float
    critical_damage_percentage: float
    contamination_percentage: float
    healthy_percentage: float
    avg_confidence: float
    detected_objects: int
    class_breakdown: Dict[str, float] = Field(default_factory=dict)
    status: str = "analyzed"


class DamageAnalysisResponse(BaseModel):
    """손상 분석 응답 (AI 서버에서 백엔드로)"""
    panel_id: int
    user_id: UUID

    # 이미지 정보
    image_info: Dict[str, Any] = Field(default_factory=dict)

    # 분석 결과
    damage_analysis: DamageAnalysisResult
    business_assessment: BusinessAssessment
    detection_details: Dict[str, Any] = Field(default_factory=dict)

    # 메타데이터
    confidence_score: float
    timestamp: datetime = Field(default_factory=datetime.now)
    processing_time_seconds: Optional[float] = None


class HealthCheckResponse(BaseModel):
    """헬스체크 응답"""
    status: str
    model_loaded: bool
    version: str
    model_type: str = "YOLOv8"


class ErrorResponse(BaseModel):
    """에러 응답"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
