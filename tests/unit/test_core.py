"""
단위 테스트 - 설정 및 예외 처리 테스트
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from app.core.config import settings, validate_settings, create_directories
from app.core.exceptions import (
    AIServiceException, ModelNotLoadedException, ImageDownloadException,
    DamageAnalysisException, get_http_status_code
)


class TestConfig:
    """설정 관련 테스트"""

    def test_settings_initialization(self):
        """설정 초기화 테스트"""
        assert settings.app_name == "Solar Panel AI Service"
        assert settings.app_version == "3.0.0"
        assert isinstance(settings.confidence_threshold, float)
        assert settings.confidence_threshold > 0

    def test_environment_detection(self):
        """환경 감지 테스트"""
        # 기본적으로 개발 환경이어야 함
        assert settings.is_development == (not settings.debug is False)
        assert settings.is_production != settings.is_development

    def test_damage_constants(self):
        """손상 분석 상수 테스트"""
        constants = settings.DamageConstants
        assert len(constants.CRITICAL_CLASSES) > 0
        assert len(constants.CONTAMINATION_CLASSES) > 0
        assert constants.PRIORITY_HIGH_THRESHOLD > 0
        assert constants.REPAIR_COST_PER_PERCENT > 0

    def test_performance_constants(self):
        """성능 예측 상수 테스트"""
        constants = settings.PerformanceConstants
        assert 0 < constants.PERFORMANCE_RATIO_GOOD <= 1
        assert 0 < constants.PERFORMANCE_RATIO_FAIR <= constants.PERFORMANCE_RATIO_GOOD
        assert constants.EXPECTED_LIFESPAN_MONTHS > 0

    def test_create_directories(self):
        """디렉토리 생성 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 임시로 설정 변경
            original_dirs = [
                settings.models_dir,
                settings.logs_dir,
                settings.reports_dir,
                settings.temp_dir
            ]

            try:
                # 임시 디렉토리로 변경
                settings.models_dir = Path(temp_dir) / "models"
                settings.logs_dir = Path(temp_dir) / "logs"
                settings.reports_dir = Path(temp_dir) / "reports"
                settings.temp_dir = Path(temp_dir) / "temp"

                create_directories()

                # 디렉토리가 생성되었는지 확인
                assert settings.models_dir.exists()
                assert settings.logs_dir.exists()
                assert settings.reports_dir.exists()
                assert settings.temp_dir.exists()

            finally:
                # 원래 설정으로 복원
                settings.models_dir = original_dirs[0]
                settings.logs_dir = original_dirs[1]
                settings.reports_dir = original_dirs[2]
                settings.temp_dir = original_dirs[3]

    def test_validate_settings_missing_models(self):
        """모델 파일 누락 시 설정 검증 테스트"""
        with patch.object(Path, 'exists', return_value=False):
            issues = validate_settings()
            assert len(issues) >= 2  # 손상 분석 모델 + 성능 예측 모델
            assert any("손상 분석 모델" in issue for issue in issues)
            assert any("성능 예측 모델" in issue for issue in issues)


class TestExceptions:
    """예외 처리 테스트"""

    def test_ai_service_exception_basic(self):
        """기본 AI 서비스 예외 테스트"""
        message = "테스트 오류"
        error_code = "TEST_ERROR"
        details = {"key": "value"}

        exc = AIServiceException(message, error_code, details)

        assert str(exc) == message
        assert exc.message == message
        assert exc.error_code == error_code
        assert exc.details == details

    def test_model_not_loaded_exception(self):
        """모델 미로드 예외 테스트"""
        model_name = "TestModel"
        model_path = "/test/path"

        exc = ModelNotLoadedException(model_name, model_path)

        assert model_name in exc.message
        assert exc.details["model_path"] == model_path
        assert exc.error_code == "MODEL_NOT_LOADED"

    def test_image_download_exception(self):
        """이미지 다운로드 예외 테스트"""
        url = "http://test.com/image.jpg"
        reason = "네트워크 오류"

        exc = ImageDownloadException(url, reason)

        assert reason in exc.message
        # ImageDownloadException은 ImageProcessingException을 상속하므로 구조가 다름
        assert exc.details["image_info"]["url"] == url
        assert exc.details["image_info"]["reason"] == reason

    def test_damage_analysis_exception(self):
        """손상 분석 예외 테스트"""
        message = "분석 실패"
        panel_id = 123

        exc = DamageAnalysisException(message, panel_id)

        assert message in exc.message
        assert exc.details["input_info"]["panel_id"] == panel_id
        assert exc.error_code == "ANALYSIS_FAILED"

    def test_http_status_code_mapping(self):
        """HTTP 상태 코드 매핑 테스트"""
        # 모델 미로드 -> 503
        exc1 = ModelNotLoadedException("Test", "/path")
        assert get_http_status_code(exc1) == 503

        # 이미지 다운로드 오류 -> 400
        exc2 = ImageDownloadException("http://test.com", "오류")
        assert get_http_status_code(exc2) == 400

        # 일반 예외 -> 500
        exc3 = Exception("일반 오류")
        assert get_http_status_code(exc3) == 500


class TestLogging:
    """로깅 시스템 테스트"""

    def test_logger_creation(self):
        """로거 생성 테스트"""
        from app.core.logging_config import get_logger

        logger = get_logger("test_logger")
        assert logger.name == "test_logger"

    def test_logger_mixin(self):
        """로거 믹스인 테스트"""
        from app.core.logging_config import LoggerMixin

        class TestClass(LoggerMixin):
            pass

        instance = TestClass()
        assert hasattr(instance, 'logger')
        assert instance.logger.name == "TestClass"

    @patch('app.core.logging_config.get_logger')
    def test_performance_logging(self, mock_get_logger):
        """성능 로깅 테스트"""
        from app.core.logging_config import log_performance

        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        log_performance("test_function", 1.234, param1="value1", param2="value2")

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "test_function" in call_args
        assert "1.234" in call_args
        assert "param1=value1" in call_args


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
