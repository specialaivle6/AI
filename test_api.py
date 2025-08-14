import requests
import json
from pathlib import Path
import time
from uuid import uuid4

# 테스트용 S3 URL 예시들
SAMPLE_S3_URLS = {
    "1": "https://your-bucket.s3.amazonaws.com/solar-panels/damaged-panel-1.jpg",
    "2": "https://your-bucket.s3.amazonaws.com/solar-panels/clean-panel-1.jpg", 
    "3": "https://your-bucket.s3.amazonaws.com/solar-panels/dirty-panel-1.jpg",
    "4": "https://your-bucket.s3.amazonaws.com/solar-panels/cracked-panel-1.jpg"
}

def print_welcome():
    """환영 메시지와 사용법 출력"""
    print("🌞 Solar Panel AI Service API 테스트 도구")
    print("=" * 60)
    print("이 도구는 태양광 패널 손상 분석 API를 테스트합니다.")
    print("\n📋 테스트 항목:")
    print("1. 서버 헬스체크")
    print("2. AI 서비스 상태 확인") 
    print("3. S3 이미지 분석 테스트")
    print("\n💡 사용법:")
    print("- 서버가 http://localhost:8000 에서 실행 중이어야 합니다")
    print("- S3 URL은 공개적으로 접근 가능한 이미지 URL이어야 합니다")
    print("- 지원 이미지 형식: JPG, PNG")
    print("=" * 60)

def print_sample_urls():
    """샘플 S3 URL들을 출력"""
    print("\n📸 테스트용 S3 URL 예시:")
    print("(실제 사용 시 본인의 S3 URL로 변경하세요)")
    print("-" * 50)
    for key, url in SAMPLE_S3_URLS.items():
        print(f"{key}. {url}")
    print("-" * 50)


