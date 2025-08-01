import torch
from torchvision import transforms
from PIL import Image
import io
import logging
from typing import Union

logger = logging.getLogger(__name__)


class ImageProcessor:
    def __init__(self):
        # MobileNetV3 ImageNet 전처리 파이프라인
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),  # 224x224로 리사이즈
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],  # ImageNet 평균
                std=[0.229, 0.224, 0.225]  # ImageNet 표준편차
            )
        ])

    def preprocess(self, image_input: Union[bytes, str, Image.Image]) -> torch.Tensor:
        """
        이미지를 모델 입력 형식으로 전처리

        Args:
            image_input: 이미지 (bytes, 파일 경로, 또는 PIL Image)

        Returns:
            torch.Tensor: 전처리된 이미지 텐서
        """
        try:
            # 입력 타입에 따라 PIL Image로 변환
            if isinstance(image_input, bytes):
                image = Image.open(io.BytesIO(image_input))
            elif isinstance(image_input, str):
                image = Image.open(image_input)
            elif isinstance(image_input, Image.Image):
                image = image_input
            else:
                raise ValueError(f"지원하지 않는 이미지 형식: {type(image_input)}")

            # RGB로 변환 (RGBA나 그레이스케일 대응)
            if image.mode != 'RGB':
                image = image.convert('RGB')
                logger.info(f"이미지를 RGB로 변환: {image.mode} -> RGB")

            # 이미지 정보 로깅
            logger.info(f"원본 이미지 크기: {image.size}")

            # 전처리 적용
            tensor = self.transform(image)

            logger.info(f"전처리 완료: {tensor.shape}")
            return tensor

        except Exception as e:
            logger.error(f"이미지 전처리 중 오류: {str(e)}")
            raise e

    def validate_image(self, image_bytes: bytes) -> bool:
        """
        이미지 파일 유효성 검사

        Args:
            image_bytes: 이미지 바이트 데이터

        Returns:
            bool: 유효한 이미지인지 여부
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))

            # 기본 유효성 검사
            if image.width < 50 or image.height < 50:
                logger.warning(f"이미지가 너무 작음: {image.size}")
                return False

            if image.width > 4000 or image.height > 4000:
                logger.warning(f"이미지가 너무 큼: {image.size}")
                return False

            # 지원 형식 확인
            supported_formats = ['JPEG', 'PNG', 'BMP', 'TIFF']
            if image.format not in supported_formats:
                logger.warning(f"지원하지 않는 형식: {image.format}")
                return False

            return True

        except Exception as e:
            logger.error(f"이미지 유효성 검사 실패: {str(e)}")
            return False

    def get_image_info(self, image_bytes: bytes) -> dict:
        """
        이미지 메타데이터 추출

        Args:
            image_bytes: 이미지 바이트 데이터

        Returns:
            dict: 이미지 정보
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))

            info = {
                'format': image.format,
                'mode': image.mode,
                'size': image.size,
                'width': image.width,
                'height': image.height
            }

            # EXIF 데이터가 있다면 추가
            if hasattr(image, '_getexif') and image._getexif():
                info['has_exif'] = True
            else:
                info['has_exif'] = False

            return info

        except Exception as e:
            logger.error(f"이미지 정보 추출 실패: {str(e)}")
            return {}