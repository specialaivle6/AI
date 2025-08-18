# -*- coding: utf-8 -*-
from typing import Dict, List, Optional
from ..config import settings

try:
    from openai import OpenAI
    _openai_ok = True
except Exception:
    _openai_ok = False

SYSTEM_PROMPT = (
    "당신은 태양광 패널 성능/수명 예측, 실제 성능 비교, 폐패널 수거·재활용, "
    "EPR 보고, 오염/파손 진단 전문가입니다. 제공된 컨텍스트만 바탕으로 "
    "한국어로 간결하고 정확히 답하세요. 근거 부족 시 이관 필요성을 명시하세요."
)

def _ctx(retrieved: List[Dict]) -> str:
    if not retrieved: return "(컨텍스트 없음)"
    parts=[]
    for i, d in enumerate(retrieved, 1):
        src = d.get("metadata", {}).get("source", "unknown")
        parts.append(f"[{i}] ({src})\n{d['content']}")
    return "\n\n".join(parts)

def ask_llm(question: str, retrieved: List[Dict], draft: bool=False) -> str:
    context = _ctx(retrieved)
    instruct = (
        "- 컨텍스트 내 사실만 사용\n"
        "- 5문장 이내, 필요 시 목록 허용\n"
        "- PR, MAPE, 수명 추정 지표 설명 가능\n"
    )
    if draft:
        instruct = (
            "- 관리자 승인용 '초안'을 생성. 확신 없는 부분은 작성하지 않음.\n"
            "- 6문장 이내, 핵심만"
        )
    prompt = f"[컨텍스트]\n{context}\n\n[질문]\n{question}\n\n[지시]\n{instruct}"

    if _openai_ok and settings.OPENAI_API_KEY:
        client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=20.0, max_retries=1)
        r = client.chat.completions.create(
            model=settings.OPENAI_CHAT_MODEL,
            temperature=settings.LLM_TEMPERATURE if not draft else 0.2,
            messages=[
                {"role":"system","content": SYSTEM_PROMPT},
                {"role":"user","content": prompt},
            ],
        )
        return r.choices[0].message.content.strip()

    # Fallback(미연결)
    if retrieved:
        return "(LLM 미연결) 컨텍스트 기반 요약: " + retrieved[0]["content"][:400]
    return "(LLM 미연결) 컨텍스트가 부족합니다. 관리자 확인 필요."
