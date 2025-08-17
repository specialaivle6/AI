"""
테스트용 이미지 생성 및 관리 유틸리티
로컬 테스트 환경에서 사용할 가짜 태양광 패널 이미지들을 생성합니다.
"""

import io
import os
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from typing import Dict, List, Tuple
import random


class TestImageGenerator:
    """테스트용 이미지 생성기"""

    def __init__(self, base_path: str = "test_code/test_images"):
        self.base_path = Path(base_path)
        self.valid_path = self.base_path / "valid"
        self.invalid_path = self.base_path / "invalid"

        # 디렉토리 생성
        self.valid_path.mkdir(parents=True, exist_ok=True)
        self.invalid_path.mkdir(parents=True, exist_ok=True)

    def generate_solar_panel_image(
        self,
        width: int = 800,
        height: int = 600,
        damage_type: str = "normal",
        save_path: str = None
    ) -> bytes:
        """
        태양광 패널 이미지 생성

        Args:
            width: 이미지 너비
            height: 이미지 높이
            damage_type: 손상 타입 (normal, crack, bird_drop, dusty, snow)
            save_path: 저장 경로 (None이면 메모리에만)

        Returns:
            bytes: 이미지 바이트 데이터
        """
        # 기본 패널 색상 (어두운 파란색)
        img = Image.new('RGB', (width, height), color='#1a237e')
        draw = ImageDraw.Draw(img)

        # 태양광 셀 그리드 그리기
        cell_width = width // 6
        cell_height = height // 4

        for row in range(4):
            for col in range(6):
                x1 = col * cell_width + 5
                y1 = row * cell_height + 5
                x2 = x1 + cell_width - 10
                y2 = y1 + cell_height - 10

                # 셀 색상 (약간 밝은 파란색)
                cell_color = '#303f9f'
                draw.rectangle([x1, y1, x2, y2], fill=cell_color, outline='#1a237e', width=2)

        # 손상 타입별 효과 추가
        if damage_type == "crack":
            self._add_crack_damage(draw, width, height)
        elif damage_type == "bird_drop":
            self._add_bird_drop_damage(draw, width, height)
        elif damage_type == "dusty":
            self._add_dust_damage(draw, width, height)
        elif damage_type == "snow":
            self._add_snow_damage(draw, width, height)

        # 이미지를 바이트로 변환
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG', quality=90)
        img_data = img_bytes.getvalue()

        # 파일로 저장 (선택적)
        if save_path:
            img.save(save_path, format='JPEG', quality=90)

        return img_data

    def _add_crack_damage(self, draw: ImageDraw.Draw, width: int, height: int):
        """균열 손상 추가"""
        # 대각선 균열
        draw.line([(width//4, height//4), (3*width//4, 3*height//4)],
                 fill='#000000', width=3)
        # 가지 균열들
        for _ in range(3):
            x1 = random.randint(width//4, 3*width//4)
            y1 = random.randint(height//4, 3*height//4)
            x2 = x1 + random.randint(-50, 50)
            y2 = y1 + random.randint(-50, 50)
            draw.line([(x1, y1), (x2, y2)], fill='#333333', width=2)

    def _add_bird_drop_damage(self, draw: ImageDraw.Draw, width: int, height: int):
        """새 배설물 손상 추가"""
        for _ in range(random.randint(2, 5)):
            x = random.randint(50, width-50)
            y = random.randint(50, height-50)
            radius = random.randint(15, 30)
            draw.ellipse([x-radius, y-radius, x+radius, y+radius],
                        fill='#ffffff', outline='#cccccc', width=1)

    def _add_dust_damage(self, draw: ImageDraw.Draw, width: int, height: int):
        """먼지 손상 추가"""
        # 반투명 먼지 효과 (점들로 표현)
        for _ in range(200):
            x = random.randint(0, width)
            y = random.randint(0, height)
            draw.point((x, y), fill='#8d6e63')

    def _add_snow_damage(self, draw: ImageDraw.Draw, width: int, height: int):
        """눈 손상 추가"""
        # 눈 덮인 부분
        snow_height = random.randint(height//4, height//2)
        draw.rectangle([0, height-snow_height, width, height],
                      fill='#ffffff', outline='#e0e0e0', width=1)

    def create_test_dataset(self) -> Dict[str, List[str]]:
        """테스트용 이미지 데이터셋 생성"""
        dataset = {
            "valid": [],
            "invalid": []
        }

        # 유효한 이미지들 생성
        damage_types = ["normal", "crack", "bird_drop", "dusty", "snow"]

        for i, damage_type in enumerate(damage_types):
            for j in range(3):  # 각 타입별 3개씩
                filename = f"panel_{damage_type}_{j+1}.jpg"
                filepath = self.valid_path / filename

                self.generate_solar_panel_image(
                    width=800 + j*100,  # 크기 다양화
                    height=600 + j*75,
                    damage_type=damage_type,
                    save_path=str(filepath)
                )
                dataset["valid"].append(str(filepath))

        # 무효한 이미지들 생성
        self._create_invalid_images(dataset)

        return dataset

    def _create_invalid_images(self, dataset: Dict[str, List[str]]):
        """무효한 테스트 이미지들 생성"""

        # 1. 너무 작은 이미지
        small_img = Image.new('RGB', (20, 20), color='red')
        small_path = self.invalid_path / "too_small.jpg"
        small_img.save(small_path, format='JPEG')
        dataset["invalid"].append(str(small_path))

        # 2. 손상된 이미지 파일 (텍스트 파일을 .jpg로 저장)
        corrupted_path = self.invalid_path / "corrupted.jpg"
        with open(corrupted_path, 'w') as f:
            f.write("This is not an image file")
        dataset["invalid"].append(str(corrupted_path))

        # 3. 지원하지 않는 형식
        unsupported_path = self.invalid_path / "unsupported.xyz"
        with open(unsupported_path, 'w') as f:
            f.write("Unsupported format")
        dataset["invalid"].append(str(unsupported_path))


def create_mock_s3_url(local_path: str, base_url: str = "http://localhost:8000") -> str:
    """로컬 파일 경로를 Mock S3 URL로 변환"""
    filename = Path(local_path).name
    return f"{base_url}/test-images/{filename}"


def get_test_image_as_bytes(filepath: str) -> bytes:
    """로컬 이미지 파일을 바이트로 읽기"""
    with open(filepath, 'rb') as f:
        return f.read()


# 테스트 이미지 생성 스크립트
if __name__ == "__main__":
    generator = TestImageGenerator()
    dataset = generator.create_test_dataset()

    print("✅ 테스트 이미지 데이터셋 생성 완료!")
    print(f"📁 유효한 이미지: {len(dataset['valid'])}개")
    print(f"📁 무효한 이미지: {len(dataset['invalid'])}개")

    for category, files in dataset.items():
        print(f"\n{category.upper()} 이미지들:")
        for file in files:
            print(f"  - {file}")
