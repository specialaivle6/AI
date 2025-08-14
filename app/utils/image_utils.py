"""
이미지 처리 유틸리티
개선된 설정 시스템과 예외 처리 적용
"""

import io
import httpx
from PIL import Image
from pathlib import Path
from typing import Tuple, Dict, Any
from urllib.parse import urlparse

# 개선된 임포트
from app.core.config import settings
from app.core.exceptions import (
    ImageDownloadException, ImageValidationException,
    ImageProcessingException, TimeoutException
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)


async def download_image_from_s3(s3_url: str) -> bytes:
    """
    S3 URL에서 이미지를 다운로드합니다.

    Args:
        s3_url: S3 이미지 URL

    Returns:
        bytes: 이미지 바이트 데이터

    Raises:
        ImageDownloadException: 다운로드 실패 시
        TimeoutException: 타임아웃 시
    """
    try:
        logger.info(f"S3 이미지 다운로드 시작: {s3_url}")

        async with httpx.AsyncClient(timeout=settings.s3_download_timeout) as client:
            response = await client.get(s3_url)
            response.raise_for_status()

            image_bytes = response.content

            # 이미지 크기 검증
            if len(image_bytes) > settings.max_image_size:
                raise ImageValidationException(
                    f"이미지 크기가 제한을 초과합니다 ({len(image_bytes):,} > {settings.max_image_size:,} bytes)"
                )

            # 이미지 유효성 검증
            filename = urlparse(s3_url).path.split('/')[-1]
            if not validate_image_file(image_bytes, filename):
                raise ImageValidationException(f"유효하지 않은 이미지 파일: {filename}")

            logger.info(f"S3 이미지 다운로드 완료: {len(image_bytes):,} bytes")
            return image_bytes

    except httpx.TimeoutException:
        raise TimeoutException("S3 이미지 다운로드", settings.s3_download_timeout)
    except httpx.HTTPError as e:
        logger.error(f"HTTP 오류로 S3 이미지 다운로드 실패: {e}")
        raise ImageDownloadException(s3_url, f"HTTP 오류: {str(e)}")
    except (ImageValidationException, TimeoutException):
        raise
    except Exception as e:
        logger.error(f"예상치 못한 S3 다운로드 오류: {e}")
        raise ImageDownloadException(s3_url, f"알 수 없는 오류: {str(e)}")


def validate_image_file(image_data: bytes, filename: str) -> bool:
    """
    이미지 파일 유효성 검증

    Args:
        image_data: 이미지 바이트 데이터
        filename: 파일명

    Returns:
        bool: 유효한 이미지인지 여부
    """
    try:
        # 파일 확장자 검증
        file_ext = Path(filename).suffix.lower()
        if file_ext not in settings.allowed_extensions:
            logger.warning(f"지원하지 않는 파일 형식: {file_ext}")
            return False

        # 이미지 데이터 유효성 검증
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                # 이미지 크기 확인 (최소 크기 검증)
                width, height = img.size
                if width < 32 or height < 32:
                    logger.warning(f"이미지 크기가 너무 작음: {width}x{height}")
                    return False

                # 최대 해상도 검증 (메모리 보호)
                max_pixels = 50_000_000  # 약 5천만 픽셀 (예: 7071x7071)
                if width * height > max_pixels:
                    logger.warning(f"이미지 해상도가 너무 높음: {width}x{height}")
                    return False

                # 이미지 모드 확인
                if img.mode not in ['RGB', 'RGBA', 'L', 'P']:
                    logger.warning(f"지원하지 않는 이미지 모드: {img.mode}")
                    return False

                return True

        except Exception as e:
            logger.warning(f"이미지 검증 실패: {e}")
            return False

    except Exception as e:
        logger.error(f"이미지 파일 검증 중 오류: {e}")
        return False


def get_image_info(image_data: bytes, source_url: str) -> Dict[str, Any]:
    """
    이미지 정보 추출

    Args:
        image_data: 이미지 바이트 데이터
        source_url: 원본 URL

    Returns:
        Dict: 이미지 정보
    """
    try:
        with Image.open(io.BytesIO(image_data)) as img:
            return {
                "source_url": source_url,
                "filename": urlparse(source_url).path.split('/')[-1],
                "format": img.format,
                "mode": img.mode,
                "size": {
                    "width": img.width,
                    "height": img.height
                },
                "file_size_bytes": len(image_data),
                "has_transparency": img.mode in ('RGBA', 'LA') or 'transparency' in img.info
            }
    except Exception as e:
        logger.error(f"이미지 정보 추출 실패: {e}")
        return {
            "source_url": source_url,
            "filename": urlparse(source_url).path.split('/')[-1],
            "file_size_bytes": len(image_data),
            "error": str(e)
        }


