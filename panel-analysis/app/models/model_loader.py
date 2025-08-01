import torch
import torch.nn as nn
from torchvision import models
from pathlib import Path
import logging
from typing import Dict, Any
import asyncio

logger = logging.getLogger(__name__)


class SolarPanelClassifier(nn.Module):
    """학습 시 사용한 것과 동일한 모델 구조"""

    def __init__(self, num_classes=6):
        super(SolarPanelClassifier, self).__init__()

        # MobileNetV3Small 백본 (pretrained)
        self.backbone = models.mobilenet_v3_small(weights='IMAGENET1K_V1')

        # 백본의 classifier를 제거하고 feature extractor만 사용
        self.features = self.backbone.features
        self.avgpool = self.backbone.avgpool

        # 동적으로 feature 크기 계산
        with torch.no_grad():
            dummy_input = torch.randn(1, 3, 224, 224)
            x = self.features(dummy_input)
            x = self.avgpool(x)
            feature_size = x.view(x.size(0), -1).size(1)

        # 백본 고정 (freeze) - 추론 시에는 불필요하지만 구조 일치를 위해 유지
        for param in self.features.parameters():
            param.requires_grad = False
        for param in self.avgpool.parameters():
            param.requires_grad = False

        # 커스텀 분류 헤드
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(0.5),
            nn.Linear(feature_size, num_classes)
        )

    def forward(self, x):
        x = self.features(x)
        x = self.avgpool(x)
        x = self.classifier(x)
        return x


class ModelLoader:
    def __init__(self):
        self.model = None
        self.device = torch.device('cpu')  # CPU 전용
        self.class_names = [
            'Bird-drop',
            'Clean',
            'Dusty',
            'Electrical-damage',
            'Physical-Damage',
            'Snow-Covered'
        ]
        self.model_path = Path("models/mobilenet_v3_small.pth")
        self._loaded = False

    async def load_model(self):
        """모델을 비동기적으로 로딩"""
        try:
            # 커스텀 SolarPanelClassifier 모델 생성
            num_classes = len(self.class_names)
            self.model = SolarPanelClassifier(num_classes=num_classes)

            # 학습된 가중치 로딩
            if self.model_path.exists():
                logger.info(f"모델 파일 로딩 시도: {self.model_path}")
                checkpoint = torch.load(self.model_path, map_location=self.device)

                # 체크포인트 정보 확인
                if isinstance(checkpoint, dict):
                    # 저장된 클래스 이름 확인 (있다면)
                    if 'class_names' in checkpoint:
                        saved_class_names = checkpoint['class_names']
                        logger.info(f"저장된 클래스명: {saved_class_names}")

                        # 클래스명이 다르면 경고
                        if saved_class_names != self.class_names:
                            logger.warning("저장된 클래스명과 현재 클래스명이 다릅니다!")
                            logger.warning(f"저장됨: {saved_class_names}")
                            logger.warning(f"현재: {self.class_names}")
                            # 저장된 클래스명 사용
                            self.class_names = saved_class_names

                    # model_state_dict 키로 저장된 경우
                    if 'model_state_dict' in checkpoint:
                        self.model.load_state_dict(checkpoint['model_state_dict'])
                        logger.info("model_state_dict로부터 가중치 로딩 성공")

                        # 추가 정보 로그
                        if 'val_acc' in checkpoint:
                            logger.info(f"모델 검증 정확도: {checkpoint['val_acc']:.4f}")
                        if 'timestamp' in checkpoint:
                            logger.info(f"모델 학습 일시: {checkpoint['timestamp']}")
                        if 'model_name' in checkpoint:
                            logger.info(f"모델명: {checkpoint['model_name']}")

                    # 직접 state_dict가 저장된 경우
                    else:
                        self.model.load_state_dict(checkpoint)
                        logger.info("state_dict로부터 가중치 로딩 성공")

                else:
                    # 전체 모델 객체가 저장된 경우
                    logger.warning("예상치 못한 저장 형식입니다.")
                    raise ValueError("지원하지 않는 모델 저장 형식입니다.")

            else:
                logger.warning(f"모델 파일을 찾을 수 없습니다: {self.model_path}")
                raise FileNotFoundError(f"모델 파일이 없습니다: {self.model_path}")

            # 평가 모드로 설정
            self.model.eval()
            self.model.to(self.device)

            # 추론 시에는 드롭아웃 비활성화를 위해 명시적으로 설정
            for module in self.model.modules():
                if isinstance(module, nn.Dropout):
                    module.eval()

            self._loaded = True
            logger.info("모델 로딩 성공!")
            logger.info(f"클래스 개수: {len(self.class_names)}")
            logger.info(f"클래스명: {self.class_names}")

        except Exception as e:
            logger.error(f"모델 로딩 실패: {str(e)}")
            raise e

    async def predict(self, image_tensor: torch.Tensor) -> Dict[str, Any]:
        """이미지에 대한 예측 수행"""
        if not self._loaded:
            raise RuntimeError("모델이 로딩되지 않았습니다.")

        try:
            with torch.no_grad():
                # 배치 차원 추가
                if image_tensor.dim() == 3:
                    image_tensor = image_tensor.unsqueeze(0)

                image_tensor = image_tensor.to(self.device)

                # 예측 수행
                outputs = self.model(image_tensor)
                probabilities = torch.nn.functional.softmax(outputs, dim=1)

                # 결과 처리
                confidence, predicted_idx = torch.max(probabilities, 1)
                predicted_class = self.class_names[predicted_idx.item()]

                # 모든 클래스별 확률
                class_probabilities = {
                    class_name: prob.item()
                    for class_name, prob in zip(self.class_names, probabilities[0])
                }

                return {
                    'predicted_class': predicted_class,
                    'confidence': confidence.item(),
                    'class_probabilities': class_probabilities,
                    'predicted_index': predicted_idx.item()
                }

        except Exception as e:
            logger.error(f"예측 중 오류 발생: {str(e)}")
            raise e

    def is_loaded(self) -> bool:
        """모델 로딩 상태 확인"""
        return self._loaded

    def get_class_names(self) -> list:
        """클래스 이름 목록 반환"""
        return self.class_names.copy()