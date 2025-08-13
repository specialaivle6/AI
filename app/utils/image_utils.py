"""
이미지 처리 유틸리티

이미지 검증, 전처리, 후처리, S3 다운로드 관련 공통 함수들
"""

import io
import httpx
from PIL import Image
from pathlib import Path
from typing import Tuple, Dict, Any
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


async def download_image_from_s3(s3_url: str, timeout: int = 30) -> bytes:
    """
    S3 URL에서 이미지를 다운로드합니다.

    Args:
        s3_url: S3 이미지 URL
        timeout: 다운로드 타임아웃 (초)

    Returns:
        bytes: 이미지 바이트 데이터

    Raises:
        Exception: 다운로드 실패 시
    """
    try:
        logger.info(f"S3 이미지 다운로드 시작: {s3_url}")

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(s3_url)
            response.raise_for_status()

            image_bytes = response.content

            # 이미지 유효성 검증
            filename = urlparse(s3_url).path.split('/')[-1]
            if not validate_image_file(image_bytes, filename):
                raise ValueError(f"유효하지 않은 이미지 파일: {filename}")

            logger.info(f"S3 이미지 다운로드 완료: {len(image_bytes)} bytes")
            return image_bytes

    except httpx.HTTPError as e:
        logger.error(f"HTTP 오류로 S3 이미지 다운로드 실패: {e}")
        raise Exception(f"S3 이미지 다운로드 실패: {str(e)}")
    except Exception as e:
        logger.error(f"S3 이미지 다운로드 중 오류: {e}")
        raise


def validate_image_file(file_bytes: bytes, filename: str, max_size: int = 20 * 1024 * 1024) -> bool:
    """
    이미지 파일 유효성 검증

    Args:
        file_bytes: 이미지 파일 바이트
        filename: 파일명
        max_size: 최대 파일 크기 (바이트)

    Returns:
        bool: 유효한 이미지 파일 여부
    """
    try:
        # 파일 크기 검증
        if len(file_bytes) > max_size:
            logger.warning(f"파일 크기 초과: {filename} ({len(file_bytes)} bytes)")
            return False

        # 확장자 검증
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
        file_ext = Path(filename).suffix.lower()
        if file_ext not in allowed_extensions:
            logger.warning(f"지원하지 않는 파일 형식: {filename} ({file_ext})")
            return False

        # 이미지 파일인지 검증
        image = Image.open(io.BytesIO(file_bytes))
        image.verify()  # 이미지 무결성 검증

        logger.info(f"이미지 파일 검증 성공: {filename}")
        return True

    except Exception as e:
        logger.error(f"이미지 파일 검증 실패: {filename} - {str(e)}")
        return False


def get_image_info(image_bytes: bytes, url: str = "") -> Dict[str, Any]:
    """
    이미지 정보를 추출합니다.

    Args:
        image_bytes: 이미지 바이트 데이터
        url: 이미지 URL (선택사항)

    Returns:
        dict: 이미지 정보
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        filename = urlparse(url).path.split('/')[-1] if url else "unknown"

        return {
            "filename": filename,
            "size": f"{image.width}x{image.height}",
            "format": image.format,
            "mode": image.mode,
            "file_size_bytes": len(image_bytes)
        }
    except Exception as e:
        logger.error(f"이미지 정보 추출 실패: {e}")
        return {
            "filename": "unknown",
            "size": "unknown",
            "format": "unknown",
            "mode": "unknown",
            "file_size_bytes": len(image_bytes)
        }


def resize_image_if_needed(file_bytes: bytes, max_dimension: int = 2048) -> bytes:
    """
    이미지 크기가 너무 큰 경우 리사이즈

    Args:
        file_bytes: 원본 이미지 바이트
        max_dimension: 최대 가로/세로 크기

    Returns:
        bytes: 리사이즈된 이미지 바이트 (필요한 경우만)
    """
    try:
        image = Image.open(io.BytesIO(file_bytes))

        # 크기 확인
        if max(image.width, image.height) <= max_dimension:
            return file_bytes  # 리사이즈 불필요

        # 비율 유지하면서 리사이즈
        ratio = max_dimension / max(image.width, image.height)
        new_width = int(image.width * ratio)
        new_height = int(image.height * ratio)

        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # 바이트로 변환
        output = io.BytesIO()
        resized_image.save(output, format=image.format or 'JPEG', quality=95)

        logger.info(f"이미지 리사이즈: {image.width}x{image.height} → {new_width}x{new_height}")
        return output.getvalue()

    except Exception as e:
        logger.error(f"이미지 리사이즈 실패: {str(e)}")
        return file_bytes  # 실패 시 원본 반환


def calculate_file_hash(file_bytes: bytes) -> str:
    """
    파일 해시 계산 (중복 검사용)

    Args:
        file_bytes: 파일 바이트

    Returns:
        str: SHA256 해시값
    """
    import hashlib
    return hashlib.sha256(file_bytes).hexdigest()


def is_valid_panel_image(image_info: dict) -> Tuple[bool, str]:
    """
    태양광 패널 이미지로 적합한지 검증

    Args:
        image_info: get_image_info()로 얻은 이미지 정보

    Returns:
        Tuple[bool, str]: (유효성, 메시지)
    """
    if not image_info:
        return False, "이미지 정보를 읽을 수 없습니다."

    # 최소 해상도 검증
    min_dimension = 224  # YOLOv8 최소 요구사항
    if image_info['width'] < min_dimension or image_info['height'] < min_dimension:
        return False, f"해상도가 너무 낮습니다. 최소 {min_dimension}x{min_dimension} 필요"

    # 극단적인 비율 검증 (1:10 이상 차이나면 패널 이미지가 아닐 가능성)
    aspect_ratio = image_info['aspect_ratio']
    if aspect_ratio > 10 or aspect_ratio < 0.1:
        return False, f"이미지 비율이 부적절합니다. (현재: {aspect_ratio}:1)"

    # 파일 크기 검증 (너무 작으면 의미있는 분석 어려움)
    min_file_size = 50 * 1024  # 50KB
    if image_info['size_bytes'] < min_file_size:
        return False, f"파일 크기가 너무 작습니다. 최소 {min_file_size//1024}KB 필요"

    return True, "유효한 패널 이미지입니다."
