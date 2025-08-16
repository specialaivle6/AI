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
    CRITICAL_DAMAGE = "심각한 손상"
    DAMAGE = "손상"
    CONTAMINATION = "오염"
    NORMAL = "정상"


class Decision(str, Enum):
    """조치 결정"""
    URGENT_SHUTDOWN = "즉시 가동 중단 및 교체"
    REPLACEMENT = "교체"
    REPAIR = "수리"
    MAINTENANCE = "정기 점검"


class Priority(str, Enum):
    """우선순위"""
    URGENT = "URGENT"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RiskLevel(str, Enum):
    """위험도"""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    MINIMAL = "MINIMAL"


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
    priority: str = Field(..., description="우선순위: URGENT, HIGH, MEDIUM, LOW")
    risk_level: str = Field(..., description="위험도: HIGH, MEDIUM, LOW, MINIMAL")
    recommendations: List[str] = Field(default_factory=list)
    estimated_repair_cost_krw: Optional[int] = None
    estimated_performance_loss_percent: Optional[float] = None
    maintenance_urgency_days: Optional[int] = None
    business_impact: Optional[str] = None

    # SQL 테이블과 일치하는 필드명
    status: str = Field(..., description="패널 상태: 손상, 오염")  # SQL의 status 필드와 일치
    damage_degree: Optional[int] = Field(None, description="손상 정도 (0-100)")
    decision: str = Field(..., description="조치 결정: 단순 오염, 수리, 교체")
    request_status: str = Field(default="요청 중", description="요청 상태: 요청 중, 요청확인, 처리중, 처리 완료")


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
    
    # 면적 기반 계산 결과 필드들
    total_image_area: Optional[int] = Field(None, description="전체 이미지 면적 (픽셀)")
    damaged_area_pixels: Optional[int] = Field(None, description="손상된 면적 (픽셀)")
    contaminated_area_pixels: Optional[int] = Field(None, description="오염된 면적 (픽셀)")

class DamageAnalysisResponse(BaseModel):
    """손상 분석 응답 (AI 서버에서 백엔드로)"""
    panel_id: int
    user_id: UUID

    # 이미지 정보
    image_info: Dict[str, Any] = Field(default_factory=dict)

    # 분석 결과
    damage_analysis: DamageAnalysisResult
    business_assessment: BusinessAssessment
    detection_details: List[DetectionDetail] = Field(default_factory=list)  # Dict에서 List로 수정

    # 메타데이터
    confidence_score: float
    timestamp: datetime = Field(default_factory=datetime.now)
    processing_time_seconds: Optional[float] = None

    # SQL 테이블 매핑을 위한 편의 메서드들 (필드명 수정)
    def get_status(self) -> str:
        """DB용 상태 반환 (SQL의 status 필드)"""
        return self.business_assessment.status

    def get_damage_degree(self) -> Optional[int]:
        """DB용 손상 정도 반환"""
        return self.business_assessment.damage_degree

    def get_decision(self) -> str:
        """DB용 조치 결정 반환"""
        return self.business_assessment.decision
    
    def get_request_status(self) -> str:
        """DB용 요청 상태 반환"""
        return self.business_assessment.request_status

    def to_panel_image_report_data(self) -> Dict[str, Any]:
        """PanelImageReport 테이블용 데이터 반환"""
        return {
            "panel_id": self.panel_id,
            "user_id": self.user_id,
            "status": self.get_status(),
            "damage_degree": self.get_damage_degree(),
            "decision": self.get_decision(),
            "request_status": self.get_request_status(),
            "created_at": self.timestamp.date()
        }

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


# === 성능 예측 서비스용 모델들 (new_service 통합) ===

class PanelRequest(BaseModel):
    """태양광 패널 성능 예측 요청"""
    user_id: str
    id: int
    model_name: str
    serial_number: int
    pmp_rated_w: float
    temp_coeff: float
    annual_degradation_rate: float
    lat: float
    lon: float
    installed_at: str
    installed_angle: float
    installed_direction: str
    temp: List[float]
    humidity: List[float]
    windspeed: List[float]
    sunshine: List[float]
    actual_generation: float


class PerformanceReportResponse(BaseModel):
    """성능 예측 리포트 응답"""
    user_id: str
    address: str = Field(..., description="생성된 PDF 리포트 파일 경로")
    created_at: str = Field(..., description="리포트 생성 시간")


class PerformanceAnalysisResult(BaseModel):
    """성능 분석 결과"""
    predicted_generation: float = Field(..., description="예측 발전량 (kWh)")
    actual_generation: float = Field(..., description="실제 발전량 (kWh)")
    performance_ratio: float = Field(..., description="성능비율 (실측/예측)")
    status: str = Field(..., description="패널 상태")
    lifespan_months: Optional[float] = Field(None, description="예상 잔여 수명 (개월)")
    estimated_cost: Optional[int] = Field(None, description="예상 교체 비용 (원)")


class PerformanceReportRequest(BaseModel):
    """성능 예측 리포트 생성 요청 (확장된 버전)"""
    panel_data: PanelRequest
    include_charts: bool = Field(default=True, description="차트 포함 여부")
    report_format: str = Field(default="pdf", description="리포트 형식")


class PerformanceReportDetailResponse(BaseModel):
    """상세 성능 예측 리포트 응답"""
    user_id: str
    panel_id: int
    
    # 분석 결과
    performance_analysis: PerformanceAnalysisResult
    
    # 리포트 정보
    report_path: str
    created_at: str
    processing_time_seconds: Optional[float] = None
    
    # 메타데이터
    panel_info: Dict[str, Any] = Field(default_factory=dict)
    environmental_data: Dict[str, Any] = Field(default_factory=dict)

