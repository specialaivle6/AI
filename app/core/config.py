import os
from pathlib import Path
from typing import List


class Settings:
    # 기본 설정
    app_name: str = "Solar Panel AI Service"
    app_version: str = "2.1.0"  # 버전 업데이트
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"

    # 서버 설정
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))

    # YOLOv8 모델 설정
    model_path: str = os.getenv("MODEL_PATH", "models/yolov8_seg_0812_v0.1.pt")
    device: str = os.getenv("DEVICE", "cpu")  # CPU 전용
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.25"))

    # 이미지 처리 설정
    max_image_size: int = int(os.getenv("MAX_IMAGE_SIZE", str(20 * 1024 * 1024)))  # 20MB
    allowed_extensions: List[str] = [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"]
    max_batch_size: int = int(os.getenv("MAX_BATCH_SIZE", "10"))

    # 손상 분석 설정
    critical_damage_threshold: float = float(os.getenv("CRITICAL_DAMAGE_THRESHOLD", "5.0"))
    contamination_threshold: float = float(os.getenv("CONTAMINATION_THRESHOLD", "10.0"))
    maintenance_urgent_threshold: float = float(os.getenv("MAINTENANCE_URGENT_THRESHOLD", "10.0"))

    # 비즈니스 로직 설정
    high_confidence_threshold: float = float(os.getenv("HIGH_CONFIDENCE_THRESHOLD", "0.85"))
    cost_per_damage_percent: float = float(os.getenv("COST_PER_DAMAGE_PERCENT", "1000"))
    cost_per_contamination_percent: float = float(os.getenv("COST_PER_CONTAMINATION_PERCENT", "50"))

    # 보안 설정
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # CORS 설정
    allowed_origins: List[str] = [
        "http://localhost:3000",  # React 개발 서버
        "http://127.0.0.1:3000",
        "http://localhost:8080",  # Vue.js 개발 서버
    ]

    # 로깅 설정
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "logs/ai_service.log")

    # 성능 설정
    prediction_timeout: float = float(os.getenv("PREDICTION_TIMEOUT", "60.0"))
    async_processing: bool = os.getenv("ASYNC_PROCESSING", "True").lower() == "true"

    # 클래스 정의 (YOLOv8 모델에 따라 조정 필요)
    critical_classes: List[str] = ['Physical-Damage', 'Electrical-Damage']
    contamination_classes: List[str] = ['Bird-drop', 'Dusty', 'Snow']
    normal_classes: List[str] = ['Non-Defective', 'Clean']



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