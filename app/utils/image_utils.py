"""
이미지 처리 유틸리티

이미지 검증, 전처리, 후처리 관련 공통 함수들
"""

import io
from PIL import Image
from pathlib import Path
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


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


def get_image_info(file_bytes: bytes) -> Optional[dict]:
    """
    이미지 기본 정보 추출

    Args:
        file_bytes: 이미지 파일 바이트

    Returns:
        dict: 이미지 정보 (크기, 형식, 모드 등)
    """
    try:
        image = Image.open(io.BytesIO(file_bytes))

        return {
            'width': image.width,
            'height': image.height,
            'format': image.format,
            'mode': image.mode,
            'size_bytes': len(file_bytes),
            'aspect_ratio': round(image.width / image.height, 2)
        }

    except Exception as e:
        logger.error(f"이미지 정보 추출 실패: {str(e)}")
        return None


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
