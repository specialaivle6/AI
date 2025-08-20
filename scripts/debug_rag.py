# scripts/debug_rag.py
"""
RAG 시스템 디버깅 도구 - 왜 답변이 안 되는지 단계별 분석
사용법: python scripts/debug_rag.py "태양광 패널 성능은 어떻게 측정하나요?"
"""

import sys
from pathlib import Path
from typing import Dict, List, Any

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.embeddings.embedding import Embedder
from app.vector.chroma_store import ChromaStore
from app.services.rag import _contains_domain_terms, _score
from app.services.llm import ask_llm
from app.core.config import settings


def debug_rag_step_by_step(question: str) -> Dict[str, Any]:
    """RAG 프로세스를 단계별로 디버깅"""

    print(f"🔍 질문: '{question}'")
    print("=" * 60)

    debug_info = {
        "question": question,
        "steps": {}
    }

    try:
        # 1. 임베딩 생성
        print("1️⃣ 임베딩 생성...")
        embedder = Embedder()
        question_embedding = embedder.embed([question])[0]
        print(f"   ✅ 임베딩 차원: {len(question_embedding)}")
        print(f"   ✅ 임베딩 샘플: {question_embedding[:5]}...")
        debug_info["steps"]["embedding"] = {
            "success": True,
            "dimension": len(question_embedding)
        }

    except Exception as e:
        print(f"   ❌ 임베딩 실패: {e}")
        debug_info["steps"]["embedding"] = {"success": False, "error": str(e)}
        return debug_info

    try:
        # 2. 벡터 검색
        print("\n2️⃣ 벡터 검색...")
        store = ChromaStore()
        hits = store.query(question_embedding, k=4)

        print(f"   ✅ 검색 결과: {len(hits)}개")
        if hits:
            print(f"   ✅ 최고 유사도: {hits[0]['distance']:.3f}")
            print(f"   ✅ 최저 유사도: {hits[-1]['distance']:.3f}")
            for i, hit in enumerate(hits):
                content_preview = hit['content'][:80] + "..."
                print(f"      {i + 1}. 거리:{hit['distance']:.3f} - {content_preview}")
        else:
            print("   ⚠️ 검색 결과 없음")

        debug_info["steps"]["search"] = {
            "success": True,
            "results_count": len(hits),
            "top_distance": hits[0]['distance'] if hits else None,
            "results": [{"distance": h['distance'], "content": h['content'][:100]} for h in hits[:3]]
        }

    except Exception as e:
        print(f"   ❌ 검색 실패: {e}")
        debug_info["steps"]["search"] = {"success": False, "error": str(e)}
        return debug_info

    # 3. 신뢰도 계산
    print("\n3️⃣ 신뢰도 계산...")
    if hits:
        top_dist = float(hits[0]['distance'])
        confidence_score = _score(top_dist)
        print(f"   ✅ 최고 거리: {top_dist:.3f}")
        print(f"   ✅ 신뢰도 점수: {confidence_score:.3f}")
        print(f"   📏 거리 임계값: {settings.MAX_DISTANCE_TO_ANSWER}")
        print(f"   📏 신뢰도 임계값: {settings.MIN_CONFIDENCE_TO_ANSWER}")

        dist_pass = top_dist <= settings.MAX_DISTANCE_TO_ANSWER
        conf_pass = confidence_score >= settings.MIN_CONFIDENCE_TO_ANSWER

        print(
            f"   {'✅' if dist_pass else '❌'} 거리 검사: {top_dist:.3f} <= {settings.MAX_DISTANCE_TO_ANSWER} = {dist_pass}")
        print(
            f"   {'✅' if conf_pass else '❌'} 신뢰도 검사: {confidence_score:.3f} >= {settings.MIN_CONFIDENCE_TO_ANSWER} = {conf_pass}")
    else:
        top_dist = 1.0
        confidence_score = 0.0
        dist_pass = conf_pass = False
        print("   ❌ 검색 결과가 없어서 신뢰도 계산 불가")

    debug_info["steps"]["confidence"] = {
        "top_distance": top_dist,
        "confidence_score": confidence_score,
        "distance_threshold": settings.MAX_DISTANCE_TO_ANSWER,
        "confidence_threshold": settings.MIN_CONFIDENCE_TO_ANSWER,
        "distance_pass": dist_pass,
        "confidence_pass": conf_pass
    }

    # 4. 도메인 키워드 검사
    print("\n4️⃣ 도메인 키워드 검사...")
    domain_ok = _contains_domain_terms(question, hits)
    print(f"   {'✅' if domain_ok else '❌'} 도메인 검사: {domain_ok}")
    print(f"   📝 허용 키워드: {settings.ALLOWED_KEYWORDS}")

    # 질문에서 발견된 키워드
    found_keywords = [kw for kw in settings.ALLOWED_KEYWORDS if kw in question]
    print(f"   🔍 질문에서 발견된 키워드: {found_keywords}")

    # 검색 결과에서 발견된 키워드
    retrieved_text = " ".join([h.get("content", "") for h in hits])
    found_in_results = [kw for kw in settings.ALLOWED_KEYWORDS if kw in retrieved_text]
    print(f"   🔍 검색 결과에서 발견된 키워드: {found_in_results[:5]}...")

    debug_info["steps"]["domain_check"] = {
        "domain_ok": domain_ok,
        "keywords_in_question": found_keywords,
        "keywords_in_results": found_in_results[:10]
    }

    # 5. 최종 판정
    print("\n5️⃣ 최종 판정...")
    has_ctx = bool(hits)
    is_answerable = (has_ctx and dist_pass and conf_pass and domain_ok)

    print(f"   {'✅' if has_ctx else '❌'} 컨텍스트 존재: {has_ctx}")
    print(f"   {'✅' if is_answerable else '❌'} 답변 가능: {is_answerable}")

    if is_answerable:
        status = "ANSWERABLE"
        print(f"   🎉 결과: 자동 답변 가능!")
    else:
        status = "ESCALATE_TO_BOARD"
        print(f"   ⚠️ 결과: 관리자 이관 필요")

        # 실패 원인 분석
        failure_reasons = []
        if not has_ctx:
            failure_reasons.append("검색 결과 없음")
        if not dist_pass:
            failure_reasons.append(f"거리 임계값 초과 ({top_dist:.3f} > {settings.MAX_DISTANCE_TO_ANSWER})")
        if not conf_pass:
            failure_reasons.append(f"신뢰도 부족 ({confidence_score:.3f} < {settings.MIN_CONFIDENCE_TO_ANSWER})")
        if not domain_ok:
            failure_reasons.append("도메인 키워드 부족")

        print(f"   🔍 실패 원인: {', '.join(failure_reasons)}")

    debug_info["steps"]["final_decision"] = {
        "has_context": has_ctx,
        "is_answerable": is_answerable,
        "status": status,
        "failure_reasons": failure_reasons if not is_answerable else []
    }

    # 6. LLM 답변 테스트 (answerable인 경우만)
    if is_answerable:
        print("\n6️⃣ LLM 답변 생성...")
        try:
            answer = ask_llm(question, hits, draft=False)
            print(f"   ✅ 답변 생성 성공:")
            print(f"   📝 {answer[:200]}...")
            debug_info["steps"]["llm_answer"] = {
                "success": True,
                "answer": answer
            }
        except Exception as e:
            print(f"   ❌ LLM 답변 실패: {e}")
            debug_info["steps"]["llm_answer"] = {
                "success": False,
                "error": str(e)
            }

    return debug_info