def test_health_check():
    """헬스체크 테스트"""
    try:
        response = requests.get("http://localhost:8000/")
        print("기본 헬스체크 결과:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))

        # AI 서비스 전용 헬스체크
        response = requests.get("http://localhost:8000/api/damage-analysis/health")
        print("\nAI 서비스 헬스체크 결과:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        return response.status_code == 200
    except Exception as e:
        print(f"헬스체크 실패: {e}")
        return False


def test_s3_image_analysis(s3_url: str, panel_id: int = 1):
    """S3 URL 기반 이미지 손상 분석 테스트"""
    try:
        print(f"\n🔍 이미지 분석 시작...")
        print(f"Panel ID: {panel_id}")
        print(f"S3 URL: {s3_url}")

        # 백엔드에서 보내는 요청 형태로 시뮬레이션
        request_data = {
            "panel_id": panel_id,
            "user_id": str(uuid4()),  # 테스트용 UUID
            "panel_imageurl": s3_url
        }

        print(f"\n📤 요청 데이터:")
        print(json.dumps(request_data, indent=2, ensure_ascii=False))

        print(f"\n⏳ 분석 중... (30초 정도 소요될 수 있습니다)")

        response = requests.post(
            "http://localhost:8000/api/damage-analysis/analyze",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=60  # 60초 타임아웃
        )

        print(f"\n📥 응답 상태코드: {response.status_code}")

        if response.status_code == 200:
            result = response.json()

            # 전체 응답 출력 (디버깅용)
            print(f"\n📊 전체 응답 데이터:")
            print(json.dumps(result, indent=2, ensure_ascii=False))

            # 주요 분석 결과 요약
            print("\n" + "=" * 50)
            print("🎯 분석 결과 요약")
            print("=" * 50)

            damage_analysis = result.get("damage_analysis", {})
            print(f"🔴 전체 손상률: {damage_analysis.get('overall_damage_percentage', 0):.2f}%")
            print(f"⚠️  심각한 손상률: {damage_analysis.get('critical_damage_percentage', 0):.2f}%")
            print(f"🟤 오염률: {damage_analysis.get('contamination_percentage', 0):.2f}%")
            print(f"✅ 정상률: {damage_analysis.get('healthy_percentage', 100):.2f}%")

            business = result.get("business_assessment", {})
            print(f"\n📈 비즈니스 평가:")
            print(f"우선순위: {business.get('priority', 'N/A')}")
            print(f"위험도: {business.get('risk_level', 'N/A')}")
            print(f"권장사항: {business.get('recommendation', 'N/A')}")

            # 성능 분석 결과
            performance = result.get("performance_analysis", {})
            if performance:
                print(f"\n⚡ 성능 분석:")
                print(f"예상 성능 감소: {performance.get('performance_reduction', 0):.2f}%")
                print(f"효율성 점수: {performance.get('efficiency_score', 0):.2f}")

            return True
        else:
            print(f"❌ 오류 발생 (상태코드: {response.status_code})")
            try:
                error_detail = response.json()
                print("오류 상세:")
                print(json.dumps(error_detail, indent=2, ensure_ascii=False))
            except:
                print("응답 내용:", response.text)
            return False

    except requests.exceptions.Timeout:
        print("❌ 요청 시간 초과 (60초). 서버가 응답하지 않습니다.")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 연결 오류. 서버가 실행 중인지 확인하세요.")
        return False
    except Exception as e:
        print(f"❌ 이미지 분석 실패: {e}")
        return False


def test_service_status():
    """AI 서비스 상태 정보 테스트"""
    try:
        response = requests.get("http://localhost:8000/api/damage-analysis/status")
        print("\nAI 서비스 상태:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        return response.status_code == 200
    except Exception as e:
        print(f"서비스 상태 확인 실패: {e}")
        return False


def get_user_input():
    """사용자로부터 S3 URL 입력 받기"""
    print_sample_urls()

    print("\n🎯 테스트 옵션:")
    print("1. 직접 S3 URL 입력")
    print("2. 샘플 URL 선택")
    print("3. 건너뛰기")

    choice = input("\n선택하세요 (1-3): ").strip()

    if choice == "1":
        url = input("\n테스트할 S3 이미지 URL을 입력하세요: ").strip()
        if url:
            panel_id = input("Panel ID를 입력하세요 (기본값: 1): ").strip()
            panel_id = int(panel_id) if panel_id.isdigit() else 1
            return url, panel_id
    elif choice == "2":
        print("\n샘플 URL 선택:")
        for key, url in SAMPLE_S3_URLS.items():
            print(f"{key}. {url.split('/')[-1]}")

        sample_choice = input("\n샘플 번호를 선택하세요 (1-4): ").strip()
        if sample_choice in SAMPLE_S3_URLS:
            url = SAMPLE_S3_URLS[sample_choice]
            print(f"선택된 URL: {url}")
            return url, 1

    return None, None

def main():
    """전체 테스트 실행"""
    print_welcome()

    print("\n🚀 테스트 시작...")
    time.sleep(1)

    # 1. 헬스체크
    print("\n" + "=" * 50)
    print("❤️  헬스체크 테스트")
    print("=" * 50)

    if not test_health_check():
        print("❌ 헬스체크 실패 - 서버가 실행 중인지 확인하세요")
        print("\n💡 해결 방법:")
        print("1. docker-compose up -d 로 서버를 시작하세요")
        print("2. http://localhost:8000 에 접속 가능한지 확인하세요")
        return

    print("\n✅ 헬스체크 통과")
    time.sleep(1)

    # 2. 서비스 상태 확인
    print("\n" + "=" * 50)
    print("🔧 서비스 상태 확인")
    print("=" * 50)

    if not test_service_status():
        print("❌ 서비스 상태 확인 실패")
        return

    print("\n✅ 서비스 상태 확인 통과")
    time.sleep(1)

    # 3. S3 URL 테스트
    print("\n" + "=" * 50)
    print("📸 S3 이미지 분석 테스트")
    print("=" * 50)

    s3_url, panel_id = get_user_input()

    if s3_url:
        print(f"\n🔍 분석 시작: {s3_url}")
        if test_s3_image_analysis(s3_url, panel_id):
            print("\n✅ S3 이미지 분석 테스트 통과")
        else:
            print("\n❌ S3 이미지 분석 테스트 실패")
            print("\n💡 문제 해결 팁:")
            print("1. S3 URL이 공개적으로 접근 가능한지 확인")
            print("2. 이미지 파일이 JPG/PNG 형식인지 확인")
            print("3. 네트워크 연결 상태 확인")
    else:
        print("⏭️  S3 URL 테스트를 건너뜁니다.")

    print("\n" + "=" * 60)
    print("🎉 테스트 완료!")
    print("📝 FastAPI 문서: http://localhost:8000/docs")
    print("📊 대시보드: http://localhost:8000")
    print("=" * 60)

if __name__ == "__main__":
    main()
