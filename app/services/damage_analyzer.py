"""
YOLOv8 기반 태양광 패널 손상 분석 서비스
"""

import numpy as np
from ultralytics import YOLO
from PIL import Image
import io
import time
from pathlib import Path
import asyncio
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class DamageAnalyzer:
    """YOLOv8 기반 태양광 패널 손상 분석기"""

    def __init__(self):
        self.model = None
        self.class_names = None
        self.is_model_loaded = False

        # 손상 심각도 분류
        self.critical_classes = ['Physical-Damage', 'Electrical-Damage']
        self.contamination_classes = ['Bird-drop', 'Dusty', 'Snow']

        # 모델 경로 설정 (실제 경로로 수정 필요)
        self.model_path = "models/yolov8_seg_0812_v0.1.pt"  # YOLOv8 모델 경로

    async def initialize(self):
        """모델 초기화 및 로딩"""
        try:
            logger.info(f"YOLOv8 모델 로딩 시작: {self.model_path}")

            # 모델 파일 존재 확인
            if not Path(self.model_path).exists():
                logger.error(f"모델 파일이 없습니다: {self.model_path}")
                logger.error("커스텀 모델을 models/ 폴더에 배치해주세요.")
                self.is_model_loaded = False
                return  # 모델 다운로드 없이 종료

            # 비동기적으로 모델 로드
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._load_model)

            self.is_model_loaded = True
            logger.info("✅ YOLOv8 모델 로딩 완료")
            logger.info(f"지원 클래스: {list(self.class_names.values()) if self.class_names else 'Unknown'}")

        except Exception as e:
            logger.error(f"모델 로딩 실패: {str(e)}")
            self.is_model_loaded = False

    def _load_model(self):
        """실제 모델 로딩 (동기)"""
        self.model = YOLO(self.model_path)
        self.class_names = self.model.names

    def is_loaded(self) -> bool:
        """모델 로딩 상태 확인"""
        return self.is_model_loaded and self.model is not None

    async def analyze_damage(self, image_bytes: bytes, filename: str = "image") -> Dict[str, Any]:
        """
        패널 이미지 손상 분석

        Args:
            image_bytes: 이미지 바이트 데이터
            filename: 파일명

        Returns:
            Dict: 상세한 손상 분석 결과
        """
        if not self.is_loaded():
            raise RuntimeError("모델이 로딩되지 않았습니다.")

        start_time = time.time()

        try:
            # 이미지 전처리
            image = Image.open(io.BytesIO(image_bytes))
            logger.info(f"🔍 손상 분석 시작: {filename}")

            # YOLOv8 예측 실행 (비동기)
            results = await asyncio.get_event_loop().run_in_executor(
                None, self._predict, image
            )

            result = results[0]

            # 손상 비율 계산
            damage_analysis = self._calculate_comprehensive_damage(result)

            # 비즈니스 평가
            business_assessment = self._generate_business_assessment(damage_analysis)

            # 처리 시간 계산
            processing_time = time.time() - start_time

            # 최종 결과 구성
            final_result = {
                'image_info': {
                    'filename': filename,
                    'size': f"{result.orig_shape[1]}x{result.orig_shape[0]}",
                    'processing_time_seconds': round(processing_time, 2)
                },
                'damage_analysis': damage_analysis,
                'business_assessment': business_assessment,
                'detection_details': self._get_detection_details(result),
                'confidence_score': damage_analysis.get('avg_confidence', 0.0),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }

            logger.info(f"✅ 손상 분석 완료 ({processing_time:.2f}초)")
            logger.info(f"📊 전체 손상률: {damage_analysis['overall_damage_percentage']:.2f}%")

            return final_result

        except Exception as e:
            logger.error(f"손상 분석 중 오류: {str(e)}")
            raise

    def _predict(self, image: Image.Image):
        """YOLOv8 예측 실행 (동기)"""
        return self.model.predict(image, verbose=False, conf=0.25)

    def _calculate_comprehensive_damage(self, result) -> Dict[str, Any]:
        """포괄적인 손상 비율 계산"""

        if result.masks is None or len(result.masks) == 0:
            return {
                'overall_damage_percentage': 0.0,
                'critical_damage_percentage': 0.0,
                'contamination_percentage': 0.0,
                'healthy_percentage': 100.0,
                'avg_confidence': 0.0,
                'detected_objects': 0,
                'class_breakdown': {},
                'status': 'no_detection'
            }

        # 이미지 크기
        img_height, img_width = result.orig_shape
        total_img_area = img_width * img_height

        # 영역별 면적 계산
        total_panel_area = 0
        defective_area = 0
        healthy_area = 0
        critical_damage_area = 0
        contamination_area = 0

        class_areas = {}
        confidences = []

        # 각 검출된 객체 분석
        for i, mask in enumerate(result.masks.data):
            mask_np = mask.cpu().numpy()
            mask_area = np.sum(mask_np)

            class_id = int(result.boxes.cls[i])
            class_name = self.class_names[class_id] if self.class_names else f"class_{class_id}"
            confidence = float(result.boxes.conf[i])

            confidences.append(confidence)

            # 클래스별 면적 누적
            if class_name not in class_areas:
                class_areas[class_name] = 0
            class_areas[class_name] += mask_area

            # 카테고리별 면적 분류
            if class_name == 'Defective':
                defective_area += mask_area
                total_panel_area += mask_area
            elif class_name == 'Non-Defective':
                healthy_area += mask_area
                total_panel_area += mask_area
            elif class_name in self.critical_classes:
                critical_damage_area += mask_area
                defective_area += mask_area
                total_panel_area += mask_area
            elif class_name in self.contamination_classes:
                contamination_area += mask_area
                defective_area += mask_area
                total_panel_area += mask_area

        # 백분율 계산
        if total_panel_area > 0:
            overall_damage_percentage = (defective_area / total_panel_area) * 100
            critical_damage_percentage = (critical_damage_area / total_panel_area) * 100
            contamination_percentage = (contamination_area / total_panel_area) * 100
            healthy_percentage = (healthy_area / total_panel_area) * 100
        else:
            # 패널이 검출되지 않은 경우
            overall_damage_percentage = 0.0
            critical_damage_percentage = 0.0
            contamination_percentage = 0.0
            healthy_percentage = 0.0

        # 클래스별 백분율 계산
        class_percentages = {}
        for class_name, area in class_areas.items():
            if total_panel_area > 0:
                class_percentages[class_name] = (area / total_panel_area) * 100
            else:
                class_percentages[class_name] = 0.0

        return {
            'overall_damage_percentage': round(overall_damage_percentage, 2),
            'critical_damage_percentage': round(critical_damage_percentage, 2),
            'contamination_percentage': round(contamination_percentage, 2),
            'healthy_percentage': round(healthy_percentage, 2),
            'avg_confidence': round(np.mean(confidences) if confidences else 0.0, 3),
            'detected_objects': len(result.masks.data),
            'class_breakdown': {k: round(v, 2) for k, v in class_percentages.items()},
            'status': 'analyzed'
        }

    def _generate_business_assessment(self, damage_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """비즈니스 평가 및 권장사항 생성"""

        overall_damage = damage_analysis['overall_damage_percentage']
        critical_damage = damage_analysis['critical_damage_percentage']
        contamination = damage_analysis['contamination_percentage']

        # 우선순위 계산
        if critical_damage > 10:
            priority = "URGENT"
            risk_level = "HIGH"
        elif critical_damage > 5 or overall_damage > 30:
            priority = "HIGH"
            risk_level = "MEDIUM"
        elif overall_damage > 15:
            priority = "MEDIUM"
            risk_level = "LOW"
        else:
            priority = "LOW"
            risk_level = "MINIMAL"

        # PanelImageReport 테이블용 패널 상태 결정
        panel_status = self._determine_panel_status(critical_damage, contamination, overall_damage)

        # 손상 정도 (0-100 점수)
        damage_degree = self._calculate_damage_degree(critical_damage, overall_damage)

        # 조치 결정
        decision = self._determine_decision(critical_damage, contamination, overall_damage)

        # 권장 조치사항
        recommendations = []
        estimated_cost = 0

        if critical_damage > 0:
            recommendations.append("즉시 전문가 점검 필요")
            recommendations.append("해당 패널 가동 중단 권장")
            estimated_cost += critical_damage * 1000  # 임시 비용 계산

        if contamination > 10:
            recommendations.append("패널 청소 필요")
            estimated_cost += contamination * 50

        if overall_damage < 5:
            recommendations.append("정상 상태 - 정기 점검 유지")

        # 예상 성능 저하율
        performance_loss = min(overall_damage * 0.8, 95)  # 최대 95% 손실

        return {
            'priority': priority,
            'risk_level': risk_level,
            'recommendations': recommendations,
            'estimated_repair_cost_krw': int(estimated_cost),
            'estimated_performance_loss_percent': round(performance_loss, 1),
            'maintenance_urgency_days': self._calculate_maintenance_urgency(critical_damage, overall_damage),
            'business_impact': self._assess_business_impact(overall_damage, critical_damage),
            # PanelImageReport 테이블 매핑용 필드들
            'panel_status': panel_status,
            'damage_degree': damage_degree,
            'decision': decision
        }

    def _determine_panel_status(self, critical_damage: float, contamination: float, overall_damage: float) -> str:
        """패널 상태 결정 (DB용)"""
        if critical_damage > 5:
            return "손상"
        elif contamination > 10 or overall_damage > 15:
            return "오염"
        else:
            return "정상"

    def _calculate_damage_degree(self, critical_damage: float, overall_damage: float) -> int:
        """손상 정도 계산 (0-100 점수)"""
        # 심각한 손상에 더 큰 가중치 부여
        weighted_damage = critical_damage * 2 + overall_damage
        # 0-100 범위로 정규화
        damage_score = min(int(weighted_damage), 100)
        return damage_score

    def _determine_decision(self, critical_damage: float, contamination: float, overall_damage: float) -> str:
        """조치 결정 (DB용)"""
        if critical_damage > 15:
            return "교체"
        elif critical_damage > 5:
            return "수리"
        elif contamination > 10 or overall_damage > 15:
            return "단순 오염"
        else:
            return "단순 오염"  # 기본값

    def _calculate_maintenance_urgency(self, critical_damage: float, overall_damage: float) -> int:
        """유지보수 긴급도 계산 (일 단위)"""
        if critical_damage > 10:
            return 1  # 즉시
        elif critical_damage > 5:
            return 7  # 1주일 이내
        elif overall_damage > 30:
            return 30  # 1달 이내
        elif overall_damage > 15:
            return 90  # 3달 이내
        else:
            return 365  # 1년 이내

    def _assess_business_impact(self, overall_damage: float, critical_damage: float) -> str:
        """비즈니스 영향도 평가"""
        if critical_damage > 15:
            return "심각한 수익 손실 예상 - 즉시 조치 필요"
        elif overall_damage > 40:
            return "상당한 성능 저하 - 신속한 대응 필요"
        elif overall_damage > 20:
            return "경미한 성능 영향 - 계획적 유지보수 권장"
        else:
            return "정상 운영 중 - 예방적 유지보수 유지"

    def _get_detection_details(self, result) -> Dict[str, Any]:
        """검출 상세 정보"""
        if result.masks is None or len(result.masks) == 0:
            return {
                'total_detections': 0,
                'detections': []
            }

        detections = []
        for i in range(len(result.masks.data)):
            class_id = int(result.boxes.cls[i])
            class_name = self.class_names[class_id] if self.class_names else f"class_{class_id}"
            confidence = float(result.boxes.conf[i])
            box = result.boxes.xyxy[i].cpu().numpy()

            detections.append({
                'class_name': class_name,
                'confidence': round(confidence, 3),
                'bbox': [float(x) for x in box],
                'area_pixels': int(np.sum(result.masks.data[i].cpu().numpy()))
            })

        return {
            'total_detections': len(detections),
            'detections': detections
        }

    def generate_batch_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """일괄 분석 결과 요약"""
        if not results:
            return {'error': '분석된 결과가 없습니다.'}

        total_files = len(results)
        total_damage = sum(r['damage_analysis']['overall_damage_percentage'] for r in results)
        critical_files = sum(1 for r in results if r['damage_analysis']['critical_damage_percentage'] > 5)

        avg_damage = total_damage / total_files if total_files > 0 else 0

        priority_distribution = {}
        for result in results:
            priority = result['business_assessment']['priority']
            priority_distribution[priority] = priority_distribution.get(priority, 0) + 1

        return {
            'total_analyzed_files': total_files,
            'average_damage_percentage': round(avg_damage, 2),
            'critical_panels_count': critical_files,
            'critical_panels_percentage': round((critical_files / total_files) * 100, 1),
            'priority_distribution': priority_distribution,
            'overall_fleet_status': self._assess_fleet_status(avg_damage, critical_files, total_files),
            'recommended_action': self._recommend_fleet_action(avg_damage, critical_files, total_files)
        }

    def _assess_fleet_status(self, avg_damage: float, critical_count: int, total_count: int) -> str:
        """전체 패널 상태 평가"""
        critical_ratio = critical_count / total_count if total_count > 0 else 0

        if critical_ratio > 0.3 or avg_damage > 40:
            return "CRITICAL"
        elif critical_ratio > 0.1 or avg_damage > 25:
            return "NEEDS_ATTENTION"
        elif avg_damage > 10:
            return "FAIR"
        else:
            return "GOOD"

    def _recommend_fleet_action(self, avg_damage: float, critical_count: int, total_count: int) -> str:
        """전체 패널 권장 조치"""
        critical_ratio = critical_count / total_count if total_count > 0 else 0

        if critical_ratio > 0.3:
            return "즉시 전면적인 점검 및 수리 필요"
        elif critical_ratio > 0.1:
            return "우선순위 기반 단계적 수리 권장"
        elif avg_damage > 15:
            return "정기 청소 및 예방적 유지보수 강화"
        else:
            return "현재 유지보수 수준 유지"