def preprocess_image_for_ai(image_data: bytes) -> Image.Image:
    """
    AI 모델 입력용 이미지 전처리

    Args:
        image_data: 원본 이미지 데이터

    Returns:
        Image.Image: 전처리된 이미지

    Raises:
        ImageProcessingException: 전처리 실패 시
    """
    try:
        # 이미지 로드
        image = Image.open(io.BytesIO(image_data))

        # RGB 변환 (AI 모델 호환성)
        if image.mode != 'RGB':
            logger.info(f"이미지 모드 변환: {image.mode} -> RGB")
            image = image.convert('RGB')

        # 이미지 크기 정규화 (필요시)
        max_dimension = 2048  # 최대 2K 해상도로 제한
        width, height = image.size

        if max(width, height) > max_dimension:
            # 비율 유지하며 리사이즈
            ratio = max_dimension / max(width, height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)

            logger.info(f"이미지 리사이즈: {width}x{height} -> {new_width}x{new_height}")
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return image

    except Exception as e:
        raise ImageProcessingException(f"이미지 전처리 실패: {str(e)}")


def optimize_image_for_storage(image_data: bytes, quality: int = 85) -> bytes:
    """
    저장용 이미지 최적화

    Args:
        image_data: 원본 이미지 데이터
        quality: JPEG 품질 (1-100)

    Returns:
        bytes: 최적화된 이미지 데이터
    """
    try:
        with Image.open(io.BytesIO(image_data)) as img:
            # RGB 변환
            if img.mode in ('RGBA', 'LA'):
                # 투명도가 있는 경우 흰색 배경과 합성
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # JPEG으로 압축
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)

            optimized_data = output.getvalue()
            compression_ratio = len(optimized_data) / len(image_data)

            logger.info(f"이미지 최적화 완료: {len(image_data):,} -> {len(optimized_data):,} bytes "
                       f"(압축률: {compression_ratio:.2%})")

            return optimized_data

    except Exception as e:
        logger.warning(f"이미지 최적화 실패, 원본 반환: {e}")
        return image_data


def create_thumbnail(image_data: bytes, size: Tuple[int, int] = (150, 150)) -> bytes:
    """
    썸네일 이미지 생성

    Args:
        image_data: 원본 이미지 데이터
        size: 썸네일 크기 (width, height)

    Returns:
        bytes: 썸네일 이미지 데이터
    """
    try:
        with Image.open(io.BytesIO(image_data)) as img:
            # RGB 변환
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # 썸네일 생성 (비율 유지)
            img.thumbnail(size, Image.Resampling.LANCZOS)

            # JPEG로 저장
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=90, optimize=True)

            return output.getvalue()

    except Exception as e:
        raise ImageProcessingException(f"썸네일 생성 실패: {str(e)}")


def extract_image_metadata(image_data: bytes) -> Dict[str, Any]:
    """
    이미지 메타데이터 추출 (EXIF 등)

    Args:
        image_data: 이미지 데이터

    Returns:
        Dict: 메타데이터 정보
    """
    metadata = {}

    try:
        with Image.open(io.BytesIO(image_data)) as img:
            # 기본 정보
            metadata.update({
                "format": img.format,
                "mode": img.mode,
                "size": img.size,
                "has_animation": getattr(img, 'is_animated', False)
            })

            # EXIF 데이터 (있는 경우)
            if hasattr(img, '_getexif') and img._getexif():
                try:
                    exif_data = img._getexif()
                    metadata["exif"] = {
                        str(k): str(v) for k, v in exif_data.items()
                        if isinstance(v, (str, int, float))
                    }
                except Exception:
                    pass

            # 기타 정보
            if img.info:
                metadata["info"] = {
                    k: str(v) for k, v in img.info.items()
                    if isinstance(v, (str, int, float))
                }

    except Exception as e:
        logger.warning(f"메타데이터 추출 실패: {e}")
        metadata["error"] = str(e)

    return metadata
