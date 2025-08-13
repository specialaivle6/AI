import requests
import json
from pathlib import Path
import time
from uuid import uuid4


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
        # 백엔드에서 보내는 요청 형태로 시뮬레이션
        request_data = {
            "panel_id": panel_id,
            "user_id": str(uuid4()),  # 테스트용 UUID
            "panel_imageurl": s3_url
        }

        print(f"\nS3 이미지 분석 요청:")
        print(f"Panel ID: {panel_id}")
        print(f"S3 URL: {s3_url}")

        response = requests.post(
            "http://localhost:8000/api/damage-analysis/analyze",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )

        print(f"\n이미지 분석 결과:")
        if response.status_code == 200:
            result = response.json()
            print(json.dumps(result, indent=2, ensure_ascii=False))

            # 주요 분석 결과 요약
            print("\n=== 분석 결과 요약 ===")
            damage_analysis = result.get("damage_analysis", {})
            print(f"전체 손상률: {damage_analysis.get('overall_damage_percentage', 0):.2f}%")
            print(f"심각한 손상률: {damage_analysis.get('critical_damage_percentage', 0):.2f}%")
            print(f"오염률: {damage_analysis.get('contamination_percentage', 0):.2f}%")
            print(f"정상률: {damage_analysis.get('healthy_percentage', 100):.2f}%")

            business = result.get("business_assessment", {})
            print(f"우선순위: {business.get('priority', 'N/A')}")
            print(f"위험도: {business.get('risk_level', 'N/A')}")

            return True
        else:
            print(f"오류 발생 (상태코드: {response.status_code})")
            print(response.text)
            return False

    except Exception as e:
        print(f"이미지 분석 실패: {e}")
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


def main():
    """전체 테스트 실행"""
    print("🔍 Solar Panel AI Service 테스트 시작\n")
    print("=" * 50)

    # 1. 헬스체크
    if not test_health_check():
        print("❌ 헬스체크 실패 - 서버가 실행 중인지 확인하세요")
        return

    print("\n✅ 헬스체크 통과")
    time.sleep(1)

    # 2. 서비스 상태 확인
    if not test_service_status():
        print("❌ 서비스 상태 확인 실패")
        return

    print("\n✅ 서비스 상태 확인 통과")
    time.sleep(1)

    # 3. S3 URL 테스트 (실제 S3 URL로 변경 필요)
    print("\n" + "=" * 50)
    print("📸 S3 이미지 분석 테스트")

    # 테스트용 S3 URL (실제 사용 시 변경 필요)
    test_s3_url = input("\n테스트할 S3 이미지 URL을 입력하세요 (Enter로 건너뛰기): ").strip()

    if test_s3_url:
        if test_s3_image_analysis(test_s3_url):
            print("\n✅ S3 이미지 분석 테스트 통과")
        else:
            print("\n❌ S3 이미지 분석 테스트 실패")
    else:
        print("S3 URL 테스트를 건너뜁니다.")

    print("\n" + "=" * 50)
    print("🎉 테스트 완료!")


if __name__ == "__main__":
    main()
