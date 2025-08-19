"""
이미지 처리 유틸리티 단위 테스트
로컬 테스트 이미지를 사용한 검증
"""

import pytest
import io
from PIL import Image
from unittest.mock import Mock, patch, AsyncMock
import httpx
from pathlib import Path

from app.utils.image_utils import (
    validate_image_file, get_image_info, preprocess_image_for_ai,
    optimize_image_for_storage, create_thumbnail, extract_image_metadata
)
from app.core.exceptions import ImageDownloadException, ImageValidationException
from test_code.test_image_generator import TestImageGenerator


class TestImageValidation:
    """이미지 검증 테스트"""

    @pytest.fixture
    def test_generator(self):
        """테스트 이미지 생성기 픽스처"""
        return TestImageGenerator()

    @pytest.fixture
    def valid_image_data(self, test_generator):
        """유효한 이미지 데이터 픽스처"""
        return test_generator.generate_solar_panel_image()

    @pytest.fixture
    def small_image_data(self):
        """너무 작은 이미지 데이터"""
        img = Image.new('RGB', (20, 20), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        return img_bytes.getvalue()

    def test_validate_valid_image(self, valid_image_data):
        """유효한 이미지 검증 테스트"""
        result = validate_image_file(valid_image_data, "test.jpg")
        assert result is True

    def test_validate_unsupported_extension(self, valid_image_data):
        """지원하지 않는 확장자 테스트"""
        result = validate_image_file(valid_image_data, "test.xyz")
        assert result is False

    def test_validate_small_image(self, small_image_data):
        """너무 작은 이미지 테스트"""
        result = validate_image_file(small_image_data, "small.jpg")
        assert result is False

    def test_validate_corrupted_data(self):
        """손상된 이미지 데이터 테스트"""
        corrupted_data = b"This is not an image file"
        result = validate_image_file(corrupted_data, "corrupted.jpg")
        assert result is False

    def test_get_image_info(self, valid_image_data):
        """이미지 정보 추출 테스트"""
        source_url = "http://test.com/test.jpg"
        info = get_image_info(valid_image_data, source_url)

        assert info["source_url"] == source_url
        assert info["filename"] == "test.jpg"
        assert info["format"] == "JPEG"
        assert info["mode"] == "RGB"
        assert "size" in info
        assert info["size"]["width"] > 0
        assert info["size"]["height"] > 0
        assert info["file_size_bytes"] == len(valid_image_data)


class TestImageProcessing:
    """이미지 처리 테스트"""

    @pytest.fixture
    def test_generator(self):
        return TestImageGenerator()

    @pytest.fixture
    def large_image_data(self, test_generator):
        """큰 이미지 데이터 (리사이즈 테스트용)"""
        return test_generator.generate_solar_panel_image(width=3000, height=2000)

    def test_preprocess_image_for_ai(self, large_image_data):
        """AI용 이미지 전처리 테스트"""
        processed_img = preprocess_image_for_ai(large_image_data)

        assert isinstance(processed_img, Image.Image)
        assert processed_img.mode == "RGB"

        # 큰 이미지는 리사이즈되어야 함
        max_dimension = max(processed_img.size)
        assert max_dimension <= 2048

    def test_optimize_image_for_storage(self, large_image_data):
        """저장용 이미지 최적화 테스트"""
        optimized_data = optimize_image_for_storage(large_image_data, quality=75)

        assert isinstance(optimized_data, bytes)
        # 일반적으로 압축되어야 함
        assert len(optimized_data) <= len(large_image_data)

    def test_create_thumbnail(self, large_image_data):
        """썸네일 생성 테스트"""
        thumbnail_data = create_thumbnail(large_image_data, size=(150, 150))

        assert isinstance(thumbnail_data, bytes)

        # 썸네일 크기 확인
        thumbnail_img = Image.open(io.BytesIO(thumbnail_data))
        assert max(thumbnail_img.size) <= 150

    def test_extract_image_metadata(self, large_image_data):
        """이미지 메타데이터 추출 테스트"""
        metadata = extract_image_metadata(large_image_data)

        assert "format" in metadata
        assert "mode" in metadata
        assert "size" in metadata
        assert metadata["format"] == "JPEG"


class TestMockS3Download:
    """Mock S3 다운로드 테스트 (로컬 서버 사용)"""

    @pytest.mark.asyncio
    async def test_download_success_mock(self):
        """성공적인 다운로드 테스트 (Mock)"""
        from app.utils.image_utils import download_image_from_s3

        # 테스트 이미지 데이터 생성
        generator = TestImageGenerator()
        test_data = generator.generate_solar_panel_image()

        # httpx 클라이언트 Mock
        with patch('app.utils.image_utils.httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.content = test_data
            mock_response.raise_for_status = Mock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # 다운로드 테스트
            result = await download_image_from_s3("http://test.com/test.jpg")

            assert result == test_data
            mock_response.raise_for_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_http_error_mock(self):
        """HTTP 오류 테스트 (Mock)"""
        from app.utils.image_utils import download_image_from_s3

        with patch('app.utils.image_utils.httpx.AsyncClient') as mock_client:
            # HTTP 오류 발생 Mock
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.HTTPError("Network error")
            )

            # 예외 발생 확인
            with pytest.raises(ImageDownloadException) as exc_info:
                await download_image_from_s3("http://test.com/invalid.jpg")

            assert "HTTP 오류" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_download_timeout_mock(self):
        """타임아웃 테스트 (Mock)"""
        from app.utils.image_utils import download_image_from_s3
        from app.core.exceptions import TimeoutException

        with patch('app.utils.image_utils.httpx.AsyncClient') as mock_client:
            # 타임아웃 오류 Mock
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("Request timeout")
            )

            # 타임아웃 예외 발생 확인
            with pytest.raises(TimeoutException) as exc_info:
                await download_image_from_s3("http://test.com/slow.jpg")

            assert "제한시간을 초과" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_download_oversized_image_mock(self):
        """크기 초과 이미지 테스트 (Mock)"""
        from app.utils.image_utils import download_image_from_s3
        from app.core.config import settings

        # 크기 제한보다 큰 가짜 데이터
        oversized_data = b"x" * (settings.max_image_size + 1)

        with patch('app.utils.image_utils.httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.content = oversized_data
            mock_response.raise_for_status = Mock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # 크기 초과 예외 발생 확인
            with pytest.raises(ImageValidationException) as exc_info:
                await download_image_from_s3("http://test.com/huge.jpg")

            assert "크기가 제한을 초과" in str(exc_info.value.message)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
