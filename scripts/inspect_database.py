# scripts/inspect_database.py
"""
지식베이스 및 로그 데이터베이스 현황 조회
사용법: python scripts/inspect_database.py [--detailed]
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.vector.chroma_store import ChromaStore
from app.storage.log_store import _load_all, recent_logs, pending_logs, public_logs
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def inspect_vector_db() -> Dict[str, Any]:
    """벡터 데이터베이스 현황 조회"""
    try:
        store = ChromaStore()

        # 전체 문서 수
        total_count = store.collection.count()

        # 전체 문서 조회 (메타데이터만)
        all_docs = store.collection.get(include=["metadatas", "documents"])

        # 소스별 분류
        source_stats = {}
        category_stats = {}

        for meta in all_docs.get("metadatas", []):
            source = meta.get("source", "unknown")
            category = meta.get("category", "unknown")

            source_stats[source] = source_stats.get(source, 0) + 1
            category_stats[category] = category_stats.get(category, 0) + 1

        return {
            "total_documents": total_count,
            "source_breakdown": source_stats,
            "category_breakdown": category_stats,
            "sample_documents": [
                {
                    "content": doc[:100] + "..." if len(doc) > 100 else doc,
                    "metadata": meta
                }
                for doc, meta in zip(
                    all_docs.get("documents", [])[:3],
                    all_docs.get("metadatas", [])[:3]
                )
            ]
        }

    except Exception as e:
        logger.error(f"벡터DB 조회 실패: {e}")
        return {"error": str(e)}


def inspect_log_db() -> Dict[str, Any]:
    """로그 데이터베이스 현황 조회"""
    try:
        all_logs = _load_all()

        # 전체 통계
        total_count = len(all_logs)

        # 상태별 분류
        status_stats = {}
        confidence_stats = {}

        for log in all_logs:
            # 승인 상태별
            approval_status = log.get("approval_status", "unknown")
            status_stats[approval_status] = status_stats.get(approval_status, 0) + 1

            # 신뢰도 상태별
            confidence_status = log.get("confidence_status", "unknown")
            confidence_stats[confidence_status] = confidence_stats.get(confidence_status, 0) + 1

        # 최근 활동
        recent_count = len([log for log in all_logs
                            if log.get("asked_at", "").startswith(datetime.now().strftime("%Y-%m-%d"))])

        # 대기 중인 항목
        pending_count = len([log for log in all_logs
                             if log.get("approval_status") == "PENDING"])

        return {
            "total_logs": total_count,
            "today_questions": recent_count,
            "pending_approval": pending_count,
            "approval_status_breakdown": status_stats,
            "confidence_status_breakdown": confidence_stats,
            "recent_questions": [
                {
                    "id": log.get("id"),
                    "question": log.get("question", "")[:80] + "...",
                    "status": log.get("approval_status"),
                    "asked_at": log.get("asked_at")
                }
                for log in sorted(all_logs, key=lambda x: x.get("id", 0), reverse=True)[:5]
            ]
        }

    except Exception as e:
        logger.error(f"로그DB 조회 실패: {e}")
        return {"error": str(e)}


def print_summary(data: Dict[str, Any]) -> None:
    """요약 정보 출력"""
    print("=" * 60)
    print("🗂️  지식베이스 & 로그 데이터베이스 현황")
    print("=" * 60)

    # 벡터 DB 현황
    vector_info = data.get("vector_db", {})
    if "error" not in vector_info:
        print(f"\n📚 벡터 지식베이스 (ChromaDB)")
        print(f"   총 문서 수: {vector_info.get('total_documents', 0)}개")

        source_breakdown = vector_info.get("source_breakdown", {})
        if source_breakdown:
            print(f"   소스별 분포:")
            for source, count in source_breakdown.items():
                print(f"     - {source}: {count}개")

        category_breakdown = vector_info.get("category_breakdown", {})
        if category_breakdown:
            print(f"   카테고리별 분포:")
            for category, count in category_breakdown.items():
                print(f"     - {category}: {count}개")
    else:
        print(f"\n❌ 벡터DB 오류: {vector_info['error']}")

    # 로그 DB 현황
    log_info = data.get("log_db", {})
    if "error" not in log_info:
        print(f"\n📝 대화 로그 (JSON)")
        print(f"   총 대화 수: {log_info.get('total_logs', 0)}개")
        print(f"   오늘 질문: {log_info.get('today_questions', 0)}개")
        print(f"   관리자 대기: {log_info.get('pending_approval', 0)}개")

        status_breakdown = log_info.get("approval_status_breakdown", {})
        if status_breakdown:
            print(f"   처리 상태별:")
            for status, count in status_breakdown.items():
                print(f"     - {status}: {count}개")

        confidence_breakdown = log_info.get("confidence_status_breakdown", {})
        if confidence_breakdown:
            print(f"   답변 방식별:")
            for status, count in confidence_breakdown.items():
                print(f"     - {status}: {count}개")
    else:
        print(f"\n❌ 로그DB 오류: {log_info['error']}")


def print_detailed(data: Dict[str, Any]) -> None:
    """상세 정보 출력"""
    print_summary(data)

    # 벡터DB 샘플
    vector_info = data.get("vector_db", {})
    samples = vector_info.get("sample_documents", [])
    if samples:
        print(f"\n📄 벡터DB 문서 샘플:")
        for i, sample in enumerate(samples, 1):
            print(f"   {i}. {sample['content']}")
            print(f"      메타: {sample['metadata']}")
            print()

    # 로그 샘플
    log_info = data.get("log_db", {})
    recent = log_info.get("recent_questions", [])
    if recent:
        print(f"\n💬 최근 질문 샘플:")
        for q in recent:
            print(f"   #{q['id']} ({q['status']}) {q['asked_at']}")
            print(f"   Q: {q['question']}")
            print()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='데이터베이스 현황 조회')
    parser.add_argument('--detailed', action='store_true', help='상세 정보 출력')
    parser.add_argument('--json', action='store_true', help='JSON 형태로 출력')

    args = parser.parse_args()

    try:
        # 데이터 수집
        data = {
            "vector_db": inspect_vector_db(),
            "log_db": inspect_log_db(),
            "timestamp": datetime.now().isoformat()
        }

        if args.json:
            # JSON 출력
            print(json.dumps(data, ensure_ascii=False, indent=2))
        elif args.detailed:
            # 상세 출력
            print_detailed(data)
        else:
            # 요약 출력
            print_summary(data)

    except Exception as e:
        logger.error(f"데이터베이스 조회 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()