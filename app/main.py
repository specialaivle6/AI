from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging
import time
from typing import Optional

from app.services.damage_analyzer import DamageAnalyzer
from app.models.schemas import (
    DamageAnalysisRequest,
    DamageAnalysisResponse,
    HealthCheckResponse
)
from app.utils.image_utils import download_image_from_s3, get_image_info

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 전역 변수로 서비스들 관리
damage_analyzer: Optional[DamageAnalyzer] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 생명주기 관리 (FastAPI 최신 방식)"""
    global damage_analyzer

    # Startup
    logger.info("AI 손상 분석 서비스 초기화 시작...")

    # AI 분석기만 로드 (DB 연동 제거)
    damage_analyzer = DamageAnalyzer()
    await damage_analyzer.initialize()

    logger.info("AI 손상 분석 서비스 준비 완료!")

    yield

    # Shutdown
    logger.info("AI 서비스 종료")


# FastAPI 앱 생성
app = FastAPI(
    title="Solar Panel AI Service",
    description="태양광 패널 손상 분석 AI 서비스 - 백엔드 연동용",
    version="3.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 백엔드 서버와 통신
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """기본 헬스체크 엔드포인트"""
    return {
        "message": "Solar Panel AI Service is running",
        "version": "3.0.0",
        "model": "YOLOv8 Segmentation",
        "mode": "Backend Integration"
    }


@app.get("/api/damage-analysis/health", response_model=HealthCheckResponse)
async def health_check():
    """손상 분석 서비스 상세 헬스체크"""
    if damage_analyzer is None:
        return HealthCheckResponse(
            status="unhealthy",
            model_loaded=False,
            version="3.0.0"
        )

    is_healthy = damage_analyzer.is_loaded()
    return HealthCheckResponse(
        status="healthy" if is_healthy else "unhealthy",
        model_loaded=is_healthy,
        version="3.0.0"
    )


@app.post("/api/damage-analysis/analyze", response_model=DamageAnalysisResponse)
async def analyze_panel_damage_from_s3(request: DamageAnalysisRequest):
    """
    백엔드에서 요청받은 S3 URL로 패널 손상 분석 수행
    """
    start_time = time.time()

    try:
        if damage_analyzer is None or not damage_analyzer.is_loaded():
            raise HTTPException(
                status_code=503,
                detail="AI 모델이 로드되지 않았습니다."
            )

        logger.info(f"패널 ID {request.panel_id} 분석 시작: {request.panel_imageurl}")

        # S3에서 이미지 다운로드
        try:
            image_data = await download_image_from_s3(request.panel_imageurl)
        except Exception as e:
            logger.error(f"S3 이미지 다운로드 실패: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"이미지 다운로드 실패: {str(e)}"
            )

        # 이미지 정보 획득
        image_info = get_image_info(image_data, request.panel_imageurl)

        # AI 분석 수행
        try:
            analysis_result = await damage_analyzer.analyze_damage(image_data)
        except Exception as e:
            logger.error(f"AI 분석 실패: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"AI 분석 실패: {str(e)}"
            )

        processing_time = time.time() - start_time

        # 응답 구성
        response = DamageAnalysisResponse(
            panel_id=request.panel_id,
            user_id=request.user_id,
            image_info=image_info,
            damage_analysis=analysis_result["damage_analysis"],
            business_assessment=analysis_result["business_assessment"],
            detection_details=analysis_result["detection_details"],
            confidence_score=analysis_result["confidence_score"],
            processing_time_seconds=processing_time
        )

        logger.info(f"패널 ID {request.panel_id} 분석 완료 (소요시간: {processing_time:.2f}초)")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"내부 서버 오류: {str(e)}"
        )


# === 개발/테스트용 엔드포인트 ===

@app.get("/api/damage-analysis/status")
async def get_service_status():
    """서비스 상태 정보 (개발용)"""
    return {
        "service": "damage-analysis",
        "model_loaded": damage_analyzer.is_loaded() if damage_analyzer else False,
        "version": "3.0.0",
        "supported_formats": ["jpg", "jpeg", "png", "bmp", "tiff", "webp"],
        "max_image_size": "20MB"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )