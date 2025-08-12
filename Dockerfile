# Python 3.11 slim 이미지 사용 (경량화)
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치 (YOLOv8 및 OpenCV 지원)
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    libgl1-mesa-glx \
    libgthread-2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사
COPY requirements.txt .

# NumPy 호환성을 위한 버전 고정 및 Python 패키지 설치
RUN pip install --no-cache-dir "numpy<2" && \
    pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY app/ ./app/
COPY models/ ./models/

# 필요한 디렉토리 생성
RUN mkdir -p logs temp uploads

# YOLOv8 기본 모델 사전 다운로드 (선택사항)
RUN python -c "from ultralytics import YOLO; YOLO('yolov8n-seg.pt')" || true

# 포트 8000 노출
EXPOSE 8000

# 헬스체크 설정 (YOLOv8 엔드포인트 반영)
HEALTHCHECK --interval=30s --timeout=30s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 애플리케이션 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
