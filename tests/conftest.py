"""
pytest 설정 파일
테스트 환경 설정 및 공통 픽스처 정의
"""

import pytest
import asyncio
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 테스트 환경 설정
os.environ["DEBUG"] = "True"
os.environ["LOG_LEVEL"] = "WARNING"  # 테스트 중 로그 최소화


@pytest.fixture(scope="session")
def event_loop():
    """세션 범위 이벤트 루프"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """테스트 환경 자동 설정"""
    print("\n[SETUP] 테스트 환경 설정 중...")

    # 테스트 이미지 생성
    from tests.test_image_generator import TestImageGenerator

    generator = TestImageGenerator()

    # 이미지가 이미 존재하는지 확인
    valid_dir = Path("tests/test_images/valid")
    if not valid_dir.exists() or len(list(valid_dir.glob("*.jpg"))) < 5:
        print("[IMAGE] 테스트 이미지 생성 중...")
        dataset = generator.create_test_dataset()
        print(f"[SUCCESS] 테스트 이미지 생성 완료: {len(dataset['valid'])}개 유효, {len(dataset['invalid'])}개 무효")
    else:
        print("[SUCCESS] 기존 테스트 이미지 사용")

    yield

    print("\n[CLEANUP] 테스트 환경 정리 완료")


@pytest.fixture
def mock_models_loaded():
    """모델 로딩 상태를 Mock으로 처리"""
    from unittest.mock import patch

    with patch('app.services.damage_analyzer.DamageAnalyzer.is_loaded', return_value=True), \
         patch('app.services.performance_analyzer.PerformanceAnalyzer.is_loaded', return_value=True):
        yield


# pytest 마커 정의
def pytest_configure(config):
    """pytest 설정"""
    config.addinivalue_line(
        "markers", "unit: 단위 테스트"
    )
    config.addinivalue_line(
        "markers", "integration: 통합 테스트"
    )
    config.addinivalue_line(
        "markers", "slow: 느린 테스트 (모델 로딩 등)"
    )
    config.addinivalue_line(
        "markers", "requires_models: 실제 모델 파일이 필요한 테스트"
    )


# 테스트 결과 요약
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """테스트 결과 요약 출력"""
    print("\n" + "="*50)
    print("[TEST] 테스트 실행 완료")
    print("="*50)

    if hasattr(terminalreporter, 'stats'):
        stats = terminalreporter.stats

        passed = len(stats.get('passed', []))
        failed = len(stats.get('failed', []))
        skipped = len(stats.get('skipped', []))

        print(f"[PASS] 성공: {passed}개")
        print(f"[FAIL] 실패: {failed}개")
        print(f"[SKIP] 건너뛴 테스트: {skipped}개")

        if failed > 0:
            print("\n[WARN] 실패한 테스트가 있습니다. 로그를 확인해주세요.")
        elif passed > 0:
            print("\n[SUCCESS] 모든 테스트가 성공했습니다!")

    print("="*50)
