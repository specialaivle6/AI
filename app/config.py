# -*- coding: utf-8 -*-
import os

class Settings:
    APP_NAME: str = "SolarMate RAG API"
    VERSION: str = "1.2.0"

    CHROMA_DIR: str = os.getenv("CHROMA_DIR", "./chatbot/db")
    CHROMA_COLLECTION: str = os.getenv("CHROMA_COLLECTION", "solar_qa")

    EMBEDDING_MODE: str = os.getenv("EMBEDDING_MODE", "openai")
    HF_EMBED_MODEL: str = os.getenv("HF_EMBED_MODEL", "jhgan/ko-sroberta-multitask")
    OPENAI_EMBED_MODEL: str = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
    OPENAI_CHAT_MODEL: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))

    # 게이트(원하면 환경변수로 조정)
    MAX_DISTANCE_TO_ANSWER: float = float(os.getenv("MAX_DISTANCE_TO_ANSWER", "0.65"))
    MIN_CONFIDENCE_TO_ANSWER: float = float(os.getenv("MIN_CONFIDENCE_TO_ANSWER", "0.35"))

    ALLOWED_KEYWORDS = [
        "태양광","패널","폐패널","EPR","재활용","수거","인버터",
        "모듈","설치","교체","철거","발전소","태양열","오염","파손","성능","예측","수명"
    ]

    LOG_FILE: str = os.getenv("LOG_FILE", "./chatbot/db/logs.json")

    # ★ 관리자 페이지/엔드포인트 보호용 토큰 (HTTP 헤더 X-Admin-Token)
    ADMIN_TOKEN: str = os.getenv("ADMIN_TOKEN", "admin123")

settings = Settings()
