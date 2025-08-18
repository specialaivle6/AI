# -*- coding: utf-8 -*-
from typing import List
from ..config import settings
import time

try:
    from openai import OpenAI
    _openai_ok = True
except Exception:
    _openai_ok = False

try:
    from sentence_transformers import SentenceTransformer
    _hf_ok = True
except Exception:
    _hf_ok = False


class Embedder:
    def __init__(self):
        self.mode = settings.EMBEDDING_MODE
        self.client = None
        self.model = None
        self.model_name = None
        self.dim = 1536  # text-embedding-3-small

        if self.mode == "openai":
            if not (_openai_ok and settings.OPENAI_API_KEY):
                print("[embed] OPENAI 키 없음 → dummy 모드")
                self.mode = "dummy"
            else:
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=20.0, max_retries=1)
                self.model_name = settings.OPENAI_EMBED_MODEL
        elif self.mode == "hf":
            if not _hf_ok:
                print("[embed] HF 미설치 → dummy 모드")
                self.mode = "dummy"
            else:
                self.model = SentenceTransformer(settings.HF_EMBED_MODEL)
        else:
            self.mode = "dummy"

    def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        out: List[List[float]] = []
        BATCH = 8
        total = len(texts)
        for i in range(0, total, BATCH):
            chunk = texts[i:i+BATCH]
            for attempt in range(2):
                try:
                    resp = self.client.embeddings.create(model=self.model_name, input=chunk)
                    out.extend([d.embedding for d in resp.data])
                    break
                except Exception as e:
                    print(f"[embed] error: {e!r}")
                    time.sleep(1.2*(attempt+1))
            else:
                out.extend([[0.0]*self.dim for _ in chunk])  # 최종 실패 시 0벡터
        return out

    def embed(self, texts: List[str]) -> List[List[float]]:
        if self.mode == "openai":
            return self._embed_openai(texts)
        if self.mode == "hf" and self.model:
            vs = self.model.encode(texts, normalize_embeddings=True)
            return [v.tolist() for v in vs]
        return [[0.0]*self.dim for _ in texts]
