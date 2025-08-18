# =====================================================
# Solar Panel AI Service - 에러 해결 버전
# 목표: 안정성 우선, 폰트 문제 해결, 권한 문제 해결
# =====================================================

FROM python:3.11-slim

# 메타데이터
LABEL maintainer="AI/ML Engineer"
LABEL description="Solar Panel AI Service - Stable Version"
LABEL version="3.0.1"

# 작업 디렉토리 설정
WORKDIR /app

# 환경변수 설정 (권한 문제 미리 방지)
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 캐시 디렉토리를 /tmp로 설정 (권한 문제 해결)
ENV YOLO_CONFIG_DIR=/tmp/ultralytics
ENV MPLCONFIGDIR=/tmp/matplotlib
ENV FONTCONFIG_PATH=/tmp/fontconfig

# 시스템 패키지 설치 (단계별로 명확하게)
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 네트워크 도구
    curl \
    wget \
    # OpenCV 필수 의존성 (에러 해결된 패키지들)
    ffmpeg \
    libsm6 \
    libxext6 \
    libglib2.0-0 \
    libgomp1 \
    libxrender1 \
    # 한글 폰트 시스템 설치 (백업용)
    fonts-noto-cjk \
    fontconfig \
    # 빌드 도구 (일부 Python 패키지 컴파일용)
    gcc \
    g++ \
    && fc-cache -fv \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Python 의존성 설치 (단계별)
COPY requirements.txt .

# pip 업그레이드 및 의존성 설치
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# 빌드 도구 제거 (이미지 크기 최소화)
RUN apt-get remove -y gcc g++ && \
    apt-get autoremove -y && \
    apt-get clean

# 캐시 디렉토리 미리 생성 (권한 문제 방지)
RUN mkdir -p /tmp/ultralytics /tmp/matplotlib /tmp/fontconfig \
    /app/logs /app/reports /app/temp && \
    chmod 777 /tmp/ultralytics /tmp/matplotlib /tmp/fontconfig

# 애플리케이션 파일들 복사
COPY app/ ./app/
COPY models/ ./models/
COPY data/ ./data/
COPY fonts/ ./fonts/

# AI 서비스 기본 설정
ENV HOST=0.0.0.0
ENV PORT=8000
ENV WORKERS=1
ENV LOG_LEVEL=INFO
ENV DEVICE=cpu

# 모델 경로 설정
ENV DAMAGE_MODEL_PATH=models/yolov8_seg_0812_v0.1.pt
ENV PERFORMANCE_MODEL_PATH=models/voting_ensemble_model.pkl

# 타임아웃 설정
ENV S3_DOWNLOAD_TIMEOUT=30
ENV IMAGE_PROCESSING_TIMEOUT=120
ENV PERFORMANCE_ANALYSIS_TIMEOUT=60
ENV REPORT_GENERATION_TIMEOUT=180

# CORS 설정 (CORS_CREDENTIALS 제거 - 보안 경고 해결)
ENV CORS_ORIGINS=*

# 포트 노출
EXPOSE 8000

# 헬스체크 설정 (시작 시간 충분히 확보)
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# 애플리케이션 실행 (root로 실행 - 권한 문제 완전 해결)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

# =====================================================
# 빌드 및 테스트 명령어
# =====================================================

# 1. 이미지 빌드
# docker build -t solar-panel-ai:stable .

# 2. 테스트 실행 (로그 확인)
# docker run --rm -p 8000:8000 \
#   -e LOG_LEVEL=DEBUG \
#   --name solar-ai-test \
#   solar-panel-ai:stable

# 3. 헬스체크 테스트
# curl http://localhost:8000/
# curl http://localhost:8000/api/damage-analysis/health

# =====================================================