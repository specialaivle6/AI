from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from pathlib import Path

from app.models.model_loader import ModelLoader
from app.services.image_processor import ImageProcessor
from app.services.result_processor import ResultProcessor
from app.core.config import settings

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="Solar Panel AI Service",
    description="태양광 패널 상태 분석 AI 서비스",
    version="1.0.0"
)

# CORS 설정 (React 프론트엔드와 통신용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React 개발 서버
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 변수로 모델과 프로세서 관리
model_loader = None
image_processor = None
result_processor = None


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 모델 로딩"""
    global model_loader, image_processor, result_processor

    logger.info("AI 모델 로딩 시작...")
    model_loader = ModelLoader()
    await model_loader.load_model()

    image_processor = ImageProcessor()
    result_processor = ResultProcessor()

    logger.info("AI 서비스 준비 완료!")


@app.get("/")
async def root():
    """헬스체크 엔드포인트"""
    return {"message": "Solar Panel AI Service is running"}


@app.get("/health")
async def health_check():
    """상세 헬스체크"""
    return {
        "status": "healthy",
        "model_loaded": model_loader.is_loaded() if model_loader else False,
        "version": "1.0.0"
    }


@app.post("/analyze-panel")
async def analyze_panel_image(file: UploadFile = File(...)):
    """
    태양광 패널 이미지 분석

    Returns:
        - predicted_class: 예측된 클래스명
        - confidence: 신뢰도 (0-1)
        - probabilities: 모든 클래스별 확률
        - recommendations: 추천 조치사항
    """
    try:
        # 파일 유효성 검사
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")

        # 이미지 읽기
        image_bytes = await file.read()

        # 이미지 전처리
        processed_image = image_processor.preprocess(image_bytes)

        # AI 모델 추론
        prediction = await model_loader.predict(processed_image)

        # 결과 후처리
        result = result_processor.process_prediction(prediction)

        logger.info(f"이미지 분석 완료: {result['predicted_class']} (신뢰도: {result['confidence']:.2f})")

        return result

    except Exception as e:
        logger.error(f"이미지 분석 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 중 오류가 발생했습니다: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 개발 모드에서만 사용
        log_level="info"
    )