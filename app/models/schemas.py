# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    status: str
    version: str

class RetrievedDoc(BaseModel):
    content: str
    metadata: Dict[str, Any] = {}
    distance: float

class ChatQuery(BaseModel):
    question: str = Field(..., description="사용자 질문")

class ChatAnswer(BaseModel):
    answer: str
    confidence_status: str
    confidence_score: float
    top_distance: float
    retrieved: List[RetrievedDoc] = []
    asked_at: str
    answered_at: Optional[str] = None
    log_id: int

# 요약
class SummarizeInput(BaseModel):
    conversation: List[Dict[str, str]]  # [{role, content}...]

class SummarizeOutput(BaseModel):
    title: str
    body: str
    created_at: str

# 피드백(지식 반영)
class FeedbackItem(BaseModel):
    question: str
    answer: str
    category: str = "기타"
    source: str = "admin"
    tags: List[str] = []
    add_to_vector: bool = True

class FeedbackResponse(BaseModel):
    stored: bool
    added_to_vector: bool
    question_id: str
    answer_id: str

# 모더레이션(승인/거절)
class PendingItem(BaseModel):
    id: int
    question: str
    draft_answer: Optional[str] = None
    approval_status: str  # PENDING/APPROVED/REJECTED
    asked_at: str
    answered_at: Optional[str] = None
    confidence_status: str
    confidence_score: float
    top_distance: float

class PendingList(BaseModel):
    items: List[PendingItem] = []

class ApproveRequest(BaseModel):
    log_id: int
    answer: Optional[str] = None
    category: str = "기타"
    tags: List[str] = []

class ApproveResponse(BaseModel):
    approved: bool
    log_id: int

class RejectRequest(BaseModel):
    log_id: int
    answer: Optional[str] = None
    category: str = "기타"
    tags: List[str] = []

class RejectResponse(BaseModel):
    rejected: bool
    log_id: int
