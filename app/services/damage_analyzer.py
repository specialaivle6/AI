"""
YOLOv8 기반 태양광 패널 손상 분석 서비스
개선된 설정 시스템과 예외 처리 적용
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

# 개선된 임포트
from app.core.config import settings
from app.core.exceptions import (
    ModelLoadFailedException, DamageAnalysisException,
    ImageProcessingException, TimeoutException
)
from app.core.logging_config import get_logger, log_analysis_result, log_performance

logger = get_logger(__name__)


class DamageAnalyzer:
    """YOLOv8 기반 태양광 패널 손상 분석기"""

    def __init__(self):
        self.model = None
        self.class_names = None
        self.is_model_loaded = False

        # 설정에서 상수 가져오기
        self.critical_classes = settings.DamageConstants.CRITICAL_CLASSES
        self.contamination_classes = settings.DamageConstants.CONTAMINATION_CLASSES
        self.model_path = settings.damage_model_path

    async def initialize(self):
        """모델 초기화 및 로딩"""
        try:
            logger.info(f"YOLOv8 모델 로딩 시작: {self.model_path}")

            # 모델 파일 존재 확인
            if not Path(self.model_path).exists():
                raise ModelLoadFailedException(
                    "YOLOv8",
                    self.model_path,
                    "모델 파일이 존재하지 않습니다"
                )

            # 비동기적으로 모델 로드
            loop = asyncio.get_event_loop()
            await asyncio.wait_for(
                loop.run_in_executor(None, self._load_model),
                timeout=settings.image_processing_timeout
            )

            self.is_model_loaded = True
            logger.info("✅ YOLOv8 모델 로딩 완료")
            logger.info(f"지원 클래스: {list(self.class_names.values()) if self.class_names else 'Unknown'}")

        except asyncio.TimeoutError:
            raise TimeoutException("모델 로딩", settings.image_processing_timeout)
        except Exception as e:
            logger.error(f"YOLOv8 모델 로딩 실패: {str(e)}")
            raise ModelLoadFailedException("YOLOv8", self.model_path, str(e))

    def _load_model(self):
        """실제 모델 로딩 (동기 함수)"""
        try:
            self.model = YOLO(self.model_path)
            self.class_names = self.model.names
            logger.info(f"모델 클래스 수: {len(self.class_names)}")
        except Exception as e:
            raise Exception(f"YOLO 모델 로드 실패: {str(e)}")

    def is_loaded(self) -> bool:
        """모델 로딩 상태 확인"""
        return self.is_model_loaded and self.model is not None

    async def analyze_damage(self, image_data: bytes) -> Dict[str, Any]:
        """
        이미지 데이터를 받아서 손상 분석 수행

        Args:
            image_data: 이미지 바이트 데이터

        Returns:
            Dict: 분석 결과
        """
        start_time = time.time()

        if not self.is_loaded():
            raise DamageAnalysisException("모델이 로드되지 않았습니다")

        try:
            # 이미지 전처리
            try:
                image = Image.open(io.BytesIO(image_data))
                if image.mode != 'RGB':
                    image = image.convert('RGB')
            except Exception as e:
                raise ImageProcessingException(f"이미지 변환 실패: {str(e)}")

            # YOLOv8 추론 수행
            try:
                loop = asyncio.get_event_loop()
                results = await asyncio.wait_for(
                    loop.run_in_executor(None, self._run_inference, image),
                    timeout=settings.image_processing_timeout
                )
            except asyncio.TimeoutError:
                raise TimeoutException("이미지 분석", settings.image_processing_timeout)

            # 결과 분석 및 비즈니스 로직 적용
            analysis_result = self._analyze_results(results, image.size)

            processing_time = time.time() - start_time

            # 로깅
            log_analysis_result(
                "Damage Analysis",
                True,
                processing_time,
                detected_objects=analysis_result["damage_analysis"]["detected_objects"],
                overall_damage=f"{analysis_result['damage_analysis']['overall_damage_percentage']:.1f}%"
            )

            return analysis_result

        except (DamageAnalysisException, ImageProcessingException, TimeoutException):
            raise
        except Exception as e:
            processing_time = time.time() - start_time
            log_analysis_result("Damage Analysis", False, processing_time, error=str(e))
            raise DamageAnalysisException(f"분석 처리 중 오류: {str(e)}")

    def _run_inference(self, image: Image.Image) -> List:
        """YOLO 모델 추론 실행"""
        try:
            results = self.model(
                image,
                conf=settings.confidence_threshold,
                iou=settings.iou_threshold,
                max_det=settings.max_detections,
                verbose=False
            )
            return results
        except Exception as e:
            raise Exception(f"YOLO 추론 실패: {str(e)}")

    def _analyze_results(self, results, image_size: tuple) -> Dict[str, Any]:
        """YOLO 결과를 분석하여 비즈니스 로직 적용"""
        try:
            # 이미지 크기
            total_image_area = image_size[0] * image_size[1]

            # 손상 분류 및 비율 계산
            damage_areas = self._calculate_damage_areas(results, total_image_area)

            # 비즈니스 평가
            business_assessment = self._create_business_assessment(damage_areas)

            # 응답 구성
            return {
                "damage_analysis": self._create_damage_analysis(damage_areas, results),
                "business_assessment": business_assessment,
                "detection_details": self._create_detection_details(results),
                "confidence_score": self._calculate_avg_confidence(results)
            }

        except Exception as e:
            raise Exception(f"결과 분석 실패: {str(e)}")

    def _calculate_damage_areas(self, results, total_area: int) -> Dict[str, float]:
        """손상 영역 계산 - 패널 영역 기준으로 개선된 계산"""
        damage_areas = {
            "critical": 0.0,
            "contamination": 0.0,
            "total": 0.0
        }

        if not results or len(results) == 0:
            return damage_areas

        # 첫 번째 결과 사용 (보통 단일 이미지 처리)
        result = results[0]

        # 감지된 객체가 없으면 빈 결과 반환
        if result.boxes is None or len(result.boxes) == 0:
            return damage_areas

        # 세그멘테이션 마스크가 없으면 바운딩 박스 기반 계산
        if result.masks is None or len(result.masks) == 0:
            return self._calculate_damage_from_boxes(result, total_area)

        # 마스크 기반 정확한 계산 (Previous 버전 방식 적용)
        return self._calculate_damage_from_masks(result)

    def _calculate_damage_from_boxes(self, result, total_area: int) -> Dict[str, float]:
        """바운딩 박스 기반 손상 영역 계산 (기존 방식)"""
        damage_areas = {
            "critical": 0.0,
            "contamination": 0.0,
            "total": 0.0
        }

        boxes = result.boxes.xyxy.cpu().numpy()
        classes = result.boxes.cls.cpu().numpy().astype(int)
        confidences = result.boxes.conf.cpu().numpy()

        critical_area = 0.0
        contamination_area = 0.0
        total_damage_area = 0.0

        for i, (box, cls_id, conf) in enumerate(zip(boxes, classes, confidences)):
            if conf < settings.confidence_threshold:
                continue

            class_name = self.class_names.get(cls_id, f"class_{cls_id}")

            # 바운딩 박스 영역 계산
            x1, y1, x2, y2 = box
            box_area = (x2 - x1) * (y2 - y1)

            # 클래스별 손상 영역 분류
            if class_name in self.critical_classes:
                critical_area += box_area
                total_damage_area += box_area
            elif class_name in self.contamination_classes:
                contamination_area += box_area
                total_damage_area += box_area
            else:
                total_damage_area += box_area

        # 전체 이미지 대비 비율로 변환 (백분율)
        damage_areas["critical"] = (critical_area / total_area) * 100.0 if total_area > 0 else 0.0
        damage_areas["contamination"] = (contamination_area / total_area) * 100.0 if total_area > 0 else 0.0
        damage_areas["total"] = (total_damage_area / total_area) * 100.0 if total_area > 0 else 0.0

        return damage_areas

    def _calculate_damage_from_masks(self, result) -> Dict[str, float]:
        """마스크 기반 정확한 손상 영역 계산 (Previous 버전 방식 적용)"""
        damage_areas = {
            "critical": 0.0,
            "contamination": 0.0,
            "total": 0.0
        }

        # 영역별 면적 계산
        total_panel_area = 0
        defective_area = 0
        healthy_area = 0
        critical_damage_area = 0
        contamination_area = 0

        # 각 검출된 객체 분석
        for i, mask in enumerate(result.masks.data):
            mask_np = mask.cpu().numpy()
            mask_area = np.sum(mask_np)

            class_id = int(result.boxes.cls[i])
            class_name = self.class_names.get(class_id, f"class_{class_id}")
            confidence = float(result.boxes.conf[i])

            # 신뢰도 임계값 확인
            if confidence < settings.confidence_threshold:
                continue

            # 카테고리별 면적 분류 (Previous 버전 로직)
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

        # 패널 영역 기준으로 백분율 계산 (Previous 버전 방식)
        if total_panel_area > 0:
            damage_areas["critical"] = (critical_damage_area / total_panel_area) * 100.0
            damage_areas["contamination"] = (contamination_area / total_panel_area) * 100.0
            damage_areas["total"] = (defective_area / total_panel_area) * 100.0
        else:
            # 패널이 검출되지 않은 경우는 0%로 처리
            damage_areas = {"critical": 0.0, "contamination": 0.0, "total": 0.0}

        logger.info(f"손상 영역 계산 완료 (패널 기준) - Critical: {damage_areas['critical']:.2f}%, "
                    f"Contamination: {damage_areas['contamination']:.2f}%, "
                    f"Total: {damage_areas['total']:.2f}%")

        return damage_areas

    def _create_business_assessment(self, damage_areas: Dict[str, float]) -> Dict[str, Any]:
        """비즈니스 평가 생성 (업데이트된 설정 상수 사용)"""
        total_damage = damage_areas["total"]
        critical_damage = damage_areas["critical"]
        contamination = damage_areas["contamination"]

        # 업데이트된 설정 상수를 사용한 우선순위 분류
        if critical_damage > settings.DamageConstants.URGENT_CRITICAL_THRESHOLD:
            priority = "URGENT"
            risk_level = "HIGH"
            decision = "즉시 가동 중단 및 교체"
        elif (critical_damage > settings.DamageConstants.HIGH_CRITICAL_THRESHOLD or
              total_damage > settings.DamageConstants.HIGH_TOTAL_THRESHOLD):
            priority = "HIGH"
            risk_level = "MEDIUM"
            decision = "교체"
        elif total_damage > settings.DamageConstants.MEDIUM_TOTAL_THRESHOLD:
            priority = "MEDIUM"
            risk_level = "LOW"
            decision = "수리"
        else:
            priority = "LOW"
            risk_level = "MINIMAL"
            decision = "정기 점검"

        # 업데이트된 설정을 사용한 현실적인 비용 추정
        estimated_cost = 0
        if critical_damage > 0:
            estimated_cost += critical_damage * settings.DamageConstants.CRITICAL_DAMAGE_COST_PER_PERCENT
        if contamination > 10:
            estimated_cost += contamination * settings.DamageConstants.CONTAMINATION_COST_PER_PERCENT

        # 기본 교체 비용 적용
        if decision == "즉시 가동 중단 및 교체" or decision == "교체":
            estimated_cost = max(estimated_cost, settings.DamageConstants.REPLACEMENT_COST_BASE)

        # 설정 기반 성능 손실 계산
        performance_loss = min(total_damage * settings.DamageConstants.PERFORMANCE_LOSS_RATIO, 95.0)

        return {
            "priority": priority,
            "risk_level": risk_level,
            "status": "심각한 손상" if critical_damage > 10 else "손상" if total_damage > 5.0 else "오염" if total_damage > 1.0 else "정상",
            "panel_status": "심각한 손상" if critical_damage > 10 else "손상" if total_damage > 5.0 else "오염" if total_damage > 1.0 else "정상",
            "damage_degree": int(total_damage),
            "decision": decision,
            "recommendations": self._generate_enhanced_recommendations(damage_areas),
            "estimated_repair_cost_krw": int(estimated_cost),
            "estimated_performance_loss_percent": round(performance_loss, 1),
            "maintenance_urgency_days": self._calculate_enhanced_urgency_days(critical_damage, total_damage),
            "business_impact": self._assess_enhanced_business_impact(total_damage, critical_damage)
        }

    def _generate_enhanced_recommendations(self, damage_areas: Dict[str, float]) -> List[str]:
        """향상된 권장사항 생성 (Previous 버전 로직 적용)"""
        recommendations = []
        critical_damage = damage_areas["critical"]
        total_damage = damage_areas["total"]
        contamination = damage_areas["contamination"]

        # Critical 손상에 대한 권장사항
        if critical_damage > 10.0:
            recommendations.append("즉시 전문가 점검 필요")
            recommendations.append("해당 패널 가동 중단 권장")
            recommendations.append("안전을 위해 패널 전원 차단 권장")
        elif critical_damage > 5.0:
            recommendations.append("즉시 전문가 점검 필요")
            recommendations.append("안전을 위해 패널 전원 차단 권장")

        # 전체 손상에 대한 권장사항
        if total_damage > 30.0:
            recommendations.append("패널 교체 검토 필요")
        elif total_damage > 15.0:
            recommendations.append("1주일 내 수리 예약 권장")

        # 오염에 대한 권장사항
        if contamination > 10.0:
            recommendations.append("패널 청소 필요")

        # 정상 상태
        if total_damage < 5.0:
            recommendations.append("정상 상태 - 정기 점검 유지")

        return recommendations if recommendations else ["현재 상태 양호, 정기 점검 지속"]

    def _calculate_enhanced_urgency_days(self, critical_damage: float, total_damage: float) -> int:
        """향상된 유지보수 긴급도 계산 (Previous 버전 로직)"""
        if critical_damage > 10.0:
            return 1  # 즉시
        elif critical_damage > 5.0:
            return 7  # 1주일 이내
        elif total_damage > 30.0:
            return 30  # 1달 이내
        elif total_damage > 15.0:
            return 90  # 3달 이내
        else:
            return 365  # 1년 이내

    def _assess_enhanced_business_impact(self, total_damage: float, critical_damage: float) -> str:
        """향상된 비즈니스 영향도 평가 (Previous 버전 로직)"""
        if critical_damage > 15.0:
            return "심각한 수익 손실 예상 - 즉시 조치 필요"
        elif total_damage > 40.0:
            return "상당한 성능 저하 - 신속한 대응 필요"
        elif total_damage > 20.0:
            return "경미한 성능 영향 - 계획적 유지보수 권장"
        else:
            return "정상 운영 중 - 예방적 유지보수 유지"

    def _create_damage_analysis(self, damage_areas: Dict[str, float], results) -> Dict[str, Any]:
        """손상 분석 결과 생성"""
        overall_damage_percentage = damage_areas["total"]
        critical_damage_percentage = damage_areas["critical"]
        contamination_percentage = damage_areas["contamination"]
        healthy_percentage = 100 - overall_damage_percentage

        # 클래스별 비율 계산
        class_percentages = self._calculate_class_percentages(results, damage_areas["total"])

        # 실제 감지된 객체 수 계산
        detected_objects_count = 0
        if results and len(results) > 0:
            result = results[0]
            if result.boxes is not None and len(result.boxes) > 0:
                # 신뢰도 임계값 이상인 객체만 카운트
                confidences = result.boxes.conf.cpu().numpy()
                detected_objects_count = int(np.sum(confidences >= settings.confidence_threshold))

        return {
            "overall_damage_percentage": round(overall_damage_percentage, 2),
            "critical_damage_percentage": round(critical_damage_percentage, 2),
            "contamination_percentage": round(contamination_percentage, 2),
            "healthy_percentage": round(healthy_percentage, 2),
            "avg_confidence": round(self._calculate_avg_confidence(results), 3),
            "detected_objects": detected_objects_count,
            "class_breakdown": class_percentages,
            "status": "analyzed"
        }

    def _calculate_class_percentages(self, results, total_damage_area: float) -> Dict[str, float]:
        """클래스별 비율 계산"""
        class_areas = {}

        if not results or len(results) == 0:
            return {}

        result = results[0]

        if result.boxes is None or len(result.boxes) == 0:
            return {}

        boxes = result.boxes.xyxy.cpu().numpy()
        classes = result.boxes.cls.cpu().numpy().astype(int)
        confidences = result.boxes.conf.cpu().numpy()

        for i, (box, cls_id, conf) in enumerate(zip(boxes, classes, confidences)):
            if conf < settings.confidence_threshold:
                continue

            class_name = self.class_names.get(cls_id, f"class_{cls_id}")

            # 바운딩 박스 영역 계산
            x1, y1, x2, y2 = box
            box_area = (x2 - x1) * (y2 - y1)

            # 세그멘테이션 마스크가 있는 경우 더 정확한 영역 계산
            if hasattr(result, 'masks') and result.masks is not None and len(result.masks) > i:
                try:
                    mask = result.masks[i].data.cpu().numpy()
                    if mask.size > 0:
                        mask_area = np.sum(mask > 0.5)
                        box_area = mask_area
                except Exception:
                    pass  # 바운딩 박스 영역 사용

            if class_name not in class_areas:
                class_areas[class_name] = 0
            class_areas[class_name] += box_area

        # 전체 손상 영역 대비 백분율로 변환
        if total_damage_area > 0:
            class_percentages = {k: (v / total_damage_area) * 100 for k, v in class_areas.items()}
        else:
            class_percentages = {k: 0.0 for k in class_areas.keys()}

        return {k: round(v, 2) for k, v in class_percentages.items()}

    def _calculate_avg_confidence(self, results) -> float:
        """평균 신뢰도 계산"""
        if not results or len(results) == 0:
            return 0.0

        result = results[0]

        if result.boxes is None or len(result.boxes) == 0:
            return 0.0

        confidences = result.boxes.conf.cpu().numpy()
        return float(np.mean(confidences)) if len(confidences) > 0 else 0.0

    def _create_detection_details(self, results) -> List[Dict[str, Any]]:
        """검출 상세 정보 생성"""
        detections = []

        if not results or len(results) == 0:
            return []

        result = results[0]

        if result.boxes is None or len(result.boxes) == 0:
            return []

        boxes = result.boxes.xyxy.cpu().numpy()
        classes = result.boxes.cls.cpu().numpy().astype(int)
        confidences = result.boxes.conf.cpu().numpy()

        for i, (box, cls_id, conf) in enumerate(zip(boxes, classes, confidences)):
            if conf < settings.confidence_threshold:
                continue

            class_name = self.class_names.get(cls_id, f"class_{cls_id}")
            bbox = [int(x) for x in box]

            # 영역 계산
            area_pixels = int((box[2] - box[0]) * (box[3] - box[1]))

            # 세그멘테이션 마스크가 있는 경우 더 정확한 영역 계산
            if hasattr(result, 'masks') and result.masks is not None and len(result.masks) > i:
                try:
                    mask = result.masks[i].data.cpu().numpy()
                    if mask.size > 0:
                        area_pixels = int(np.sum(mask > 0.5))
                except Exception:
                    pass  # 바운딩 박스 영역 사용

            detections.append({
                "class_name": class_name,
                "confidence": round(float(conf), 3),
                "bbox": bbox,
                "area_pixels": area_pixels
            })

        return detections

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

    def _generate_recommendations(self, damage_areas: Dict[str, float]) -> List[str]:
        """권장사항 생성 (기존 메소드를 enhanced 버전으로 대체됨)"""
        return self._generate_enhanced_recommendations(damage_areas)

    def _calculate_urgency_days(self, critical_damage: float) -> int:
        """긴급도 일수 계산 (기존 메소드를 enhanced 버전으로 대체됨)"""
        return self._calculate_enhanced_urgency_days(critical_damage, 0.0)

    def _assess_business_impact(self, total_damage: float) -> str:
        """비즈니스 영향도 평가 (기존 메소드를 enhanced 버전으로 대체됨)"""
        return self._assess_enhanced_business_impact(total_damage, 0.0)
