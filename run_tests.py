"""
테스트 실행 스크립트
다양한 테스트 시나리오를 쉽게 실행할 수 있도록 도와주는 스크립트
"""

import subprocess
import sys
import argparse
from pathlib import Path


def run_command(command: list, description: str):
    """명령어 실행 및 결과 출력"""
    print(f"\n🔄 {description}")
    print(f"📝 실행 명령: {' '.join(command)}")
    print("-" * 50)

    try:
        result = subprocess.run(command, capture_output=True, text=True)

        if result.stdout:
            print(result.stdout)
        if result.stderr and result.returncode != 0:
            print("❌ 오류:", result.stderr)

        return result.returncode == 0
    except Exception as e:
        print(f"❌ 명령 실행 실패: {e}")
        return False


def generate_test_images():
    """테스트 이미지 생성"""
    print("🖼️  테스트 이미지 생성 중...")
    try:
        from tests.test_image_generator import TestImageGenerator
        generator = TestImageGenerator()
        dataset = generator.create_test_dataset()
        print(f"✅ 테스트 이미지 생성 완료: {len(dataset['valid'])}개 유효, {len(dataset['invalid'])}개 무효")
        return True
    except Exception as e:
        print(f"❌ 테스트 이미지 생성 실패: {e}")
        return False


def run_unit_tests():
    """단위 테스트 실행"""
    command = ["python", "-m", "pytest", "tests/unit/", "-v", "-m", "unit"]
    return run_command(command, "단위 테스트 실행")


def run_integration_tests():
    """통합 테스트 실행"""
    command = ["python", "-m", "pytest", "tests/integration/", "-v", "-m", "integration"]
    return run_command(command, "통합 테스트 실행")


def run_all_tests():
    """모든 테스트 실행"""
    command = ["python", "-m", "pytest", "tests/", "-v"]
    return run_command(command, "전체 테스트 실행")


def run_fast_tests():
    """빠른 테스트만 실행 (느린 테스트 제외)"""
    command = ["python", "-m", "pytest", "tests/", "-v", "-m", "not slow"]
    return run_command(command, "빠른 테스트 실행 (느린 테스트 제외)")


def run_coverage_tests():
    """코드 커버리지와 함께 테스트 실행"""
    commands = [
        ["python", "-m", "pip", "install", "pytest-cov"],
        ["python", "-m", "pytest", "tests/", "--cov=app", "--cov-report=html", "--cov-report=term"]
    ]

    success = True
    for cmd in commands:
        if not run_command(cmd, f"커버리지 테스트 실행 - {' '.join(cmd[:3])}"):
            success = False

    if success:
        print("\n📊 커버리지 리포트가 htmlcov/ 디렉토리에 생성되었습니다.")

    return success


def check_test_environment():
    """테스트 환경 확인"""
    print("🔍 테스트 환경 확인 중...")

    # 필요한 디렉토리 확인
    required_dirs = [
        "tests/",
        "tests/unit/",
        "tests/integration/",
        "tests/test_images/"
    ]

    missing_dirs = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)

    if missing_dirs:
        print(f"❌ 누락된 디렉토리: {missing_dirs}")
        return False

    # 테스트 이미지 확인
    test_images_dir = Path("tests/test_images/valid")
    if not test_images_dir.exists() or len(list(test_images_dir.glob("*.jpg"))) < 5:
        print("⚠️  테스트 이미지가 부족합니다. 생성하시겠습니까? (y/n)")
        if input().lower() == 'y':
            return generate_test_images()
        else:
            print("❌ 테스트 이미지가 필요합니다.")
            return False

    # pytest 설치 확인
    try:
        import pytest
        print(f"✅ pytest 설치됨: {pytest.__version__}")
    except ImportError:
        print("❌ pytest가 설치되지 않음. pip install pytest로 설치해주세요.")
        return False

    print("✅ 테스트 환경 준비 완료")
    return True


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="AI 서비스 테스트 실행 스크립트")
    parser.add_argument(
        "test_type",
        choices=["unit", "integration", "all", "fast", "coverage", "setup", "check"],
        help="실행할 테스트 타입"
    )
    parser.add_argument(
        "--generate-images",
        action="store_true",
        help="테스트 이미지 생성"
    )

    args = parser.parse_args()

    print("🧪 AI 서비스 테스트 실행 스크립트")
    print("=" * 50)

    # 테스트 이미지 생성 (옵션)
    if args.generate_images:
        if not generate_test_images():
            sys.exit(1)

    # 테스트 타입별 실행
    success = True

    if args.test_type == "check":
        success = check_test_environment()
    elif args.test_type == "setup":
        success = check_test_environment() and generate_test_images()
    elif args.test_type == "unit":
        success = check_test_environment() and run_unit_tests()
    elif args.test_type == "integration":
        success = check_test_environment() and run_integration_tests()
    elif args.test_type == "all":
        success = check_test_environment() and run_all_tests()
    elif args.test_type == "fast":
        success = check_test_environment() and run_fast_tests()
    elif args.test_type == "coverage":
        success = check_test_environment() and run_coverage_tests()

    if success:
        print("\n🎉 테스트 실행 완료!")
        sys.exit(0)
    else:
        print("\n❌ 테스트 실행 실패!")
        sys.exit(1)


if __name__ == "__main__":
    main()
