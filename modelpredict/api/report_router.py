#클라이언트가 /report 엔드포인트로 POST 요청을 보낼 때 이 파일이 컨트롤러로 작동
#실제 예측, 수명 예측, 보고서 생성 등은 서비스 레이어로 위임

from fastapi import APIRouter
from model.panel_request import PanelRequest
from services.report_service import process_report

router = APIRouter()

@router.post("")
def generate_panel_report(data: PanelRequest):
    return process_report(data)
