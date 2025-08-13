# Python 3.11 slim 이미지 사용 (경량화)
FROM python:3.11-slim

# 메타데이터 추가
LABEL maintainer="AI Services Team"
LABEL version="3.0.0"
LABEL description="Solar Panel AI Service - Backend Integration"

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치 (YOLOv8 및 OpenCV 지원)
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    libgthread-2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Python 의존성 파일 복사
COPY requirements.txt .

# 최적화된 Python 패키지 설치
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir "numpy>=1.24.0,<2.0.0" && \
    pip install --no-cache-dir -r requirements.txt

# 필요한 디렉토리 생성
RUN mkdir -p /app/models /app/logs /app/temp /app/uploads

# AI 모델 파일 복사 (로컬에 있는 경우)
COPY models/ ./models/

# 애플리케이션 코드 복사
COPY app/ ./app/

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000
ENV LOG_LEVEL=INFO
ENV MODEL_PATH=/app/models/yolov8_seg_0812_v0.1.pt
ENV DEVICE=cpu

# 포트 노출
EXPOSE 8000

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/damage-analysis/health || exit 1

# 비root 사용자 생성 및 권한 설정 (보안 강화)
RUN groupadd -r aiuser && useradd -r -g aiuser aiuser && \
    chown -R aiuser:aiuser /app
USER aiuser

# 애플리케이션 실행
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
