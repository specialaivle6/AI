# app/api/chat.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services import rag

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatIn(BaseModel):
    message: str

class ChatOut(BaseModel):
    answer: str
    confidence_status: str
    confidence_score: float
    top_distance: float
    log_id: int

@router.get("/health")
def health():
    return {"status": "ok"}

@router.post("/ask", response_model=ChatOut)
def ask(body: ChatIn):
    q = (body.message or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="message is required")
    res = rag.query(q)
    return ChatOut(
        answer=res["answer"],
        confidence_status=res["confidence_status"],
        confidence_score=res["confidence_score"],
        top_distance=res["top_distance"],
        log_id=res["log_id"],
    )
