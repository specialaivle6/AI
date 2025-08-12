import requests
import json
from pathlib import Path
import time


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
    """단일 이미지 손상 분석 테스트 (YOLOv8)"""
    if not Path(image_path).exists():
        print(f"이미지 파일을 찾을 수 없습니다: {image_path}")
        return False

    try:
        with open(image_path, "rb") as f:
            files = {"file": (Path(image_path).name, f, "image/jpeg")}
            response = requests.post("http://localhost:8000/analyze-damage", files=files)

        print(f"\n이미지 분석 결과 ({image_path}):")
        if response.status_code == 200:
            result = response.json()

            # 이미지 정보
            image_info = result.get('image_info', {})
            print(f"📸 파일명: {image_info.get('filename', 'Unknown')}")
            print(f"📐 크기: {image_info.get('size', 'Unknown')}")
            print(f"⏱️ 처리시간: {image_info.get('processing_time_seconds', 0)}초")

            # 손상 분석 결과
            damage_analysis = result.get('damage_analysis', {})
            print(f"\n📊 손상 분석 결과:")
            print(f"   전체 손상률: {damage_analysis.get('overall_damage_percentage', 0):.2f}%")
            print(f"   심각한 손상률: {damage_analysis.get('critical_damage_percentage', 0):.2f}%")
            print(f"   오염 손상률: {damage_analysis.get('contamination_percentage', 0):.2f}%")
            print(f"   정상 비율: {damage_analysis.get('healthy_percentage', 0):.2f}%")
            print(f"   평균 신뢰도: {damage_analysis.get('avg_confidence', 0):.3f}")
            print(f"   검출 객체 수: {damage_analysis.get('detected_objects', 0)}개")

            # 클래스별 분석
            class_breakdown = damage_analysis.get('class_breakdown', {})
            if class_breakdown:
                print(f"\n🔍 클래스별 손상률:")
                for class_name, percentage in class_breakdown.items():
                    print(f"   {class_name}: {percentage:.2f}%")

            # 비즈니스 평가
            business_assessment = result.get('business_assessment', {})
            print(f"\n💼 비즈니스 평가:")
            print(f"   우선순위: {business_assessment.get('priority', 'Unknown')}")
            print(f"   위험도: {business_assessment.get('risk_level', 'Unknown')}")
            print(f"   예상 수리비용: {business_assessment.get('estimated_repair_cost_krw', 0):,}원")
            print(f"   성능 저하율: {business_assessment.get('estimated_performance_loss_percent', 0):.1f}%")
            print(f"   유지보수 긴급도: {business_assessment.get('maintenance_urgency_days', 0)}일")

            # 권장사항
            recommendations = business_assessment.get('recommendations', [])
            if recommendations:
                print(f"\n💡 권장 조치사항:")
                for i, recommendation in enumerate(recommendations, 1):
                    print(f"   {i}. {recommendation}")

            # 검출 상세 정보
            detection_details = result.get('detection_details', {})
            total_detections = detection_details.get('total_detections', 0)
            print(f"\n🎯 검출 상세 정보: 총 {total_detections}개 객체")

            detections = detection_details.get('detections', [])
            for i, detection in enumerate(detections[:3], 1):  # 상위 3개만 표시
                print(f"   {i}. {detection.get('class_name', 'Unknown')} "
                      f"(신뢰도: {detection.get('confidence', 0):.3f}, "
                      f"영역: {detection.get('area_pixels', 0):,}px)")

        else:
            print(f"❌ 분석 실패: {response.status_code}")
            print(f"오류 메시지: {response.text}")

        return response.status_code == 200
    except Exception as e:
        print(f"이미지 분석 실패: {e}")
        return False


