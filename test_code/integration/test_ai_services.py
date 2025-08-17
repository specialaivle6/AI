"""
AI 서비스 통합 테스트
로컬 테스트 이미지를 사용한 전체 워크플로우 테스트
"""

import pytest
import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.schemas import DamageAnalysisRequest, PanelRequest
from test_code.test_image_generator import TestImageGenerator, create_mock_s3_url
from test_code.test_image_server import start_test_server


class TestDamageAnalysisIntegration:
    """손상 분석 통합 테스트"""

    @pytest.fixture(scope="class")
    def test_client(self):
        """FastAPI 테스트 클라이언트"""
        return TestClient(app)

    @pytest.fixture(scope="class")
    def test_images(self):
        """테스트 이미지 생성"""
        generator = TestImageGenerator()
        dataset = generator.create_test_dataset()
        return dataset

    @pytest.fixture
    def mock_download_image(self):
        """이미지 다운로드를 로컬 파일로 Mock"""
        async def mock_download(url: str) -> bytes:
            # URL에서 파일명 추출
            filename = url.split("/")[-1]

            # 로컬 테스트 이미지 경로에서 찾기
            test_images_dir = Path("test_code/test_images")

            valid_path = test_images_dir / "valid" / filename
            if valid_path.exists():
                with open(valid_path, 'rb') as f:
                    return f.read()

            invalid_path = test_images_dir / "invalid" / filename
            if invalid_path.exists():
                with open(invalid_path, 'rb') as f:
                    return f.read()

            raise Exception(f"Test image {filename} not found")

        return mock_download

    def test_health_check(self, test_client):
        """헬스체크 테스트"""
        response = test_client.get("/api/damage-analysis/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "model_loaded" in data
        assert "version" in data

    @patch('app.utils.image_utils.download_image_from_s3')
    def test_damage_analysis_normal_panel(self, mock_download, test_client, mock_download_image):
        """정상 패널 손상 분석 테스트"""
        # Mock 설정
        mock_download.side_effect = mock_download_image

        # 테스트 요청 데이터
        request_data = {
            "panel_id": 1,
            "user_id": "550e8400-e29b-41d4-a716-446655440000",  # 유효한 UUID 형식
            "panel_imageurl": create_mock_s3_url("panel_normal_1.jpg")
        }

        response = test_client.post("/api/damage-analysis/analyze", json=request_data)

        # 모델이 없는 경우 503, 있는 경우 200 또는 분석 결과
        if response.status_code == 503:
            # 모델이 로드되지 않은 경우
            pytest.skip("Damage analysis model not loaded")

        assert response.status_code == 200
        data = response.json()

        # 응답 구조 검증
        assert "panel_id" in data
        assert "user_id" in data
        assert "damage_analysis" in data
        assert "business_assessment" in data
        assert "processing_time_seconds" in data

        # 손상 분석 결과 검증
        damage_analysis = data["damage_analysis"]
        assert "overall_damage_percentage" in damage_analysis
        assert "detected_objects" in damage_analysis
        assert damage_analysis["overall_damage_percentage"] >= 0

        # 비즈니스 평가 검증
        business_assessment = data["business_assessment"]
        assert "priority" in business_assessment
        assert "decision" in business_assessment
        assert business_assessment["priority"] in ["HIGH", "MEDIUM", "LOW"]

    @patch('app.utils.image_utils.download_image_from_s3')
    def test_damage_analysis_cracked_panel(self, mock_download, test_client, mock_download_image):
        """균열 패널 손상 분석 테스트"""
        mock_download.side_effect = mock_download_image

        request_data = {
            "panel_id": 2,
            "user_id": "550e8400-e29b-41d4-a716-446655440001",  # 유효한 UUID 형식으로 수정
            "panel_imageurl": create_mock_s3_url("panel_crack_1.jpg")
        }

        response = test_client.post("/api/damage-analysis/analyze", json=request_data)

        if response.status_code == 503:
            pytest.skip("Damage analysis model not loaded")

        assert response.status_code == 200
        data = response.json()

        # 균열이 있는 패널은 손상도가 더 높을 것으로 예상
        damage_analysis = data["damage_analysis"]
        business_assessment = data["business_assessment"]

        # 실제 모델 결과에 따라 달라지지만, 구조는 확인 가능
        assert isinstance(damage_analysis["overall_damage_percentage"], (int, float))
        assert business_assessment["decision"] in ["단순 오염", "수리", "교체"]

    def test_damage_analysis_invalid_request(self, test_client):
        """잘못된 요청 테스트"""
        # 필수 필드 누락
        invalid_request = {
            "panel_id": 1
            # user_id, panel_imageurl 누락
        }

        response = test_client.post("/api/damage-analysis/analyze", json=invalid_request)
        assert response.status_code == 422  # Validation Error

    @patch('app.utils.image_utils.download_image_from_s3')
    def test_damage_analysis_download_error(self, mock_download, test_client):
        """이미지 다운로드 오류 테스트"""
        # 다운로드 실패 Mock - 일반적인 Exception 사용
        mock_download.side_effect = Exception("Network error")

        request_data = {
            "panel_id": 1,
            "user_id": "550e8400-e29b-41d4-a716-446655440002",  # 유효한 UUID 형식으로 수정
            "panel_imageurl": "http://invalid.com/image.jpg"
        }

        response = test_client.post("/api/damage-analysis/analyze", json=request_data)

        # 모델이 로드되지 않은 경우 503, 다운로드 오류 시 400/500 예상
        if response.status_code == 503:
            pytest.skip("Damage analysis model not loaded")

        assert response.status_code in [400, 500]

        data = response.json()
        assert "error" in data
        # 에러 코드는 실제 구현에 따라 달라질 수 있음
        assert data["error"] in ["IMAGE_PROCESSING_ERROR", "INTERNAL_SERVER_ERROR"]


class TestPerformanceAnalysisIntegration:
    """성능 예측 통합 테스트"""

    @pytest.fixture(scope="class")
    def test_client(self):
        return TestClient(app)

    @pytest.fixture
    def sample_panel_request(self):
        """샘플 성능 예측 요청 데이터"""
        return {
            "user_id": "test-user-performance",
            "id": 100,
            "model_name": "Q.PEAK DUO ML-G11.5 / BFG 510W",
            "serial_number": 12345,
            "pmp_rated_w": 510.0,
            "temp_coeff": -0.38,
            "annual_degradation_rate": 0.68,
            "lat": 37.5665,
            "lon": 126.9780,
            "installed_at": "2022-01-15",
            "installed_angle": 30.0,
            "installed_direction": "South",
            "temp": [15.2, 16.8, 18.1, 19.5, 21.0],
            "humidity": [65.0, 62.3, 58.7, 61.2, 67.5],
            "windspeed": [2.1, 1.8, 2.5, 3.2, 2.0],
            "sunshine": [4.2, 5.1, 6.8, 7.2, 5.9],
            "actual_generation": 450.5
        }

    def test_performance_health_check(self, test_client):
        """성능 예측 헬스체크 테스트"""
        response = test_client.get("/api/performance-analysis/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "model_loaded" in data
        assert "service" in data
        assert data["service"] == "performance-analysis"

    def test_performance_analysis_basic(self, test_client, sample_panel_request):
        """기본 성능 예측 테스트"""
        response = test_client.post("/api/performance-analysis/analyze", json=sample_panel_request)

        if response.status_code == 503:
            pytest.skip("Performance analysis model not loaded")

        assert response.status_code == 200
        data = response.json()

        # 응답 구조 검증
        assert "user_id" in data
        assert "panel_id" in data
        assert "performance_analysis" in data
        assert "processing_time_seconds" in data

        # 성능 분석 결과 검증
        performance = data["performance_analysis"]
        assert "predicted_generation" in performance
        assert "actual_generation" in performance
        assert "performance_ratio" in performance
        assert "status" in performance

        # 수치 검증
        assert performance["predicted_generation"] > 0
        assert performance["actual_generation"] == sample_panel_request["actual_generation"]
        assert performance["performance_ratio"] > 0

    def test_performance_report_generation(self, test_client, sample_panel_request):
        """PDF 리포트 생성 테스트"""
        response = test_client.post("/api/performance-analysis/report", json=sample_panel_request)

        if response.status_code == 503:
            pytest.skip("Performance analysis model not loaded")

        assert response.status_code == 200
        data = response.json()

        # 리포트 응답 검증
        assert "user_id" in data
        assert "address" in data  # PDF 파일 경로
        assert "created_at" in data

        # 생성된 PDF 파일 존재 확인
        pdf_path = Path(data["address"])
        assert pdf_path.exists()
        assert pdf_path.suffix == ".pdf"

    def test_performance_analysis_invalid_data(self, test_client):
        """잘못된 성능 예측 데이터 테스트"""
        invalid_request = {
            "user_id": "test",
            "id": 1,
            # 필수 필드들 누락
        }

        response = test_client.post("/api/performance-analysis/analyze", json=invalid_request)
        assert response.status_code == 422  # Validation Error


class TestEndToEndWorkflow:
    """전체 워크플로우 End-to-End 테스트"""

    @pytest.fixture(scope="class")
    def test_client(self):
        return TestClient(app)

    def test_full_application_health(self, test_client):
        """전체 애플리케이션 상태 확인"""
        # 메인 엔드포인트
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data

        # 손상 분석 헬스체크
        damage_health = test_client.get("/api/damage-analysis/health")
        assert damage_health.status_code == 200

        # 성능 예측 헬스체크
        perf_health = test_client.get("/api/performance-analysis/health")
        assert perf_health.status_code == 200

    def test_error_handling_consistency(self, test_client):
        """일관된 에러 처리 테스트"""
        # 존재하지 않는 엔드포인트
        response = test_client.get("/api/nonexistent")
        assert response.status_code == 404

        # 잘못된 HTTP 메서드
        response = test_client.delete("/api/damage-analysis/analyze")
        assert response.status_code == 405


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
