import os
from pathlib import Path


class Settings:
    # 기본 설정
    app_name: str = "Solar Panel AI Service"
    app_version: str = "2.0.0"  # YOLOv8 버전으로 업데이트
    debug: bool = True

    # 서버 설정
    host: str = "0.0.0.0"
    port: int = 8000

    # YOLOv8 모델 설정
    model_path: str = "models/yolov8_seg_0812_v0.1.pt"  # 실제 커스텀 모델 경로
    device: str = "cpu"  # CPU 전용
    confidence_threshold: float = 0.25  # YOLOv8 신뢰도 임계값

    # 이미지 처리 설정
    max_image_size: int = 20 * 1024 * 1024  # 20MB로 증가 (고해상도 패널 이미지)
    allowed_extensions: list = [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"]
    max_batch_size: int = 10  # 일괄 처리 최대 파일 수

    # 손상 분석 설정
    critical_damage_threshold: float = 5.0  # 심각한 손상 임계값 (%)
    contamination_threshold: float = 10.0   # 오염 임계값 (%)
    maintenance_urgent_threshold: float = 10.0  # 긴급 유지보수 임계값 (%)

    # 비즈니스 로직 설정
    high_confidence_threshold: float = 0.85
    cost_per_damage_percent: float = 1000  # 손상 1%당 수리 비용 (원)
    cost_per_contamination_percent: float = 50  # 오염 1%당 청소 비용 (원)

    # 보안 설정
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS 설정
    allowed_origins: list = [
        "http://localhost:3000",  # React 개발 서버
        "http://127.0.0.1:3000",
        "http://localhost:8080",  # Vue.js 개발 서버
    ]

    # 로깅 설정
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = "logs/ai_service.log"

    # 성능 설정
    prediction_timeout: float = 60.0  # YOLOv8는 더 많은 시간 필요
    async_processing: bool = True  # 비동기 처리 활성화

    # 클래스 정의 (YOLOv8 모델에 따라 조정 필요)
    critical_classes: list = ['Physical-Damage', 'Electrical-Damage']
    contamination_classes: list = ['Bird-drop', 'Dusty', 'Snow']
    normal_classes: list = ['Non-Defective', 'Clean']


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