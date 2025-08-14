from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import time
from typing import Optional
from datetime import datetime

# 개선된 임포트
from app.core.config import settings, validate_settings
from app.core.exceptions import (
    AIServiceException, ModelNotLoadedException,
    get_http_status_code, EXCEPTION_STATUS_MAPPING
)
from app.core.logging_config import setup_logging, get_logger, log_api_request, log_model_status

from app.services.damage_analyzer import DamageAnalyzer
from app.services.performance_analyzer import PerformanceAnalyzer
from app.models.schemas import (
    DamageAnalysisRequest,
    DamageAnalysisResponse,
    HealthCheckResponse,
    PanelRequest,
    PerformanceReportResponse,
    PerformanceReportDetailResponse,
    PerformanceAnalysisResult
)
from app.utils.image_utils import download_image_from_s3, get_image_info
from app.utils.report_generator import generate_performance_report
from app.utils.performance_utils import estimate_panel_cost

""" s3 업로드용 """
import os, time
import boto3
from botocore.exceptions import BotoCoreError, ClientError

AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "ap-northeast-2")
S3_BUCKET = os.getenv("S3_BUCKET", "solar-panel-storage")

s3 = boto3.client("s3", region_name=AWS_REGION)

# 로깅 초기화
setup_logging()
logger = get_logger(__name__)

# 전역 변수로 서비스들 관리
damage_analyzer: Optional[DamageAnalyzer] = None
performance_analyzer: Optional[PerformanceAnalyzer] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 생명주기 관리"""
    global damage_analyzer, performance_analyzer

    # Startup
    logger.info(f"🚀 {settings.app_name} v{settings.app_version} 초기화 시작...")

    # 설정 검증
    config_issues = validate_settings()
    if config_issues:
        logger.warning("⚠️ 설정 검증 결과:")
        for issue in config_issues:
            logger.warning(f"  - {issue}")

    try:
        # 손상 분석기 초기화
        log_model_status("DamageAnalyzer", "loading", path=settings.damage_model_path)
        damage_analyzer = DamageAnalyzer()
        await damage_analyzer.initialize()
        log_model_status("DamageAnalyzer", "loaded",
                        loaded=damage_analyzer.is_loaded())

        # 성능 분석기 초기화
        log_model_status("PerformanceAnalyzer", "loading", path=settings.performance_model_path)
        performance_analyzer = PerformanceAnalyzer()
        await performance_analyzer.initialize()
        log_model_status("PerformanceAnalyzer", "loaded",
                        loaded=performance_analyzer.is_loaded())

        logger.info("✅ AI 서비스 준비 완료!")

    except Exception as e:
        logger.error(f"❌ 서비스 초기화 실패: {e}")
        raise

    yield

    # Shutdown
    logger.info("🔄 AI 서비스 종료 중...")


# FastAPI 앱 생성 (개선된 설정 사용)
app = FastAPI(
    title=settings.app_name,
    description=settings.description,
    version=settings.app_version,
    lifespan=lifespan
)

# CORS 설정 (설정 파일에서 가져오기)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 전역 예외 처리기
@app.exception_handler(AIServiceException)
async def ai_service_exception_handler(request: Request, exc: AIServiceException):
    """AI 서비스 커스텀 예외 처리"""
    logger.error(f"AI Service Error: {exc.message}", extra={"details": exc.details})

    return JSONResponse(
        status_code=get_http_status_code(exc),
        content={
            "error": exc.error_code or "AI_SERVICE_ERROR",
            "message": exc.message,
            "details": exc.details,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 처리"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "내부 서버 오류가 발생했습니다",
            "timestamp": datetime.now().isoformat()
        }
    )


def _check_service_health(analyzer, service_name: str) -> dict:
    """서비스 헬스체크 공통 로직"""
    if analyzer is None:
        return {
            "status": "unhealthy",
            "model_loaded": False,
            "error": f"{service_name} 초기화되지 않음"
        }

    is_healthy = analyzer.is_loaded()
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "model_loaded": is_healthy,
        "error": None if is_healthy else f"{service_name} 모델 로드 실패"
    }


@app.get("/")
async def root():
    """기본 엔드포인트"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "environment": "development" if settings.is_development else "production",
        "models": {
            "damage_analysis": "YOLOv8 Segmentation",
            "performance_prediction": "Voting Ensemble"
        }
    }


@app.get("/api/damage-analysis/health", response_model=HealthCheckResponse)
async def damage_health_check():
    """손상 분석 서비스 헬스체크"""
    health_info = _check_service_health(damage_analyzer, "DamageAnalyzer")

    return HealthCheckResponse(
        status=health_info["status"],
        model_loaded=health_info["model_loaded"],
        version=settings.app_version,
        model_type="YOLOv8"
    )


