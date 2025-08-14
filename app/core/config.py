import os
from pathlib import Path
from typing import List, Dict, Any
import logging


class Settings:
    """애플리케이션 설정 클래스"""

    # === 기본 애플리케이션 설정 ===
    app_name: str = "Solar Panel AI Service"
    app_version: str = "3.0.0"
    description: str = "태양광 패널 손상 분석 및 성능 예측 AI 서비스"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"

    # === 서버 설정 ===
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    workers: int = int(os.getenv("WORKERS", "1"))

    # === AI 모델 경로 설정 ===
    damage_model_path: str = os.getenv("DAMAGE_MODEL_PATH", "models/yolov8_seg_0812_v0.1.pt")
    performance_model_path: str = os.getenv("PERFORMANCE_MODEL_PATH", "models/voting_ensemble_model.pkl")
    device: str = os.getenv("DEVICE", "cpu")

    # === YOLOv8 손상 분석 설정 ===
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.25"))
    iou_threshold: float = float(os.getenv("IOU_THRESHOLD", "0.45"))
    max_detections: int = int(os.getenv("MAX_DETECTIONS", "300"))

    # 손상 분류 임계값
    critical_damage_threshold: float = float(os.getenv("CRITICAL_DAMAGE_THRESHOLD", "5.0"))
    contamination_threshold: float = float(os.getenv("CONTAMINATION_THRESHOLD", "10.0"))
    maintenance_urgent_threshold: float = float(os.getenv("MAINTENANCE_URGENT_THRESHOLD", "10.0"))

    # === 이미지 처리 설정 ===
    max_image_size: int = int(os.getenv("MAX_IMAGE_SIZE", str(20 * 1024 * 1024)))  # 20MB
    allowed_extensions: List[str] = [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"]
    s3_download_timeout: int = int(os.getenv("S3_DOWNLOAD_TIMEOUT", "30"))
    image_processing_timeout: int = int(os.getenv("IMAGE_PROCESSING_TIMEOUT", "120"))

    # === 성능 예측 설정 ===
    performance_analysis_timeout: int = int(os.getenv("PERFORMANCE_ANALYSIS_TIMEOUT", "60"))
    report_generation_timeout: int = int(os.getenv("REPORT_GENERATION_TIMEOUT", "180"))

    # === API 타임아웃 설정 ===
    backend_api_timeout: int = int(os.getenv("BACKEND_API_TIMEOUT", "60"))
    external_api_timeout: int = int(os.getenv("EXTERNAL_API_TIMEOUT", "30"))

    # === CORS 설정 ===
    cors_origins: List[str] = os.getenv("CORS_ORIGINS", "*").split(",")
    cors_credentials: bool = os.getenv("CORS_CREDENTIALS", "True").lower() == "true"

    # === 로깅 설정 ===
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "logs/ai_service.log")
    log_max_size: str = os.getenv("LOG_MAX_SIZE", "10MB")
    log_backup_count: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    # === 디렉토리 설정 ===
    models_dir: Path = Path("models")
    logs_dir: Path = Path("logs")
    reports_dir: Path = Path("reports")
    temp_dir: Path = Path("temp")
    fonts_dir: Path = Path("fonts")

    # === 비즈니스 로직 상수 ===
    class DamageConstants:
        """손상 분석 관련 상수들"""
        CRITICAL_CLASSES = ['Physical-Damage', 'Electrical-Damage']
        CONTAMINATION_CLASSES = ['Bird-drop', 'Dusty', 'Snow']

        # 우선순위 매핑
        PRIORITY_HIGH_THRESHOLD = 10.0
        PRIORITY_MEDIUM_THRESHOLD = 5.0

        # 비용 추정 (원)
        REPAIR_COST_PER_PERCENT = 50000  # 1% 손상당 수리비
        REPLACEMENT_COST_BASE = 500000   # 기본 교체비

    class PerformanceConstants:
        """성능 예측 관련 상수들"""
        PERFORMANCE_RATIO_GOOD = 0.85
        PERFORMANCE_RATIO_FAIR = 0.70
        PERFORMANCE_RATIO_POOR = 0.50

        # 수명 추정 (개월)
        EXPECTED_LIFESPAN_MONTHS = 300  # 25년

        # 성능 상태 임계값
        STATUS_EXCELLENT = 0.95
        STATUS_GOOD = 0.85
        STATUS_FAIR = 0.70
        STATUS_POOR = 0.50

    # === 환경별 설정 ===
    @property
    def is_development(self) -> bool:
        return self.debug

    @property
    def is_production(self) -> bool:
        return not self.debug

    @property
    def log_level_int(self) -> int:
        """로그 레벨을 정수로 반환"""
        return getattr(logging, self.log_level.upper(), logging.INFO)


# 전역 설정 인스턴스
settings = Settings()


def create_directories():
    """필요한 디렉토리들을 생성"""
    directories = [
        settings.models_dir,
        settings.logs_dir,
        settings.reports_dir,
        settings.temp_dir
    ]

    for directory in directories:
        directory.mkdir(exist_ok=True)


def get_model_info() -> Dict[str, Any]:
    """모델 정보 반환"""
    return {
        "damage_model": {
            "path": settings.damage_model_path,
            "exists": Path(settings.damage_model_path).exists()
        },
        "performance_model": {
            "path": settings.performance_model_path,
            "exists": Path(settings.performance_model_path).exists()
        }
    }


def validate_settings() -> List[str]:
    """설정 검증 및 문제점 반환"""
    issues = []

    # 모델 파일 존재 확인
    if not Path(settings.damage_model_path).exists():
        issues.append(f"손상 분석 모델 파일이 없습니다: {settings.damage_model_path}")

    if not Path(settings.performance_model_path).exists():
        issues.append(f"성능 예측 모델 파일이 없습니다: {settings.performance_model_path}")

    # 폰트 파일 확인 (한글 PDF 생성용)
    korean_fonts = [
        settings.fonts_dir / "NotoSansKR-Regular.otf",
        settings.fonts_dir / "NotoSansKR-Bold.otf"
    ]

    missing_fonts = [f for f in korean_fonts if not f.exists()]
    if missing_fonts:
        issues.append(f"한글 폰트 파일이 없습니다: {missing_fonts}")

    return issues


# 초기화 시 디렉토리 생성
create_directories()