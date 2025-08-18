# -*- coding: utf-8 -*-
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from .config import settings
from .models.schemas import (
    HealthResponse, ChatQuery, ChatAnswer,
    SummarizeInput, SummarizeOutput,
    FeedbackItem, FeedbackResponse, RetrievedDoc,
    PendingList, ApproveRequest, ApproveResponse,
    RejectRequest, RejectResponse
)
from .services import rag
from .services.feedback import add_feedback_qa
from .storage.log_store import recent_logs, pending_logs, get_log, set_approval, update_answer, public_logs
from .vector.chroma_store import ChromaStore

app = FastAPI(title=settings.APP_NAME, version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

def _admin_guard(token: str | None):
    if not token or token != settings.ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")

@app.on_event("startup")
def _startup():
    try:
        rag.warmup()
    except Exception as e:
        print("warmup failed:", e)

@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", version=settings.VERSION)

@app.post("/api/v1/chat/query", response_model=ChatAnswer)
def chat_query(payload: ChatQuery):
    if not payload.question or not payload.question.strip():
        raise HTTPException(status_code=400, detail="question은 필수입니다.")
    result = rag.query(payload.question.strip())
    retrieved = [RetrievedDoc(**d) for d in result.get("retrieved", [])]
    return ChatAnswer(
        answer=result["answer"],
        confidence_status=result["confidence_status"],
        confidence_score=result["confidence_score"],
        top_distance=result["top_distance"],
        retrieved=retrieved,
        asked_at=result["asked_at"],
        answered_at=result["answered_at"],
        log_id=result["log_id"]
    )

# 공개 로그(답변 완료/승인된 것만)
@app.get("/api/v1/logs/public")
def logs_public(limit: int = 50):
    return {"items": public_logs(limit)}

# 승인된 Q&A(벡터DB 기준) 목록
@app.get("/api/v1/qa/approved")
def qa_approved(limit: int = 30):
    store = ChromaStore()
    items = store.list_curated(limit=limit)
    # "Q: ...\nA: ..." 파싱
    out = []
    for it in items:
        q, a = "", ""
        text = it["content"] or ""
        if "\nA:" in text:
            try:
                q = text.split("\nA:")[0].replace("Q:","").strip()
                a = text.split("\nA:")[1].strip()
            except Exception:
                q = text[:200]
        else:
            q = text[:200]
        out.append({
            "id": it["id"],
            "question": q,
            "answer": a,
            "meta": it.get("metadata", {})
        })
    return {"items": out}

# -------------------- 관리자 영역 (토큰 필요) --------------------
@app.get("/api/v1/moderation/pending", response_model=PendingList)
def moderation_pending(x_admin_token: str | None = Header(None, alias="X-Admin-Token")):
    _admin_guard(x_admin_token)
    items = pending_logs(100)
    out = []
    for it in items:
        out.append({
            "id": it["id"],
            "question": it["question"],
            "draft_answer": it.get("draft_answer"),
            "approval_status": it.get("approval_status", "PENDING"),
            "asked_at": it.get("asked_at"),
            "answered_at": it.get("answered_at"),
            "confidence_status": it.get("confidence_status"),
            "confidence_score": it.get("confidence_score"),
            "top_distance": it.get("top_distance"),
        })
    return PendingList(items=out)

@app.post("/api/v1/moderation/approve", response_model=ApproveResponse)
def moderation_approve(req: ApproveRequest, x_admin_token: str | None = Header(None, alias="X-Admin-Token")):
    _admin_guard(x_admin_token)
    log = get_log(req.log_id)
    if not log:
        raise HTTPException(status_code=404, detail="log_id not found")
    final_answer = (req.answer or log.get("draft_answer") or "").strip()
    if not final_answer:
        raise HTTPException(status_code=400, detail="승인할 답변이 없습니다.")
    update_answer(req.log_id, final_answer, datetime.now().isoformat())
    set_approval(req.log_id, "APPROVED")
    add_feedback_qa(log["question"], final_answer, req.category, "admin_approved", req.tags)
    return ApproveResponse(approved=True, log_id=req.log_id)

@app.post("/api/v1/moderation/reject", response_model=RejectResponse)
def moderation_reject(req: RejectRequest, x_admin_token: str | None = Header(None, alias="X-Admin-Token")):
    _admin_guard(x_admin_token)
    log = get_log(req.log_id)
    if not log:
        raise HTTPException(status_code=404, detail="log_id not found")
    if req.answer and req.answer.strip():
        final_answer = req.answer.strip()
        update_answer(req.log_id, final_answer, datetime.now().isoformat())
        add_feedback_qa(log["question"], final_answer, req.category, "admin_written", req.tags)
    set_approval(req.log_id, "REJECTED")
    return RejectResponse(rejected=True, log_id=req.log_id)

# -------------------- 요약/피드백(기존) --------------------
@app.post("/api/v1/summarize", response_model=SummarizeOutput)
def summarize(body: SummarizeInput):
    try:
        from openai import OpenAI
        if not settings.OPENAI_API_KEY:
            raise RuntimeError
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        conv_text = "\n".join([f"{m['role']}: {m['content']}" for m in body.conversation])
        prompt = f"""다음 대화를 게시판용으로 요약하세요.
- 한국어 제목 1줄
- 본문 400자 이내

[대화]
{conv_text}

[출력]
제목: ...
본문: ...
"""
        resp = client.chat.completions.create(
            model=settings.OPENAI_CHAT_MODEL,
            temperature=0.2,
            messages=[{"role":"system","content":"너는 요약 전문가다."},{"role":"user","content":prompt}]
        )
        txt = resp.choices[0].message.content.strip()
        title = "요약"; body_text = txt
        if "제목:" in txt:
            parts = txt.split("본문:")
            title = parts[0].replace("제목:","").strip()
            body_text = (parts[1] if len(parts)>1 else "").strip()
    except Exception:
        title = "요약(LLM 미연결)"
        body_text = "OpenAI API 연결 시 요약 고도화가 활성화됩니다."
    return SummarizeOutput(title=title, body=body_text, created_at=datetime.now().isoformat())

@app.post("/api/v1/feedback", response_model=FeedbackResponse)
def feedback(item: FeedbackItem):
    add_feedback_qa(item.question, item.answer, item.category, item.source, item.tags)
    return FeedbackResponse(stored=True, added_to_vector=item.add_to_vector, question_id="gen-q", answer_id="gen-a")

# -------------------- 페이지 라우팅 --------------------
@app.get("/ui", response_class=HTMLResponse)
def ui():
    path = os.path.join(os.path.dirname(__file__), "webui", "templates", "index.html")
    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.get("/admin", response_class=HTMLResponse)
def admin():
    path = os.path.join(os.path.dirname(__file__), "webui", "templates", "admin.html")
    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)
