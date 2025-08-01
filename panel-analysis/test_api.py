import requests
import json
from pathlib import Path


def test_health_check():
    """헬스체크 테스트"""
    try:
        response = requests.get("http://localhost:8000/health")
        print("헬스체크 결과:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        return response.status_code == 200
    except Exception as e:
        print(f"헬스체크 실패: {e}")
        return False


def test_image_analysis(image_path: str):
    """이미지 분석 테스트"""
    if not Path(image_path).exists():
        print(f"이미지 파일을 찾을 수 없습니다: {image_path}")
        return False

    try:
        with open(image_path, "rb") as f:
            files = {"file": ("test_image.jpg", f, "image/jpeg")}
            response = requests.post("http://localhost:8000/analyze-panel", files=files)

        print(f"\n이미지 분석 결과 ({image_path}):")
        if response.status_code == 200:
            result = response.json()
            print(json.dumps(result, indent=2, ensure_ascii=False))

            # 핵심 정보만 요약 출력
            print("\n=== 분석 요약 ===")
            print(f"예측 클래스: {result.get('predicted_class', 'N/A')}")
            print(f"신뢰도: {result.get('confidence', 0):.2%}")
            print(f"권장 조치: {result.get('recommendations', {}).get('action', 'N/A')}")
            print(f"우선순위: {result.get('recommendations', {}).get('priority', 'N/A')}")
            print(f"예상 비용: {result.get('recommendations', {}).get('estimated_cost', 0):,}원")
        else:
            print(f"오류 발생 (상태코드: {response.status_code})")
            print(response.text)

        return response.status_code == 200

    except Exception as e:
        print(f"이미지 분석 실패: {e}")
        return False


def download_sample_image():
    """샘플 이미지 다운로드 (테스트용)"""
    import urllib.request

    # 무료 태양광 패널 이미지 URL (예시)
    sample_urls = [
        "https://images.unsplash.com/photo-1509391366360-2e959784a276?w=400",  # 태양광 패널
        "https://images.unsplash.com/photo-1497440001374-f26997328c1b?w=400",  # 태양광 패널 2
    ]

    for i, url in enumerate(sample_urls):
        try:
            filename = f"sample_panel_{i + 1}.jpg"
            print(f"샘플 이미지 다운로드 중: {filename}")
            urllib.request.urlretrieve(url, filename)
            print(f"다운로드 완료: {filename}")
            return filename
        except Exception as e:
            print(f"다운로드 실패: {e}")
            continue

    return None


def main():
    print("=== AI 서버 테스트 시작 ===")

    # 1. 헬스체크
    if not test_health_check():
        print("❌ 헬스체크 실패 - 서버가 실행되지 않았거나 오류가 있습니다.")
        return

    print("✅ 헬스체크 성공")

    # 2. 이미지 분석 테스트
    # 사용자가 제공할 수 있는 이미지 경로들
    test_images = [
        "test_panel.jpg",
        "sample_panel.jpg",
        "~/Pictures/panel_image.jpg",
        "/mnt/c/Users/사용자명/Desktop/panel.jpg",  # Windows 경로
        "sample_panel_1.jpg",
        "sample_panel_2.jpg"
    ]

    tested = False
    for image_path in test_images:
        # 홈 디렉토리 경로 확장
        expanded_path = str(Path(image_path).expanduser())

        if Path(expanded_path).exists():
            print(f"\n📸 테스트 이미지 발견: {expanded_path}")
            if test_image_analysis(expanded_path):
                print(f"✅ {expanded_path} 분석 성공")
                tested = True
            else:
                print(f"❌ {expanded_path} 분석 실패")
        else:
            print(f"⚠️  이미지 없음: {expanded_path}")

    # 3. 샘플 이미지 다운로드 시도
    if not tested:
        print("\n테스트할 이미지가 없습니다. 샘플 이미지를 다운로드합니다...")
        sample_image = download_sample_image()
        if sample_image and test_image_analysis(sample_image):
            print(f"✅ 샘플 이미지 분석 성공: {sample_image}")
        else:
            print("❌ 샘플 이미지 테스트 실패")

    print("\n=== 테스트 완료 ===")
    print("💡 테스트용 이미지를 추가하려면:")
    print("   - 현재 디렉토리에 'test_panel.jpg' 파일을 놓거나")
    print("   - 스크립트에서 test_images 리스트에 본인의 이미지 경로 추가")


if __name__ == "__main__":
    main()