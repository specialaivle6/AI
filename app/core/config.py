import os
from pathlib import Path


class Settings:
    # 기본 설정
    app_name: str = "Solar Panel AI Service"
    app_version: str = "1.0.0"
    debug: bool = True

    # 서버 설정
    host: str = "0.0.0.0"
    port: int = 8000

    # 모델 설정
    model_path: str = "models/mobilenet_v3_small.pth"
    device: str = "cpu"  # CPU 전용

    # 이미지 처리 설정
    max_image_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: list = [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]
    image_input_size: int = 224

    # 보안 설정
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS 설정
    allowed_origins: list = [
        "http://localhost:3000",  # React 개발 서버
        "http://127.0.0.1:3000",
    ]

    # 로깅 설정
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = "logs/ai_service.log"

    # 성능 설정
    max_batch_size: int = 1  # 단일 이미지 처리
    prediction_timeout: float = 30.0  # 30초

    # 비즈니스 로직 설정
    confidence_threshold: float = 0.5
    high_confidence_threshold: float = 0.85
    damage_alert_threshold: float = 0.2


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