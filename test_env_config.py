#!/usr/bin/env python3
"""
환경 변수 설정 테스트 스크립트
.env 파일이 제대로 로드되는지 확인
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_env_loading():
    """환경 변수 로딩 테스트"""
    print("=== 환경 변수 로딩 테스트 ===\n")

    # .env 파일 존재 확인
    env_file = project_root / ".env"
    print(f"1. .env 파일 존재 여부: {env_file.exists()}")
    print(f"   경로: {env_file}\n")

    if not env_file.exists():
        print("❌ .env 파일을 찾을 수 없습니다!")
        return

    # .env 파일 내용 읽기
    print("2. .env 파일 내용:")
    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:10], 1):  # 처음 10줄만 표시
            if line.strip() and not line.startswith('#'):
                print(f"   {i:2d}: {line.strip()}")
    print(f"   ... (총 {len(lines)}줄)\n")

    # 직접 os.getenv로 환경 변수 확인
    print("3. 직접 os.getenv 테스트:")
    test_vars = [
        "DEBUG", "LOG_LEVEL", "HOST", "PORT",
        "OPENAI_API_KEY", "AWS_ACCESS_KEY_ID",
        "CONFIDENCE_THRESHOLD", "MAX_DISTANCE_TO_ANSWER"
    ]

    for var in test_vars:
        value = os.getenv(var)
        if value:
            # 민감한 정보는 마스킹
            if "KEY" in var or "SECRET" in var:
                masked_value = value[:8] + "..." if len(value) > 8 else "***"
                print(f"   ✅ {var}: {masked_value}")
            else:
                print(f"   ✅ {var}: {value}")
        else:
            print(f"   ❌ {var}: None (환경변수 없음)")

    print()

def test_dotenv_loading():
    """python-dotenv 라이브러리로 .env 파일 로딩 테스트"""
    print("4. python-dotenv 라이브러리 테스트:")

    try:
        from dotenv import load_dotenv

        # .env 파일 로드
        env_file = project_root / ".env"
        loaded = load_dotenv(env_file)
        print(f"   ✅ dotenv 로딩 결과: {loaded}")

        # 로딩 후 환경 변수 재확인
        print("   로딩 후 환경 변수:")
        test_vars = ["DEBUG", "LOG_LEVEL", "OPENAI_API_KEY"]
        for var in test_vars:
            value = os.getenv(var)
            if value:
                if "KEY" in var:
                    masked_value = value[:8] + "..." if len(value) > 8 else "***"
                    print(f"     ✅ {var}: {masked_value}")
                else:
                    print(f"     ✅ {var}: {value}")
            else:
                print(f"     ❌ {var}: None")

    except ImportError:
        print("   ❌ python-dotenv 라이브러리가 설치되지 않았습니다.")
        print("   설치 명령: pip install python-dotenv")

    print()

def test_config_loading():
    """config.py 모듈 로딩 테스트"""
    print("5. config.py 모듈 로딩 테스트:")

    try:
        # dotenv 먼저 로드
        try:
            from dotenv import load_dotenv
            load_dotenv(project_root / ".env")
        except ImportError:
            pass

        from app.core.config import settings

        print("   ✅ config 모듈 로딩 성공")
        print(f"   앱 이름: {settings.app_name}")
        print(f"   디버그 모드: {settings.debug}")
        print(f"   로그 레벨: {settings.log_level}")
        print(f"   포트: {settings.port}")
        print(f"   호스트: {settings.host}")
        print(f"   신뢰도 임계값: {settings.confidence_threshold}")

        # OpenAI API 키 확인
        if settings.OPENAI_API_KEY:
            masked_key = settings.OPENAI_API_KEY[:8] + "..."
            print(f"   OpenAI API Key: {masked_key}")
        else:
            print("   ❌ OpenAI API Key: 없음")

        # AWS 설정 확인
        if hasattr(settings, 'aws_access_key_id') and settings.aws_access_key_id:
            masked_aws = settings.aws_access_key_id[:8] + "..."
            print(f"   AWS Access Key: {masked_aws}")
        else:
            print("   ❌ AWS Access Key: 없음")

    except Exception as e:
        print(f"   ❌ config 모듈 로딩 실패: {e}")

    print()

def identify_issues():
    """문제점 식별 및 해결 방안 제시"""
    print("6. 문제점 분석 및 해결 방안:")

    # config.py 파일 확인
    config_file = project_root / "app" / "core" / "config.py"
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()

        issues = []

        # python-dotenv 사용 확인
        if "from dotenv import load_dotenv" not in content:
            issues.append("config.py에서 python-dotenv를 사용하지 않음")

        if "load_dotenv(" not in content:
            issues.append("config.py에서 .env 파일을 명시적으로 로드하지 않음")

        # Pydantic BaseSettings 사용 확인
        if "BaseSettings" not in content:
            issues.append("Pydantic BaseSettings를 사용하지 않음 (권장)")

        # Config 클래스 확인
        if "class Config:" in content and "env_file" in content:
            print("   ✅ Config 클래스에 env_file 설정이 있음")
        else:
            issues.append("Config 클래스에 env_file 설정이 없음")

        if issues:
            print("   발견된 문제점들:")
            for i, issue in enumerate(issues, 1):
                print(f"     {i}. {issue}")
        else:
            print("   ✅ 주요 설정 문제 없음")

    print()

if __name__ == "__main__":
    test_env_loading()
    test_dotenv_loading()
    test_config_loading()
    identify_issues()

    print("=== 테스트 완료 ===")
