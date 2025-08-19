# -*- coding: utf-8 -*-
from typing import List
from datetime import datetime
from ..embeddings.embedding import Embedder
from ..vector.chroma_store import ChromaStore

def add_feedback_qa(question: str, answer: str, category: str, source: str, tags: List[str]):
    """관리자 확정 Q&A를 벡터DB에 삽입"""
    store = ChromaStore()
    embedder = Embedder()
    doc = f"Q: {question}\nA: {answer}"
    meta = {
        "source": source or "admin",
        "category": category or "기타",
        "tags": ";".join(tags or []),
        "timestamp": datetime.now().isoformat(),  # ★ 정렬용
    }
    vec = embedder.embed([doc])[0]
    store.add_docs([doc], [meta], [vec], ids=None)
