"""
Solar Panel AI Service - 통합 AI 분석 서비스

태양광 패널 손상 분석 및 성능 예측을 위한 통합 AI 서비스입니다.
YOLOv8 기반 손상 분석과 ML 앙상블 기반 성능 예측을 제공합니다.

주요 기능:
- YOLOv8 Segmentation 기반 패널 손상 분석
- ML 앙상블 모델 기반 성능 예측 및 수명 추정
- S3 URL 기반 이미지 처리
- PDF 리포트 생성
- 백엔드 서버와의 RESTful API 연동

Version: 3.0.0 - Integrated AI Services
"""

from .core import settings, setup_logging, get_logger
from .services import DamageAnalyzer, PerformanceAnalyzer
from .schemas import (
    DamageAnalysisRequest, DamageAnalysisResponse,
    PanelRequest, PerformanceReportResponse
)

# 패키지 메타데이터
__version__ = "3.0.0"
__author__ = "Solar AI Services Team"
__description__ = "통합 태양광 패널 AI 분석 서비스 (손상 분석 + 성능 예측)"
__mode__ = "Integrated AI Services"

# 애플리케이션 정보
APP_INFO = {
    "name": "Solar Panel AI Service",
    "version": __version__,
    "description": __description__,
    "services": [
        "Damage Analysis (YOLOv8)",
        "Performance Prediction (ML Ensemble)",
        "PDF Report Generation"
    ],
    "integration_mode": "Backend API",
    "supported_formats": ["JPEG", "PNG", "BMP", "TIFF", "WEBP"]
}

# 서비스 상태 체크
def get_service_info():
    """서비스 정보 반환"""
    return {
        **APP_INFO,
        "settings": {
            "debug": settings.debug,
            "environment": "development" if settings.is_development else "production",
            "log_level": settings.log_level
        }
    }

# 초기화 함수
def initialize_app():
    """애플리케이션 초기화"""
    logger = get_logger(__name__)
    logger.info(f"🚀 {APP_INFO['name']} v{__version__} 초기화")
    logger.info(f"📊 지원 서비스: {', '.join(APP_INFO['services'])}")
    logger.info(f"🔧 환경: {'개발' if settings.is_development else '프로덕션'}")

__all__ = [
    # 핵심 구성요소
    "settings",
    "setup_logging",
    "get_logger",

    # AI 서비스
    "DamageAnalyzer",
    "PerformanceAnalyzer",

    # 데이터 모델
    "DamageAnalysisRequest",
    "DamageAnalysisResponse",
    "PanelRequest",
    "PerformanceReportResponse",

    # 유틸리티
    "APP_INFO",
    "get_service_info",
    "initialize_app"
]
