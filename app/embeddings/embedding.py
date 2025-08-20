# app/embeddings/embedding.py (개선된 버전)
# -*- coding: utf-8 -*-
from typing import List
from app.core.config import settings
import time
import hashlib
import re

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
                print("[embed] OPENAI 키 없음 → HF 모드로 fallback 시도")
                self.mode = "hf"  # dummy가 아닌 HF로 fallback
            else:
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=20.0, max_retries=1)
                self.model_name = settings.OPENAI_EMBED_MODEL

        if self.mode == "hf":
            if not _hf_ok:
                print("[embed] HF 미설치 → 의미 기반 fallback 모드")
                self.mode = "semantic_fallback"
            else:
                try:
                    self.model = SentenceTransformer(settings.HF_EMBED_MODEL)
                    print("[embed] HF 모델 로드 성공")
                except Exception as e:
                    print(f"[embed] HF 모델 로드 실패 → 의미 기반 fallback: {e}")
                    self.mode = "semantic_fallback"

        if self.mode not in ["openai", "hf"]:
            self.mode = "semantic_fallback"

    def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        out: List[List[float]] = []
        BATCH = 8
        total = len(texts)
        for i in range(0, total, BATCH):
            chunk = texts[i:i + BATCH]
            for attempt in range(2):
                try:
                    resp = self.client.embeddings.create(model=self.model_name, input=chunk)
                    out.extend([d.embedding for d in resp.data])
                    break
                except Exception as e:
                    print(f"[embed] OpenAI error (attempt {attempt + 1}): {e!r}")
                    time.sleep(1.2 * (attempt + 1))
            else:
                # OpenAI 실패 시 HF로 즉시 fallback
                print(f"[embed] OpenAI 완전 실패 → HF fallback for batch {i // BATCH + 1}")
                return self._embed_hf_fallback(texts)
        return out

    def _embed_hf_fallback(self, texts: List[str]) -> List[List[float]]:
        """OpenAI 실패 시 HF로 fallback"""
        if _hf_ok:
            try:
                if not self.model:
                    self.model = SentenceTransformer(settings.HF_EMBED_MODEL)
                vs = self.model.encode(texts, normalize_embeddings=True)
                return [v.tolist() for v in vs]
            except Exception as e:
                print(f"[embed] HF fallback도 실패: {e}")

        return self._embed_semantic_fallback(texts)

    def _embed_semantic_fallback(self, texts: List[str]) -> List[List[float]]:
        """의미 기반 간단한 임베딩 (TF-IDF 스타일)"""
        print("[embed] 의미 기반 fallback 모드 사용")

        # 모든 텍스트에서 키워드 추출
        all_keywords = set()
        for text in texts:
            keywords = self._extract_keywords(text)
            all_keywords.update(keywords)

        keyword_list = sorted(list(all_keywords))
        vocab_size = max(len(keyword_list), 100)  # 최소 100차원 보장

        embeddings = []
        for text in texts:
            keywords = self._extract_keywords(text)

            # 키워드 기반 벡터 생성
            vector = [0.0] * vocab_size

            for i, vocab_word in enumerate(keyword_list):
                if i >= vocab_size:
                    break
                if vocab_word in keywords:
                    # TF-IDF 스타일 가중치
                    tf = keywords.count(vocab_word)
                    vector[i] = tf * 0.1  # 간단한 가중치

            # 텍스트 길이 기반 추가 피처
            if len(vector) > 10:
                vector[vocab_size - 10] = len(text) / 1000.0  # 텍스트 길이
                vector[vocab_size - 9] = text.count('?') * 0.5  # 질문 여부
                vector[vocab_size - 8] = text.count('패널') * 0.3  # 도메인 키워드
                vector[vocab_size - 7] = text.count('태양광') * 0.3
                vector[vocab_size - 6] = text.count('성능') * 0.2

            # 정규화
            norm = sum(x * x for x in vector) ** 0.5
            if norm > 0:
                vector = [x / norm for x in vector]

            # 차원을 1536으로 맞춤 (OpenAI 호환)
            if len(vector) < self.dim:
                vector.extend([0.0] * (self.dim - len(vector)))
            else:
                vector = vector[:self.dim]

            embeddings.append(vector)

        return embeddings

    def _extract_keywords(self, text: str) -> List[str]:
        """간단한 키워드 추출"""
        # 한글, 영문, 숫자만 추출
        words = re.findall(r'[가-힣a-zA-Z0-9]+', text.lower())

        # 너무 짧은 단어 제거
        keywords = [w for w in words if len(w) >= 2]

        # 도메인 특화 키워드 가중치
        domain_keywords = ['태양광', '패널', '성능', '예측', '수명', '오염', '파손', '교체', '수리']
        result = []

        for word in keywords:
            result.append(word)
            # 도메인 키워드는 중복 추가 (가중치 효과)
            if word in domain_keywords:
                result.append(word)

        return result

    def embed(self, texts: List[str]) -> List[List[float]]:
        if self.mode == "openai":
            return self._embed_openai(texts)
        elif self.mode == "hf" and self.model:
            vs = self.model.encode(texts, normalize_embeddings=True)
            return [v.tolist() for v in vs]
        else:
            return self._embed_semantic_fallback(texts)