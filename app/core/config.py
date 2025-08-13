import os
from pathlib import Path
from typing import List


class Settings:
    # 기본 설정
    app_name: str = "Solar Panel AI Service"
    app_version: str = "3.0.0"  # 백엔드 연동 버전으로 업데이트
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"

    # 서버 설정
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))

    # YOLOv8 모델 설정
    model_path: str = os.getenv("MODEL_PATH", "models/yolov8_seg_0812_v0.1.pt")
    device: str = os.getenv("DEVICE", "cpu")  # CPU 전용
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.25"))

    # 이미지 처리 설정 (S3 다운로드용)
    max_image_size: int = int(os.getenv("MAX_IMAGE_SIZE", str(20 * 1024 * 1024)))  # 20MB
    allowed_extensions: List[str] = [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"]
    s3_download_timeout: int = int(os.getenv("S3_DOWNLOAD_TIMEOUT", "30"))  # 30초

    # 손상 분석 설정
    critical_damage_threshold: float = float(os.getenv("CRITICAL_DAMAGE_THRESHOLD", "5.0"))
    contamination_threshold: float = float(os.getenv("CONTAMINATION_THRESHOLD", "10.0"))
    maintenance_urgent_threshold: float = float(os.getenv("MAINTENANCE_URGENT_THRESHOLD", "10.0"))

    # 백엔드 연동 설정
    backend_api_timeout: int = int(os.getenv("BACKEND_API_TIMEOUT", "60"))  # 60초

    # CORS 설정
    cors_origins: List[str] = os.getenv("CORS_ORIGINS", "*").split(",")

    # 로깅 설정
    log_level: str = os.getenv("LOG_LEVEL", "INFO")



# 전역 설정 인스턴스
settings = Settings()


# 디렉토리 생성
def create_directories():
    """필요한 디렉토리들을 생성"""
    directories = [
        Path("models"),
        Path("logs"),
        Path("temp"),
        Path("uploads")
    ]

    for directory in directories:
        directory.mkdir(exist_ok=True)


# 앱 시작 시 디렉토리 생성
create_directories()