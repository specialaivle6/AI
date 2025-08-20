# debug_config.py - 설정 문제 디버깅 스크립트

import sys
import importlib


def reload_config():
    """설정 모듈 강제 새로고침"""

    # 기존 캐시된 모듈들 제거
    modules_to_reload = [
        'app.core.config',
        'app.embeddings.embedding',
        'app.services.rag',
        'app.api.chat'
    ]

    for module_name in modules_to_reload:
        if module_name in sys.modules:
            print(f"🔄 {module_name} 모듈 캐시 제거")
            del sys.modules[module_name]

    # 설정 다시 로드
    try:
        from app.core.config import settings
        print("✅ 설정 로드 성공")

        # 챗봇 관련 설정 확인
        chatbot_attrs = [
            'EMBEDDING_MODE', 'CHROMA_DIR', 'CHROMA_COLLECTION',
            'HF_EMBED_MODEL', 'OPENAI_EMBED_MODEL', 'OPENAI_API_KEY'
        ]

        print("\n📊 챗봇 설정 확인:")
        for attr in chatbot_attrs:
            if hasattr(settings, attr):
                value = getattr(settings, attr)
                # API 키는 마스킹
                if 'API_KEY' in attr:
                    value = f"{'*' * 20}...{value[-4:]}" if value else "없음"
                print(f"  ✅ {attr}: {value}")
            else:
                print(f"  ❌ {attr}: 속성 없음")

        return True

    except Exception as e:
        print(f"❌ 설정 로드 실패: {e}")
        return False


def test_embedder():
    """임베더 초기화 테스트"""
    try:
        from app.embeddings.embedding import Embedder
        embedder = Embedder()
        print(f"✅ 임베더 초기화 성공 (모드: {embedder.mode})")
        return True
    except Exception as e:
        print(f"❌ 임베더 초기화 실패: {e}")
        return False


if __name__ == "__main__":
    print("🔧 설정 디버깅 시작...\n")

    # 1. 설정 새로고침
    config_ok = reload_config()

    # 2. 임베더 테스트
    if config_ok:
        print("\n🤖 임베더 테스트...")
        embedder_ok = test_embedder()

    print("\n📋 결과 요약:")
    print(f"  - 설정 로드: {'✅' if config_ok else '❌'}")
    if config_ok:
        print(f"  - 임베더: {'✅' if embedder_ok else '❌'}")

    if config_ok and embedder_ok:
        print("\n🎉 모든 테스트 통과! 서버를 다시 시작해주세요.")
    else:
        print("\n🚨 문제 발견. 의존성을 확인해주세요:")
        print("  pip install openai sentence-transformers chromadb")