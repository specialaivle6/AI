# -*- coding: utf-8 -*-
"""
CSV 형식(헤더):
question,answer,category,source,tags
"""
import csv, os
from datetime import datetime

from ..app.embeddings.embedding import Embedder
from ..app.vector.chroma_store import ChromaStore

def main(csv_path: str):
    print("📂 CSV 로드:", csv_path)
    embedder = Embedder()
    store = ChromaStore()

    docs, metas = [], []
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        if rd.fieldnames:
            rd.fieldnames = [(name or "").strip().lstrip("\ufeff") for name in rd.fieldnames]
        for row in rd:
            q = (row.get("question") or "").strip()
            a = (row.get("answer") or "").strip()
            if not q or not a:
                continue
            docs.append(f"Q: {q}\nA: {a}")
            metas.append({
                "source": row.get("source","faq"),
                "category": row.get("category","기타"),
                "timestamp": datetime.now().isoformat(),
                "question_id": f"seed-{abs(hash(q))}",
                "answer_id": f"seed-{abs(hash(a))}",
                "lang": "ko",
                "tags": row.get("tags","")
            })

    print(f"🧾 문서 개수: {len(docs)}")
    if not docs:
        raise SystemExit("CSV에 유효한 question/answer 행이 없습니다.")

    print("🧠 임베딩 시작...")
    vecs = embedder.embed(docs)
    print("💾 DB 적재...")
    ids = [f"seed-{i}" for i in range(len(docs))]
    store.add_docs(docs, metas, vecs, ids=ids)
    print(f"🎉 완료: Loaded {len(docs)} docs.")

if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(__file__))
    csv_path = os.path.join(base, "data", "initial", "faq.csv")
    if not os.path.exists(csv_path):
        raise SystemExit(f"CSV not found: {csv_path}")
    main(csv_path)
