import boto3, os, time
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
from typing import Optional, List, Union
import asyncio
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=False)

from app.core.config import settings, validate_settings
from app.core.exceptions import (
    AIServiceException, ModelNotLoadedException,
    get_http_status_code, EXCEPTION_STATUS_MAPPING
)
from app.core.logging_config import setup_logging, get_logger, log_api_request, log_model_status

from app.services.damage_analyzer import DamageAnalyzer

from app.services.performance_analyzer import PerformanceAnalyzer
from app.schemas.schemas import (
    DamageAnalysisRequest,
    DamageAnalysisResponse,
    HealthCheckResponse,
    PanelRequest,
    PerformanceReportResponse,
    PerformanceReportDetailResponse,
    PerformanceAnalysisResult, ReportItemResult
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
PRESIGN_EXP_SECONDS = int(os.getenv("PRESIGN_EXP_SECONDS", "900"))

s3 = boto3.client("s3", region_name=AWS_REGION)

# 로깅 초기화
setup_logging()
logger = get_logger(__name__)

# 전역 변수로 서비스들 관리
damage_analyzer: Optional[DamageAnalyzer] = None
performance_analyzer: Optional[PerformanceAnalyzer] = None

load_dotenv(find_dotenv(), override=False)


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


from app.schemas.schemas import (
    # ...
    PerformanceReportResponse,
    PerformanceReportDetailResponse,
    PerformanceAnalysisResult,
)

# 기존 함수 시그니처/데코레이터 교체
@app.post("/api/performance-analysis/report",
          response_model=List[PerformanceReportResponse])
async def generate_performance_report_endpoint(
    request: List[PanelRequest],
    address_mode: str = Query("key", pattern="^(key|url|presigned)$")  # ✅ 선택지
):
    if performance_analyzer is None or not performance_analyzer.is_loaded():
        raise ModelNotLoadedException("PerformanceAnalyzer", settings.performance_model_path)

    concurrency = getattr(settings, "batch_max_concurrency", 4)
    sem = asyncio.Semaphore(concurrency)

    async def run_one(p: PanelRequest) -> PerformanceReportResponse:
        async with sem:
            log_api_request("POST", "/api/performance-analysis/report(batch)", p.user_id, p.id)

            # 1) 분석
            analysis = await performance_analyzer.analyze_performance(p)

            # 2) PDF 생성
            report_path = generate_performance_report(
                predicted=analysis["predicted_generation"],
                actual=analysis["actual_generation"],
                status=analysis["status"],
                user_id=p.user_id,
                lifespan=analysis.get("lifespan_months", 0) / 12 if analysis.get("lifespan_months") else None,
                cost=analysis.get("estimated_cost"),
            )

            # 3) S3 업로드 (키는 {user_id}/{panel_id}_{ts}.pdf 규칙 사용)
            ts = int(time.time())                                 # 이걸 report_id로 사용
            key = f"reports/{p.user_id}/{p.id}_{ts}.pdf"
            item = upload_pdf_to_s3(report_path, key)

            try:
                os.remove(report_path)
            except FileNotFoundError:
                pass

            # 4) 응답 address 선택
            if address_mode == "url":
                addr = item.s3Url
            elif address_mode == "presigned":
                addr = item.presignedUrl
            else:
                addr = item.s3Key

            return PerformanceReportResponse(
                user_id=p.user_id,
                address=addr,
                created_at=datetime.now().isoformat()
            )

    return await asyncio.gather(*[run_one(p) for p in request])




@app.post(
    "/api/performance-analysis/analyze",
    response_model=Union[PerformanceReportDetailResponse, List[PerformanceReportDetailResponse]],
)
async def analyze_performance_detailed(request: Union[PanelRequest, List[PanelRequest]]):
    """
    상세한 성능 분석 (PDF 생성 없이 분석 결과만 반환)
    단건/배치 모두 지원:
    - 단건 -> PerformanceReportDetailResponse
    - 배열 -> PerformanceReportDetailResponse[]
    """
    start_time = time.time()

    if performance_analyzer is None or not performance_analyzer.is_loaded():
        raise ModelNotLoadedException("PerformanceAnalyzer", settings.performance_model_path)

    # --- 배열 처리 ---
    if isinstance(request, list):
        concurrency = getattr(settings, "batch_max_concurrency", 4)
        sem = asyncio.Semaphore(concurrency)

        async def run_one(p: PanelRequest) -> PerformanceReportDetailResponse:
            async with sem:
                log_api_request("POST", "/api/performance-analysis/analyze(batch)", p.user_id, p.id)
                ar = await performance_analyzer.analyze_performance(p)

                perf = PerformanceAnalysisResult(
                    predicted_generation=ar["predicted_generation"],
                    actual_generation=ar["actual_generation"],
                    performance_ratio=ar["performance_ratio"],
                    status=ar["status"],
                    lifespan_months=ar.get("lifespan_months"),
                    estimated_cost=ar.get("estimated_cost")
                )

                return PerformanceReportDetailResponse(
                    user_id=p.user_id,
                    panel_id=p.id,
                    performance_analysis=perf,
                    report_path="",
                    created_at=datetime.now().isoformat(),
                    processing_time_seconds=None,
                    panel_info=ar.get("panel_info", {}),
                    environmental_data=ar.get("environmental_data", {})
                )

        tasks = [run_one(p) for p in request]
        return await asyncio.gather(*tasks)

    # --- 단건 처리(기존 로직) ---
    try:
        p: PanelRequest = request
        log_api_request("POST", "/api/performance-analysis/analyze", p.user_id, p.id)
        ar = await performance_analyzer.analyze_performance(p)
        processing_time = time.time() - start_time
        log_api_request("POST", "/api/performance-analysis/analyze",
                       p.user_id, p.id, processing_time)

        perf = PerformanceAnalysisResult(
            predicted_generation=ar["predicted_generation"],
            actual_generation=ar["actual_generation"],
            performance_ratio=ar["performance_ratio"],
            status=ar["status"],
            lifespan_months=ar.get("lifespan_months"),
            estimated_cost=ar.get("estimated_cost")
        )

        return PerformanceReportDetailResponse(
            user_id=p.user_id,
            panel_id=p.id,
            performance_analysis=perf,
            report_path="",
            created_at=datetime.now().isoformat(),
            processing_time_seconds=processing_time,
            panel_info=ar.get("panel_info", {}),
            environmental_data=ar.get("environmental_data", {})
        )

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

# --- S3 client ---

session = boto3.session.Session(
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
    region_name=AWS_REGION,
)

s3_client = session.client("s3")

try:
    sts = session.client("sts")
    ident = sts.get_caller_identity()
    ak = os.getenv("AWS_ACCESS_KEY_ID") or ""
    logger.info(
        f"AWS credentials OK (acct={ident['Account']}, arn={ident['Arn']}, key=***{ak[-4:]})"
    )
except Exception as e:
    logger.error(f"AWS credentials NOT found/invalid: {e}")

def upload_pdf_to_s3(local_path: str, key: str) -> ReportItemResult:
    content_type = "application/pdf"
    size = os.path.getsize(local_path)
    extra_args = {
        "ContentType": content_type,
        "ContentDisposition": f'attachment; filename="{os.path.basename(local_path)}"'
    }
    try:
        resp = s3_client.upload_file(
            Filename=local_path,
            Bucket=S3_BUCKET,
            Key=key,
            ExtraArgs=extra_args
        )
        head = s3_client.head_object(Bucket=S3_BUCKET, Key=key)
        e_tag = head.get("ETag", "").strip('"')

        s3_url = f"https://{S3_BUCKET}.s3.{os.getenv('AWS_DEFAULT_REGION','ap-northeast-2')}.amazonaws.com/{key}"
        presigned = s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": S3_BUCKET, "Key": key},
            ExpiresIn=PRESIGN_EXP_SECONDS
        )
        expires_at = str(int(time.time()) + PRESIGN_EXP_SECONDS)

        return ReportItemResult(
            id=int(os.path.basename(key).split("_")[0]) if "_" in os.path.basename(key) else -1,
            s3Key=key,
            s3Url=s3_url,
            presignedUrl=presigned,
            expiresAt=expires_at,
            contentType=content_type,
            contentLength=size,
            eTag=e_tag
        )
    except (BotoCoreError, ClientError) as e:
        raise HTTPException(status_code=500, detail=f"S3 upload failed: {e}")
