#!/bin/bash

# Solar Panel AI Service 배포 스크립트
# 사용법: ./deploy.sh [환경]
# 예: ./deploy.sh production

set -e

ENVIRONMENT=${1:-development}
IMAGE_NAME="solar-panel-ai"
CONTAINER_NAME="solar-panel-ai-service"

echo "🚀 Solar Panel AI Service 배포 시작 - 환경: $ENVIRONMENT"

# 1. 이전 컨테이너 정리
echo "📦 기존 컨테이너 정리..."
docker-compose down --remove-orphans || true
docker container rm -f $CONTAINER_NAME 2>/dev/null || true

# 2. Docker 이미지 빌드
echo "🔨 Docker 이미지 빌드..."
docker build -t $IMAGE_NAME:latest .

# 3. 필요한 디렉토리 생성
echo "📁 로그 디렉토리 생성..."
mkdir -p ./logs ./temp

# 4. 환경변수 파일 확인
if [ ! -f .env ]; then
    echo "⚠️  .env 파일이 없습니다. .env.example을 복사하여 설정하세요."
    cp .env.example .env
    echo "✅ .env.example을 .env로 복사했습니다. 설정을 확인하세요."
fi

# 5. AI 모델 파일 확인
if [ ! -f "./models/yolov8_seg_0812_v0.1.pt" ]; then
    echo "❌ AI 모델 파일이 없습니다: ./models/yolov8_seg_0812_v0.1.pt"
    echo "모델 파일을 models/ 폴더에 배치하세요."
    exit 1
fi

# 6. Docker Compose로 서비스 시작
echo "🌟 서비스 시작..."
if [ "$ENVIRONMENT" = "production" ]; then
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
else
    docker-compose up -d
fi

# 7. 서비스 상태 확인
echo "🔍 서비스 상태 확인 중..."
sleep 10

# 헬스체크
for i in {1..30}; do
    if curl -s http://localhost:8000/api/damage-analysis/health > /dev/null; then
        echo "✅ 서비스가 정상적으로 시작되었습니다!"
        echo "🌐 서비스 URL: http://localhost:8000"
        echo "📊 헬스체크: http://localhost:8000/api/damage-analysis/health"
        echo "📖 API 문서: http://localhost:8000/docs"
        break
    else
        echo "⏳ 서비스 시작 대기 중... ($i/30)"
        sleep 2
    fi

    if [ $i -eq 30 ]; then
        echo "❌ 서비스 시작에 실패했습니다. 로그를 확인하세요:"
        echo "docker logs $CONTAINER_NAME"
        exit 1
    fi
done

echo "🎉 배포 완료!"