def suggest_fixes(debug_info: Dict[str, Any]) -> None:
    """문제 해결 방안 제안"""
    print("\n" + "=" * 60)
    print("🔧 문제 해결 방안")
    print("=" * 60)

    steps = debug_info["steps"]
    final = steps.get("final_decision", {})

    if final.get("is_answerable"):
        print("✅ 시스템이 정상 작동하고 있습니다!")
        return

    failure_reasons = final.get("failure_reasons", [])

    for reason in failure_reasons:
        if "거리 임계값 초과" in reason:
            print("🎯 거리 임계값 조정:")
            print("   - config.py에서 MAX_DISTANCE_TO_ANSWER를 0.65 → 0.75로 증가")
            print("   - 또는 환경변수: MAX_DISTANCE_TO_ANSWER=0.75")

        elif "신뢰도 부족" in reason:
            print("🎯 신뢰도 임계값 조정:")
            print("   - config.py에서 MIN_CONFIDENCE_TO_ANSWER를 0.35 → 0.25로 감소")
            print("   - 또는 환경변수: MIN_CONFIDENCE_TO_ANSWER=0.25")

        elif "도메인 키워드 부족" in reason:
            print("🎯 도메인 키워드 확장:")
            print("   - config.py의 ALLOWED_KEYWORDS에 누락된 키워드 추가")
            question = debug_info["question"]
            print(f"   - 질문 '{question}'에서 중요한 단어들을 키워드에 추가 검토")

        elif "검색 결과 없음" in reason:
            print("🎯 지식베이스 확장:")
            print("   - 더 많은 FAQ 데이터 추가 필요")
            print("   - 임베딩 모델 품질 검토 필요")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='RAG 시스템 디버깅')
    parser.add_argument('question', help='테스트할 질문')
    parser.add_argument('--json', action='store_true', help='JSON 형태로 출력')

    args = parser.parse_args()

    try:
        debug_info = debug_rag_step_by_step(args.question)

        if not args.json:
            suggest_fixes(debug_info)
        else:
            import json
            print(json.dumps(debug_info, ensure_ascii=False, indent=2))

    except Exception as e:
        print(f"❌ 디버깅 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()