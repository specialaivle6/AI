from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging
from typing import List

from app.services.damage_analyzer import DamageAnalyzer
from app.services.panel_analysis_service import PanelAnalysisService
from app.models.schemas import AnalysisRequest, AnalysisResponse, RequestStatus
from app.utils import validate_image_file, get_image_info, is_valid_panel_image

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 전역 변수로 서비스들 관리
damage_analyzer = None
panel_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 생명주기 관리 (FastAPI 최신 방식)"""
    global damage_analyzer, panel_service

    # Startup
    logger.info("AI 서비스들 초기화 시작...")

    # 기존 AI 분석기
    damage_analyzer = DamageAnalyzer()
    await damage_analyzer.initialize()

    # 통합 패널 분석 서비스
    panel_service = PanelAnalysisService()
    await panel_service.initialize()

    logger.info("모든 AI 서비스 준비 완료!")

    yield

    # Shutdown
    logger.info("AI 서비스 종료")


# FastAPI 앱 생성
app = FastAPI(
    title="Solar Panel AI Service",
    description="태양광 패널 손상 분석 AI 서비스 (YOLOv8 기반 + DB 연동)",
    version="2.1.0",
    lifespan=lifespan
)

# CORS 설정 (React 프론트엔드와 통신용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React 개발 서버
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """헬스체크 엔드포인트"""
    return {
        "message": "Solar Panel Damage Analysis Service is running",
        "version": "2.0.0",
        "model": "YOLOv8 Segmentation"
    }


@app.get("/health")
async def health_check():
    """상세 헬스체크"""
    return {
        "status": "healthy",
        "ai_model_loaded": damage_analyzer.is_loaded() if damage_analyzer else False,
        "panel_service_ready": panel_service.is_ready() if panel_service else False,
        "version": "2.1.0",
        "model_type": "YOLOv8"
    }


# 기존 API 유지 (호환성)
@app.post("/analyze-damage")
async def analyze_panel_damage(file: UploadFile = File(...)):
    """
    기존 API - 단순 AI 분석만 (DB 연동 없음)
    호환성을 위해 유지
    """
    try:
        # 이미지 읽기
        image_bytes = await file.read()

        # 향상된 파일 유효성 검사
        if not validate_image_file(image_bytes, file.filename):
            raise HTTPException(status_code=400, detail="유효하지 않은 이미지 파일입니다.")

        # 이미지 정보 확인
        image_info = get_image_info(image_bytes)
        if not image_info:
            raise HTTPException(status_code=400, detail="이미지 정보를 읽을 수 없습니다.")

        # 패널 이미지 적합성 검증
        is_valid, message = is_valid_panel_image(image_info)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"패널 이미지로 부적합: {message}")

        # YOLOv8 기반 손상 분석
        result = await damage_analyzer.analyze_damage(image_bytes, file.filename)

        # 이미지 정보 추가
        result['image_info'].update({
            'original_size': f"{image_info['width']}x{image_info['height']}",
            'file_size_mb': round(image_info['size_bytes'] / (1024 * 1024), 2),
            'aspect_ratio': image_info['aspect_ratio']
        })

        logger.info(f"손상 분석 완료: {file.filename} - 전체 손상률: {result['damage_analysis']['overall_damage_percentage']:.2f}%")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"손상 분석 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 중 오류가 발생했습니다: {str(e)}")


# 새로운 비즈니스 요구사항 API들
@app.post("/panels/analyze", response_model=AnalysisResponse)
async def analyze_panel_with_database(
    file: UploadFile = File(...),
    panel_id: int = None,
    user_id: str = None  # UUID에서 str로 변경
):
    """
    패널 분석 + 데이터베이스 연동 (신규 API)

    실제 비즈니스 요구사항에 맞는 완전한 분석 서비스:
    1. AI 모델로 이미지 분석
    2. PanelImage 테이블에 이미지 정보 저장
    3. PanelImageReport 테이블에 분석 결과 저장
    4. 통합된 결과 반환
    """
    try:
        if not panel_id or not user_id:
            raise HTTPException(status_code=400, detail="panel_id와 user_id가 필요합니다.")

        # UUID 형식 검증 및 변환 (유연하게)
        try:
            from uuid import UUID
            import hashlib

            # 문자열이 UUID 형식인지 확인
            if len(user_id) == 36 and user_id.count('-') == 4:
                user_uuid = UUID(user_id)
            else:
                # 짧은 문자열을 안정적인 UUID로 변환
                uuid_str = hashlib.md5(user_id.encode()).hexdigest()
                user_uuid = UUID(f"{uuid_str[:8]}-{uuid_str[8:12]}-{uuid_str[12:16]}-{uuid_str[16:20]}-{uuid_str[20:32]}")
                logger.info(f"user_id '{user_id}'를 UUID '{user_uuid}'로 변환했습니다.")
        except Exception as e:
            logger.error(f"UUID 변환 실패: {str(e)}")
            raise HTTPException(status_code=400, detail="user_id 형식을 처리할 수 없습니다.")

        # 파일 유효성 검사
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")

        # 이미지 읽기
        image_bytes = await file.read()

        # 분석 요청 객체 생성 (UUID 사용)
        request = AnalysisRequest(
            panel_id=panel_id,
            user_id=user_uuid,  # 변환된 UUID 사용
            panel_imageurl=f"uploads/{file.filename}"
        )

        # 통합 분석 실행
        result = await panel_service.analyze_panel_with_db_integration(
            image_bytes, request, file.filename
        )

        logger.info(f"패널 분석 완료: panel_id={panel_id}, report_id={result.panel_image_report_id}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"패널 분석 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 중 오류가 발생했습니다: {str(e)}")


@app.get("/panels/{panel_id}/history")
async def get_panel_analysis_history(panel_id: int):
    """
    특정 패널의 분석 이력 조회

    PanelImage와 PanelImageReport 테이블에서 해당 패널의 모든 이력을 조회합니다.
    """
    try:
        history = await panel_service.get_panel_analysis_history(panel_id)
        return history
    except Exception as e:
        logger.error(f"패널 이력 조회 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"이력 조회 중 오류가 발생했습니다: {str(e)}")


@app.post("/panels/batch-analyze")
async def batch_analyze_panels_with_database(
    files: List[UploadFile] = File(...),
    panel_ids: List[int] = None,
    user_ids: List[str] = None
):
    """
    여러 패널 일괄 분석 + 데이터베이스 연동

    각 이미지마다 panel_id와 user_id를 매핑하여 일괄 분석합니다.
    """
    try:
        if not panel_ids or not user_ids:
            raise HTTPException(status_code=400, detail="panel_ids와 user_ids가 필요합니다.")

        if len(files) != len(panel_ids) or len(files) != len(user_ids):
            raise HTTPException(status_code=400, detail="파일 수, panel_id 수, user_id 수가 일치해야 합니다.")

        if len(files) > 10:
            raise HTTPException(status_code=400, detail="최대 10개 파일까지 업로드 가능합니다.")

        # 파일 데이터 준비
        files_data = []
        requests = []

        for i, file in enumerate(files):
            if not file.content_type.startswith("image/"):
                continue

            image_bytes = await file.read()
            files_data.append(image_bytes)

            # UUID 변환 처리
            user_id = user_ids[i]
            try:
                from uuid import UUID
                import hashlib

                if len(user_id) == 36 and user_id.count('-') == 4:
                    user_uuid = UUID(user_id)
                else:
                    uuid_str = hashlib.md5(user_id.encode()).hexdigest()
                    user_uuid = UUID(f"{uuid_str[:8]}-{uuid_str[8:12]}-{uuid_str[12:16]}-{uuid_str[16:20]}-{uuid_str[20:32]}")
            except Exception as e:
                logger.error(f"UUID 변환 실패 (index {i}): {str(e)}")
                raise HTTPException(status_code=400, detail=f"user_id[{i}] 형식을 처리할 수 없습니다.")

            requests.append(AnalysisRequest(
                panel_id=panel_ids[i],
                user_id=user_uuid,
                panel_imageurl=f"uploads/{file.filename}"
            ))

        # 일괄 분석 실행
        result = await panel_service.batch_analyze_with_db(files_data, requests)

        logger.info(f"일괄 분석 완료: 성공 {result['successful']}개, 실패 {result['failed']}개")
        return result

    except Exception as e:
        logger.error(f"일괄 분석 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"일괄 분석 중 오류가 발생했습니다: {str(e)}")


@app.put("/reports/{report_id}/status")
async def update_report_status(
    report_id: int,
    status: RequestStatus
):
    """
    리포트 상태 업데이트 (관리자용)

    PanelImageReport의 request_status를 업데이트합니다.
    - 요청 중 → 요청확인 → 처리중 → 처리 완료
    """
    try:
        success = await panel_service.update_report_status(report_id, status)

        if success:
            return {"message": "리포트 상태가 업데이트되었습니다.", "report_id": report_id, "new_status": status}
        else:
            raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다.")

    except Exception as e:
        logger.error(f"리포트 상태 업데이트 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"상태 업데이트 중 오류가 발생했습니다: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )