# =====================================================
# Solar Panel AI Service - Stable/Prod-lean Version
# =====================================================
FROM python:3.12-slim

LABEL maintainer="AI/ML Engineer"
LABEL description="Solar Panel AI Service - Stable Version"
LABEL version="3.0.2"

WORKDIR /app

# 기본 런타임 환경
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    YOLO_CONFIG_DIR=/tmp/ultralytics \
    MPLCONFIGDIR=/tmp/matplotlib \
    FONTCONFIG_PATH=/tmp/fontconfig

# 시스템 패키지
# - libgl1: OpenCV의 libGL.so.1 오류 방지
# - ca-certificates: boto3/OpenAI 등 HTTPS 실패 방지
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl wget ca-certificates \
    ffmpeg libsm6 libxext6 libglib2.0-0 libgomp1 libxrender1 libgl1 \
    fonts-noto-cjk fontconfig fonts-nanum \
    gcc g++ \
 && fc-cache -fv \
 && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Python 의존성
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt

# 빌드 도구 제거(경량화)
RUN apt-get purge -y --auto-remove gcc g++ \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# 캐시/로그 디렉터리
RUN mkdir -p /tmp/ultralytics /tmp/matplotlib /tmp/fontconfig /app/logs /app/reports /app/temp \
 && chmod 777 /tmp/ultralytics /tmp/matplotlib /tmp/fontconfig

# 애플리케이션
COPY app/ ./app/
COPY models/ ./models/
COPY data/ ./data/
COPY fonts/ ./fonts/
COPY chatbot/ ./chatbot/

# 기본 런타임 설정 (민감값/모델경로/CORS는 .env(.docker)에서만 관리)
ENV HOST=0.0.0.0 \
    PORT=8000 \
    LOG_LEVEL=INFO \
    DEVICE=cpu \
    S3_DOWNLOAD_TIMEOUT=30 \
    IMAGE_PROCESSING_TIMEOUT=120 \
    PERFORMANCE_ANALYSIS_TIMEOUT=60 \
    REPORT_GENERATION_TIMEOUT=180 \
    WORKERS=2

EXPOSE 8000

# 헬스체크(전용 /health 라우트가 있다면 해당 경로로 교체 권장)
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
  CMD curl -fsS http://localhost:8000/ || exit 1

# 워커 수를 환경변수로 제어(기본 2). 필요 시 1로도 쉽게 조정 가능.
CMD ["sh","-c","uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WORKERS:-2}"]

