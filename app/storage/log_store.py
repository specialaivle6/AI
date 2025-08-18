# -*- coding: utf-8 -*-
import json, os, threading
from typing import Any, Dict, List, Optional
from app.core.config import settings

_LOCK = threading.Lock()

def _load_all() -> List[Dict[str, Any]]:
    if not os.path.exists(settings.LOG_FILE):
        return []
    try:
        with open(settings.LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _save_all(items: List[Dict[str, Any]]):
    os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)
    with open(settings.LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def _next_id(items: List[Dict]) -> int:
    return (max([it.get("id", 0) for it in items]) + 1) if items else 1

def insert_log(question: str, confidence_status: str, confidence_score: float,
               top_distance: float, draft_answer: Optional[str], retrieved: List[Dict[str, Any]],
               asked_at: str, answered_at: Optional[str]) -> int:
    with _LOCK:
        items = _load_all()
        lid = _next_id(items)
        items.append({
            "id": lid,
            "question": question,
            "answer": None,
            "draft_answer": draft_answer,
            "approval_status": "PENDING" if confidence_status == "ESCALATE_TO_BOARD" else "N/A",
            "confidence_status": confidence_status,
            "confidence_score": float(confidence_score),
            "top_distance": float(top_distance),
            "retrieved": retrieved or [],
            "asked_at": asked_at,
            "answered_at": answered_at
        })
        _save_all(items)
        return lid

def set_draft(log_id: int, draft_answer: Optional[str]):
    with _LOCK:
        items = _load_all()
        for it in items:
            if it["id"] == log_id:
                it["draft_answer"] = draft_answer
                break
        _save_all(items)

def update_answer(log_id: int, answer: str, answered_at: str):
    with _LOCK:
        items = _load_all()
        for it in items:
            if it["id"] == log_id:
                it["answer"] = answer
                it["answered_at"] = answered_at
                break
        _save_all(items)

def set_approval(log_id: int, status: str):
    with _LOCK:
        items = _load_all()
        for it in items:
            if it["id"] == log_id:
                it["approval_status"] = status
                break
        _save_all(items)

def get_log(log_id: int) -> Optional[Dict[str, Any]]:
    items = _load_all()
    for it in items:
        if it["id"] == log_id:
            return it
    return None

def recent_logs(n: int = 50) -> List[Dict[str, Any]]:
    items = _load_all()
    items.sort(key=lambda x: x.get("id", 0), reverse=True)
    return items[:n]

def pending_logs(n: int = 50) -> List[Dict[str, Any]]:
    items = _load_all()
    out = [it for it in items if it.get("approval_status") == "PENDING"]
    out.sort(key=lambda x: x.get("id", 0), reverse=True)
    return out[:n]

# ★ 공개 노출 전용: 자동응답(ANSWERABLE) + 승인된 것만
def public_logs(n: int = 50) -> List[Dict[str, Any]]:
    items = _load_all()
    out = []
    for it in items:
        if it.get("approval_status") == "PENDING":
            continue
        # ANSWERABLE 이거나, 승인/직접작성 등으로 최종 답변이 존재하면 공개
        if it.get("confidence_status") == "ANSWERABLE" or (it.get("answer") and it.get("approval_status") in ("APPROVED","REJECTED","N/A")):
            out.append(it)
    out.sort(key=lambda x: x.get("id", 0), reverse=True)
    return out[:n]
