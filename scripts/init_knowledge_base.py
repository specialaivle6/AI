# scripts/init_knowledge_base.py
"""
CSV 파일로부터 지식베이스 초기화
사용법: python scripts/init_knowledge_base.py --csv-file data/faq.csv
"""

import os
import sys
import pandas as pd
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.embeddings.embedding import Embedder
from app.vector.chroma_store import ChromaStore
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def load_csv_faq(csv_path: str) -> List[Dict[str, Any]]:
    """
    CSV 파일에서 FAQ 데이터 로드

    Args:
        csv_path: CSV 파일 경로

    Returns:
        List[Dict]: 파싱된 FAQ 데이터
    """
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')

        # 필수 컬럼 확인
        required_cols = ['question', 'answer']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"필수 컬럼 누락: {missing_cols}")

        # 데이터 정제 및 변환
        faq_data = []
        for idx, row in df.iterrows():
            question = str(row['question']).strip()
            answer = str(row['answer']).strip()
            keywords = str(row.get('keywords', '')).strip()

            # 빈 데이터 스킵
            if not question or not answer or question == 'nan' or answer == 'nan':
                logger.warning(f"행 {idx + 2}: 빈 질문/답변 스킵")
                continue

            # 키워드 파싱 (세미콜론 구분)
            tag_list = []
            if keywords and keywords != 'nan':
                tag_list = [kw.strip() for kw in keywords.split(';') if kw.strip()]

            faq_data.append({
                'question': question,
                'answer': answer,
                'keywords': tag_list,
                'source': 'csv_init',
                'category': '기본FAQ'
            })

        logger.info(f"CSV에서 {len(faq_data)}개 FAQ 로드 완료")
        return faq_data

    except Exception as e:
        logger.error(f"CSV 로드 실패: {e}")
        raise


def embed_and_store_faqs(faq_data: List[Dict[str, Any]],
                         embedder: Embedder,
                         store: ChromaStore,
                         batch_size: int = 10) -> None:
    """
    FAQ 데이터를 임베딩하여 벡터DB에 저장

    Args:
        faq_data: FAQ 데이터 리스트
        embedder: 임베딩 객체
        store: 벡터 저장소
        batch_size: 배치 크기
    """
    try:
        total_count = len(faq_data)
        logger.info(f"총 {total_count}개 FAQ 임베딩 시작...")

        # 배치 단위로 처리
        for i in range(0, total_count, batch_size):
            batch = faq_data[i:i + batch_size]

            # 문서 텍스트 생성 (Q&A 형태로 결합)
            documents = []
            metadatas = []

            for item in batch:
                # FAQ 문서 형태로 포맷
                doc_text = f"Q: {item['question']}\nA: {item['answer']}"
                documents.append(doc_text)

                # 메타데이터 구성
                metadata = {
                    'source': item['source'],
                    'category': item['category'],
                    'tags': ';'.join(item['keywords']),
                    'timestamp': datetime.now().isoformat(),
                    'question': item['question'],  # 검색 편의성을 위해 추가
                }
                metadatas.append(metadata)

            # 임베딩 생성
            logger.info(f"배치 {i // batch_size + 1}/{(total_count - 1) // batch_size + 1} 임베딩 중...")
            embeddings = embedder.embed(documents)

            # 벡터DB에 저장
            store.add_docs(
                contents=documents,
                metadatas=metadatas,
                embeddings=embeddings,
                ids=None  # UUID 자동 생성
            )

            logger.info(f"배치 완료: {len(batch)}개 FAQ 저장")

        logger.info(f"✅ 전체 {total_count}개 FAQ 초기화 완료!")

    except Exception as e:
        logger.error(f"임베딩/저장 실패: {e}")
        raise


def check_existing_data(store: ChromaStore) -> int:
    """기존 데이터 확인"""
    try:
        # ChromaDB에서 전체 문서 수 확인
        collection_info = store.collection.count()
        return collection_info
    except Exception:
        return 0


def main():
    parser = argparse.ArgumentParser(description='CSV에서 지식베이스 초기화')
    parser.add_argument('--csv-file', required=True, help='FAQ CSV 파일 경로')
    parser.add_argument('--force', action='store_true', help='기존 데이터가 있어도 강제 실행')
    parser.add_argument('--batch-size', type=int, default=10, help='임베딩 배치 크기')

    args = parser.parse_args()

    try:
        # CSV 파일 존재 확인
        if not Path(args.csv_file).exists():
            raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {args.csv_file}")

        # 서비스 초기화
        logger.info("🚀 지식베이스 초기화 시작...")
        embedder = Embedder()
        store = ChromaStore()

        # 기존 데이터 확인
        existing_count = check_existing_data(store)
        if existing_count > 0 and not args.force:
            logger.warning(f"⚠️ 기존 데이터 {existing_count}개 발견. --force 옵션으로 강제 실행 가능")
            return

        if existing_count > 0:
            logger.info(f"기존 데이터 {existing_count}개 위에 추가로 로드합니다.")

        # CSV 로드
        faq_data = load_csv_faq(args.csv_file)

        if not faq_data:
            logger.error("로드할 FAQ 데이터가 없습니다.")
            return

        # 임베딩 및 저장
        embed_and_store_faqs(faq_data, embedder, store, args.batch_size)

        # 최종 확인
        final_count = check_existing_data(store)
        logger.info(f"🎉 초기화 완료! 총 {final_count}개 문서가 지식베이스에 저장되었습니다.")

        # 테스트 쿼리 실행
        logger.info("📝 테스트 쿼리 실행...")
        test_question = "태양광 패널 성능은 어떻게 측정하나요?"
        test_embedding = embedder.embed([test_question])[0]
        results = store.query(test_embedding, k=3)

        if results:
            logger.info(f"✅ 테스트 성공! {len(results)}개 유사 문서 발견")
            logger.info(f"가장 유사한 문서 거리: {results[0]['distance']:.3f}")
        else:
            logger.warning("⚠️ 테스트 쿼리에서 결과를 찾지 못했습니다.")

    except Exception as e:
        logger.error(f"❌ 초기화 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()