def test_batch_analysis(image_paths: list):
    """일괄 이미지 분석 테스트 (YOLOv8)"""
    existing_paths = [path for path in image_paths if Path(path).exists()]

    if not existing_paths:
        print("분석할 유효한 이미지 파일이 없습니다.")
        return False

    if len(existing_paths) > 10:
        print("최대 10개 파일까지만 일괄 분석 가능합니다.")
        existing_paths = existing_paths[:10]

    try:
        files = []
        for path in existing_paths:
            with open(path, "rb") as f:
                files.append(("files", (Path(path).name, f.read(), "image/jpeg")))

        response = requests.post("http://localhost:8000/batch-analyze", files=files)

        print(f"\n일괄 분석 결과 ({len(existing_paths)}개 파일):")
        if response.status_code == 200:
            result = response.json()

            # 전체 결과 요약
            print(f"📊 분석 완료: {result.get('total_analyzed', 0)}개 파일")

            summary = result.get('summary', {})
            print(f"\n📈 전체 요약:")
            print(f"   평균 손상률: {summary.get('average_damage_percentage', 0):.2f}%")
            print(f"   심각 손상 패널: {summary.get('critical_panels_count', 0)}개 "
                  f"({summary.get('critical_panels_percentage', 0):.1f}%)")
            print(f"   전체 시설 상태: {summary.get('overall_fleet_status', 'Unknown')}")
            print(f"   권장 조치: {summary.get('recommended_action', 'Unknown')}")

            # 우선순위 분포
            priority_dist = summary.get('priority_distribution', {})
            if priority_dist:
                print(f"\n🚨 우선순위 분포:")
                for priority, count in priority_dist.items():
                    print(f"   {priority}: {count}개")

            # 개별 결과 요약 (상위 3개)
            results = result.get('results', [])
            print(f"\n📋 개별 결과 (상위 3개):")
            for i, res in enumerate(results[:3], 1):
                filename = res.get('image_info', {}).get('filename', f'File {i}')
                damage_pct = res.get('damage_analysis', {}).get('overall_damage_percentage', 0)
                priority = res.get('business_assessment', {}).get('priority', 'Unknown')
                print(f"   {i}. {filename}: {damage_pct:.1f}% 손상 (우선순위: {priority})")

        else:
            print(f"❌ 일괄 분석 실패: {response.status_code}")
            print(f"오류 메시지: {response.text}")

        return response.status_code == 200
    except Exception as e:
        print(f"일괄 분석 실패: {e}")
        return False


def test_error_cases():
    """에러 케이스 테스트"""
    print("\n🧪 에러 케이스 테스트:")

    # 1. 잘못된 파일 형식
    try:
        files = {"file": ("test.txt", b"not an image", "text/plain")}
        response = requests.post("http://localhost:8000/analyze-damage", files=files)
        print(f"1. 잘못된 파일 형식: {response.status_code} - {response.json().get('detail', 'Unknown')}")
    except Exception as e:
        print(f"1. 잘못된 파일 형식 테스트 실패: {e}")

    # 2. 파일 없이 요청
    try:
        response = requests.post("http://localhost:8000/analyze-damage")
        print(f"2. 파일 없는 요청: {response.status_code}")
    except Exception as e:
        print(f"2. 파일 없는 요청 테스트 실패: {e}")

    # 3. 너무 많은 파일 일괄 분석
    try:
        files = [("files", (f"test{i}.jpg", b"fake image", "image/jpeg")) for i in range(15)]
        response = requests.post("http://localhost:8000/batch-analyze", files=files)
        print(f"3. 너무 많은 파일: {response.status_code} - {response.json().get('detail', 'Unknown')}")
    except Exception as e:
        print(f"3. 너무 많은 파일 테스트 실패: {e}")


def main():
    """메인 테스트 실행"""
    print("🚀 YOLOv8 기반 태양광 패널 손상 분석 API 테스트 시작\n")

    # 1. 헬스체크
    print("1️⃣ 헬스체크 테스트")
    health_ok = test_health_check()

    if not health_ok:
        print("❌ 헬스체크 실패. 서버가 실행 중인지 확인하세요.")
        return

    time.sleep(1)

    # 2. 단일 이미지 분석 (테스트 이미지가 있는 경우)
    print("\n2️⃣ 단일 이미지 분석 테스트")
    test_images = [
        "test_image.jpg",
        "sample_panel.jpg",
        "panel_test.png",
        # 실제 존재하는 이미지 경로로 수정 필요
    ]

    analyzed = False
    for image_path in test_images:
        if Path(image_path).exists():
            test_image_analysis(image_path)
            analyzed = True
            break

    if not analyzed:
        print(f"⚠️ 테스트용 이미지 파일을 찾을 수 없습니다.")
        print(f"다음 경로 중 하나에 테스트 이미지를 배치하세요: {test_images}")

    time.sleep(1)

    # 3. 일괄 분석 테스트 (여러 이미지가 있는 경우)
    print("\n3️⃣ 일괄 분석 테스트")
    batch_images = [img for img in test_images if Path(img).exists()]

    if len(batch_images) >= 2:
        test_batch_analysis(batch_images)
    else:
        print("⚠️ 일괄 분석을 위한 이미지가 부족합니다 (최소 2개 필요)")

    time.sleep(1)

    # 4. 에러 케이스 테스트
    print("\n4️⃣ 에러 케이스 테스트")
    test_error_cases()

    print("\n✅ 모든 테스트 완료!")
    print("\n📌 참고사항:")
    print("- 실제 이미지 파일을 프로젝트 루트에 배치하면 더 정확한 테스트가 가능합니다")
    print("- API 문서는 http://localhost:8000/docs 에서 확인할 수 있습니다")
    print("- 헬스체크는 http://localhost:8000/health 에서 확인할 수 있습니다")


if __name__ == "__main__":
    main()