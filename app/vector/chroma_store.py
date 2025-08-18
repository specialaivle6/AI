# -*- coding: utf-8 -*-
import os, uuid
from typing import Any, Dict, List, Optional
import chromadb
from app.core.config import settings

class ChromaStore:
    def __init__(self):
        os.makedirs(settings.CHROMA_DIR, exist_ok=True)
        self.client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )

    def add_docs(self, contents: List[str], metadatas: Optional[List[Dict[str, Any]]] = None,
                 embeddings: Optional[List[List[float]]] = None, ids: Optional[List[str]] = None):
        if not contents:
            raise ValueError("contents is empty")
        if embeddings is None or len(embeddings) != len(contents):
            raise ValueError("embeddings length mismatch")
        if metadatas is not None and len(metadatas) != len(contents):
            raise ValueError("metadatas length mismatch")
        if not ids:
            ids = [str(uuid.uuid4()) for _ in contents]
        self.collection.add(
            ids=ids, embeddings=embeddings, documents=contents,
            metadatas=metadatas or [{} for _ in contents],
        )

    def query(self, query_embedding: List[float], k: int = 4):
        res = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["distances", "metadatas", "documents"],
        )
        out = []
        if res and res.get("documents"):
            for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
                out.append({"content": doc, "metadata": meta, "distance": float(dist)})
        return out

    # ★ 승인/직접작성 Q&A 목록
    def list_curated(self, limit: int = 30) -> List[Dict[str, Any]]:
        # where 의 $in 지원이 환경마다 달라 안전하게 두 번 가져와 병합
        def _pull(src):
            try:
                return self.collection.get(where={"source": src}, include=["documents","metadatas","ids"])
            except Exception:
                return {"ids": [], "documents": [], "metadatas": []}
        a = _pull("admin_approved")
        b = _pull("admin_written")
        items = []
        for ids, docs, metas in ((a["ids"], a["documents"], a["metadatas"]),
                                 (b["ids"], b["documents"], b["metadatas"])):
            for i, d, m in zip(ids, docs, metas):
                items.append({"id": i, "content": d, "metadata": m})
        # timestamp 내림차순
        items.sort(key=lambda x: x.get("metadata",{}).get("timestamp",""), reverse=True)
        return items[:limit]
