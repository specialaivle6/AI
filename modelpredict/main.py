# main.py는 이제 앱 생성과 라우터 등록만 담당
# main.py (FastAPI 엔트리포인트)
from fastapi import FastAPI
from api.report_router import router as report_router

app = FastAPI()
app.include_router(report_router, prefix="/report", tags=["Report"])

@app.get("/")
def root():
    return {"msg": "Solar Panel Performance API is running"}