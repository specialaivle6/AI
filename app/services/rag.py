# -*- coding: utf-8 -*-
from typing import Any, Dict, List
from datetime import datetime
from ..embeddings.embedding import Embedder
from ..vector.chroma_store import ChromaStore
from .llm import ask_llm
from ..config import settings
from ..storage.log_store import insert_log, update_answer, set_draft

_embedder: Embedder = None
_store: ChromaStore = None

def _ensure():
    global _embedder, _store
    if _embedder is None:
        _embedder = Embedder()
    if _store is None:
        _store = ChromaStore()

def _score(dist: float) -> float:
    return max(0.0, 1.0 - float(dist))

def _contains_domain_terms(question: str, retrieved: List[Dict]) -> bool:
    keys = settings.ALLOWED_KEYWORDS
    pool = (question or "") + " " + " ".join([d.get("content","") for d in (retrieved or [])])
    return any(k in pool for k in keys)

def warmup():
    try:
        _ensure()
        _embedder.embed(["warmup"])
        print("[warmup] ok")
    except Exception as e:
        print("[warmup] skip:", e)

def query(question: str) -> Dict[str, Any]:
    _ensure()
    asked_at = datetime.now().isoformat()

    retrieved: List[Dict[str, Any]] = []
    top_dist, conf = 1.0, 0.0
    status = "ESCALATE_TO_BOARD"
    answer = ""
    log_id = None
    answered_at = None

    try:
        qv = _embedder.embed([question])[0]
        hits = _store.query(qv, k=4) or []
        retrieved = hits

        if hits:
            top_dist = float(hits[0].get("distance", 1.0))
            conf = _score(top_dist)

        domain_ok = _contains_domain_terms(question, retrieved)
        has_ctx = bool(hits)
        is_answerable = (has_ctx
                         and (top_dist <= settings.MAX_DISTANCE_TO_ANSWER)
                         and (conf >= settings.MIN_CONFIDENCE_TO_ANSWER)
                         and domain_ok)
        status = "ANSWERABLE" if is_answerable else "ESCALATE_TO_BOARD"

        # 로그 먼저 생성 (draft 자리도 마련)
        log_id = insert_log(question, status, conf, top_dist, None, retrieved, asked_at, None)

        if status == "ANSWERABLE":
            answer = ask_llm(question, retrieved, draft=False)
        else:
            # 여기서 '초안' 생성 → draft 저장 → 응답은 이관 문구
            try:
                draft = ask_llm(question, retrieved, draft=True)
            except Exception:
                draft = None
            set_draft(log_id, draft)
            answer = "관련 문서가 부족하거나 도메인과 무관하여 게시판 이관이 필요합니다. 관리자 답변 후 지식베이스에 반영됩니다."

        answered_at = datetime.now().isoformat()
        update_answer(log_id, answer, answered_at)

        return {
            "answer": answer,
            "confidence_status": status,
            "confidence_score": conf,
            "top_distance": top_dist,
            "retrieved": retrieved,
            "asked_at": asked_at,
            "answered_at": answered_at,
            "log_id": log_id or 0,
        }

    except Exception as e:
        print("[rag] fatal:", repr(e))
        if log_id:
            answered_at = datetime.now().isoformat()
            update_answer(log_id, "(시스템 오류) 관리자 확인 필요", answered_at)
        return {
            "answer": "(시스템 오류) 잠시 후 다시 시도해주세요.",
            "confidence_status": "ESCALATE_TO_BOARD",
            "confidence_score": 0.0,
            "top_distance": 1.0,
            "retrieved": [],
            "asked_at": asked_at,
            "answered_at": datetime.now().isoformat(),
            "log_id": log_id or 0,
        }
