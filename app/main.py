from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging

from app.services import DamageAnalyzer

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 전역 변수로 손상 분석기 관리
damage_analyzer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 생명주기 관리 (FastAPI 최신 방식)"""
    global damage_analyzer

    # Startup
    logger.info("YOLOv8 모델 로딩 시작...")
    damage_analyzer = DamageAnalyzer()
    await damage_analyzer.initialize()
    logger.info("AI 서비스 준비 완료!")

    yield

    # Shutdown
    logger.info("AI 서비스 종료")


# FastAPI 앱 생성
app = FastAPI(
    title="Solar Panel AI Service",
    description="태양광 패널 손상 분석 AI 서비스 (YOLOv8 기반)",
    version="2.0.0",
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
        "model_loaded": damage_analyzer.is_loaded() if damage_analyzer else False,
        "version": "2.0.0",
        "model_type": "YOLOv8"
    }


@app.post("/analyze-damage")
async def analyze_panel_damage(file: UploadFile = File(...)):
    """
    태양광 패널 손상 분석 (YOLOv8 기반)

    Returns:
        - damage_analysis: 세부 손상 분석 결과
        - business_assessment: 비즈니스 평가 및 권장사항
        - detection_details: 검출된 객체 상세 정보
        - confidence_score: 전체 신뢰도
    """
    try:
        # 파일 유효성 검사
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")

        # 이미지 읽기
        image_bytes = await file.read()

        # YOLOv8 기반 손상 분석
        result = await damage_analyzer.analyze_damage(image_bytes, file.filename)

        logger.info(f"손상 분석 완료: {file.filename} - 전체 손상률: {result['damage_analysis']['overall_damage_percentage']:.2f}%")

        return result

    except Exception as e:
        logger.error(f"손상 분석 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 중 오류가 발생했습니다: {str(e)}")


@app.post("/batch-analyze")
async def batch_analyze_panels(files: list[UploadFile] = File(...)):
    """
    여러 패널 이미지 일괄 분석
    """
    try:
        if len(files) > 10:  # 최대 10개 파일 제한
            raise HTTPException(status_code=400, detail="최대 10개 파일까지 업로드 가능합니다.")

        results = []
        for file in files:
            if not file.content_type.startswith("image/"):
                continue  # 이미지가 아닌 파일은 건너뛰기

            image_bytes = await file.read()
            result = await damage_analyzer.analyze_damage(image_bytes, file.filename)
            results.append(result)

        logger.info(f"일괄 분석 완료: {len(results)}개 파일")

        return {
            "total_analyzed": len(results),
            "results": results,
            "summary": damage_analyzer.generate_batch_summary(results)
        }

    except Exception as e:
        logger.error(f"일괄 분석 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"일괄 분석 중 오류가 발생했습니다: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )