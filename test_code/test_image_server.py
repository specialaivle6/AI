"""
테스트용 로컬 이미지 서버
실제 S3 URL 대신 로컬 파일을 서빙하는 Mock 서버
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import uvicorn
import asyncio
from contextlib import asynccontextmanager

# 테스트 이미지 경로
TEST_IMAGES_DIR = Path("test_code/test_images")


@asynccontextmanager
async def server_lifespan(app: FastAPI):
    """테스트 서버 생명주기 관리 (함수명 변경으로 pytest 수집 방지)"""
    print("🔄 테스트 이미지 서버 시작...")
    yield
    print("🔄 테스트 이미지 서버 종료")


# 테스트용 FastAPI 앱
test_app = FastAPI(
    title="Test Image Server",
    description="테스트용 로컬 이미지 서버",
    lifespan=server_lifespan  # 함수명 변경
)


@test_app.get("/test-images/{image_name}")
async def serve_test_image(image_name: str):
    """테스트 이미지 파일 서빙"""

    # valid 디렉토리에서 먼저 찾기
    valid_path = TEST_IMAGES_DIR / "valid" / image_name
    if valid_path.exists():
        return FileResponse(
            path=str(valid_path),
            media_type="image/jpeg",
            headers={"Content-Disposition": f"inline; filename={image_name}"}
        )

    # invalid 디렉토리에서 찾기
    invalid_path = TEST_IMAGES_DIR / "invalid" / image_name
    if invalid_path.exists():
        return FileResponse(
            path=str(invalid_path),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"inline; filename={image_name}"}
        )

    raise HTTPException(status_code=404, detail=f"Image {image_name} not found")


@test_app.get("/health")
async def health_check():
    """테스트 서버 헬스체크"""
    return {"status": "ok", "message": "Test image server is running"}


# 테스트 서버 시작 함수
async def start_test_server(port: int = 9000):
    """테스트 서버를 백그라운드에서 시작"""
    config = uvicorn.Config(
        test_app,
        host="127.0.0.1",
        port=port,
        log_level="warning"  # 테스트 중 로그 최소화
    )
    server = uvicorn.Server(config)

    # 백그라운드 태스크로 서버 실행
    task = asyncio.create_task(server.serve())

    # 서버가 시작될 때까지 잠시 대기
    await asyncio.sleep(1)

    return server, task


if __name__ == "__main__":
    # 직접 실행시 테스트 서버 시작
    uvicorn.run(
        test_app,
        host="127.0.0.1",
        port=9000,
        log_level="info"
    )