@app.post("/api/damage-analysis/analyze", response_model=DamageAnalysisResponse)
async def analyze_panel_damage_from_s3(request: DamageAnalysisRequest):
    """백엔드에서 요청받은 S3 URL로 패널 손상 분석 수행"""
    start_time = time.time()

    # 서비스 상태 확인
    if damage_analyzer is None or not damage_analyzer.is_loaded():
        raise ModelNotLoadedException("DamageAnalyzer", settings.damage_model_path)

    try:
        log_api_request("POST", "/api/damage-analysis/analyze",
                       str(request.user_id), request.panel_id)

        # S3에서 이미지 다운로드
        image_data = await download_image_from_s3(request.panel_imageurl)
        image_info = get_image_info(image_data, request.panel_imageurl)

        # AI 분석 수행
        analysis_result = await damage_analyzer.analyze_damage(image_data)
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

        log_api_request("POST", "/api/damage-analysis/analyze",
                       str(request.user_id), request.panel_id, processing_time)

        return response

    except AIServiceException:
        raise
    except Exception as e:
        logger.error(f"손상 분석 중 예상치 못한 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"분석 처리 오류: {str(e)}")


@app.get("/api/performance-analysis/health")
async def performance_health_check():
    """성능 예측 서비스 헬스체크"""
    health_info = _check_service_health(performance_analyzer, "PerformanceAnalyzer")

    return {
        **health_info,
        "service": "performance-analysis",
        "version": settings.app_version
    }


@app.post("/api/performance-analysis/report", response_model=PerformanceReportResponse)
async def generate_performance_report_endpoint(request: PanelRequest):
    """태양광 패널 성능 예측 및 PDF 리포트 생성"""
    start_time = time.time()

    # 서비스 상태 확인
    if performance_analyzer is None or not performance_analyzer.is_loaded():
        raise ModelNotLoadedException("PerformanceAnalyzer", settings.performance_model_path)

    try:
        log_api_request("POST", "/api/performance-analysis/report", request.user_id, request.id)

        # 성능 분석 수행
        analysis_result = await performance_analyzer.analyze_performance(request)

        # PDF 리포트 생성
        report_path = generate_performance_report(
            predicted=analysis_result["predicted_generation"],
            actual=analysis_result["actual_generation"],
            status=analysis_result["status"],
            user_id=request.user_id,
            lifespan=analysis_result.get("lifespan_months", 0) / 12 if analysis_result.get("lifespan_months") else None,
            cost=analysis_result.get("estimated_cost")
        )

        s3_key = upload_pdf_to_s3(report_path, request.user_id)

        # (선택) 로컬 파일 정리
        try:
            os.remove(report_path)
        except FileNotFoundError:
            pass

        response = PerformanceReportResponse(
            user_id=request.user_id,
            address=s3_key,                                  # ✅ 로컬 경로 대신 S3 key로 반환
            created_at=datetime.now().isoformat()
        )

        return response

    except AIServiceException:
        raise
    except Exception as e:
        logger.error(f"성능 분석 중 예상치 못한 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"성능 분석 처리 오류: {str(e)}")


@app.post("/api/performance-analysis/analyze", response_model=PerformanceReportDetailResponse)
async def analyze_performance_detailed(request: PanelRequest):
    """상세한 성능 분석 (PDF 생성 없이 분석 결과만 반환)"""
    start_time = time.time()

    # 서비스 상태 확인
    if performance_analyzer is None or not performance_analyzer.is_loaded():
        raise ModelNotLoadedException("PerformanceAnalyzer", settings.performance_model_path)

    try:
        log_api_request("POST", "/api/performance-analysis/analyze", request.user_id, request.id)

        # 성능 분석 수행
        analysis_result = await performance_analyzer.analyze_performance(request)
        processing_time = time.time() - start_time

        # 성능 분석 결과 구성
        performance_analysis = PerformanceAnalysisResult(
            predicted_generation=analysis_result["predicted_generation"],
            actual_generation=analysis_result["actual_generation"],
            performance_ratio=analysis_result["performance_ratio"],
            status=analysis_result["status"],
            lifespan_months=analysis_result.get("lifespan_months"),
            estimated_cost=analysis_result.get("estimated_cost")
        )

        response = PerformanceReportDetailResponse(
            user_id=request.user_id,
            panel_id=request.id,
            performance_analysis=performance_analysis,
            report_path="",
            created_at=datetime.now().isoformat(),
            processing_time_seconds=processing_time,
            panel_info=analysis_result.get("panel_info", {}),
            environmental_data=analysis_result.get("environmental_data", {})
        )

        log_api_request("POST", "/api/performance-analysis/analyze",
                       request.user_id, request.id, processing_time)

        return response

    except AIServiceException:
        raise
    except Exception as e:
        logger.error(f"상세 성능 분석 중 예상치 못한 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"상세 분석 처리 오류: {str(e)}")
        

def upload_pdf_to_s3(local_path: str, user_id) -> str:
    """
    로컬 PDF를 S3에 업로드하고 S3 object key를 반환.
    파일명 충돌 방지를 위해 timestamp 포함.
    """
    file_name = os.path.basename(local_path) or "report.pdf"
    ts = int(time.time())
    key = f"reports/{user_id}/{ts}.pdf"
    extra = {
        "ContentType": "application/pdf",
        "ContentDisposition": f'attachment; filename="{file_name}"'
    }
    try:
        s3.upload_file(Filename=local_path, Bucket=S3_BUCKET, Key=key, ExtraArgs=extra)
        return key
    except (BotoCoreError, ClientError) as e:
        raise HTTPException(status_code=500, detail=f"S3 upload failed: {e}")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        log_level=settings.log_level.lower()
    )

