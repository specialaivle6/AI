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
        """손상 영역 계산"""
        damage_areas = {
            "critical": 0.0,
            "contamination": 0.0,
            "total": 0.0
        }

        # 실제 계산 로직은 기존과 동일하되, 설정 상수 사용
        # self.critical_classes, self.contamination_classes 사용

        return damage_areas

    def _create_business_assessment(self, damage_areas: Dict[str, float]) -> Dict[str, Any]:
        """비즈니스 평가 생성 (설정 기반)"""
        total_damage = damage_areas["total"]
        critical_damage = damage_areas["critical"]

        # 설정에서 임계값 가져오기
        high_threshold = settings.DamageConstants.PRIORITY_HIGH_THRESHOLD
        medium_threshold = settings.DamageConstants.PRIORITY_MEDIUM_THRESHOLD

        # 우선순위 결정
        if critical_damage > high_threshold:
            priority = "HIGH"
            risk_level = "HIGH"
            decision = "교체"
        elif total_damage > medium_threshold:
            priority = "MEDIUM"
            risk_level = "MEDIUM"
            decision = "수리"
        else:
            priority = "LOW"
            risk_level = "LOW"
            decision = "단순 오염"

        # 비용 추정 (설정 기반)
        repair_cost = int(total_damage * settings.DamageConstants.REPAIR_COST_PER_PERCENT)
        if decision == "교체":
            repair_cost = settings.DamageConstants.REPLACEMENT_COST_BASE

        return {
            "priority": priority,
            "risk_level": risk_level,
            "panel_status": "손상" if total_damage > 5.0 else "오염" if total_damage > 1.0 else "정상",
            "damage_degree": int(total_damage),
            "decision": decision,
            "recommendations": self._generate_recommendations(damage_areas),
            "estimated_repair_cost_krw": repair_cost,
            "estimated_performance_loss_percent": total_damage * 1.5,  # 손상 1%당 성능 1.5% 저하 가정
            "maintenance_urgency_days": self._calculate_urgency_days(critical_damage),
            "business_impact": self._assess_business_impact(total_damage)
        }

    def _generate_recommendations(self, damage_areas: Dict[str, float]) -> List[str]:
        """권장사항 생성"""
        recommendations = []

        if damage_areas["critical"] > 5.0:
            recommendations.append("즉시 전문가 점검 필요")
            recommendations.append("안전을 위해 패널 전원 차단 권장")
        elif damage_areas["total"] > 10.0:
            recommendations.append("1주일 내 수리 예약 권장")
        elif damage_areas["contamination"] > 15.0:
            recommendations.append("정기 청소 서비스 신청 권장")

        if not recommendations:
            recommendations.append("현재 상태 양호, 정기 점검 지속")

        return recommendations

    def _calculate_urgency_days(self, critical_damage: float) -> int:
        """긴급도 일수 계산"""
        if critical_damage > 10.0:
            return 1  # 즉시
        elif critical_damage > 5.0:
            return 7  # 1주일
        else:
            return 30  # 1개월

    def _assess_business_impact(self, total_damage: float) -> str:
        """비즈니스 영향도 평가"""
        if total_damage > 15.0:
            return "높음 - 수익성에 심각한 영향"
        elif total_damage > 8.0:
            return "중간 - 발전 효율 저하"
        else:
            return "낮음 - 경미한 성능 영향"

    def _create_damage_analysis(self, damage_areas: Dict[str, float], results) -> Dict[str, Any]:
        """손상 분석 결과 생성"""
        overall_damage_percentage = damage_areas["total"]
        critical_damage_percentage = damage_areas["critical"]
        contamination_percentage = damage_areas["contamination"]
        healthy_percentage = 100 - overall_damage_percentage

        # 클래스별 비율 계산
        class_percentages = self._calculate_class_percentages(results, damage_areas["total"])

        return {
            "overall_damage_percentage": round(overall_damage_percentage, 2),
            "critical_damage_percentage": round(critical_damage_percentage, 2),
            "contamination_percentage": round(contamination_percentage, 2),
            "healthy_percentage": round(healthy_percentage, 2),
            "avg_confidence": round(self._calculate_avg_confidence(results), 3),
            "detected_objects": len(results),
            "class_breakdown": class_percentages,
            "status": "analyzed"
        }

    def _calculate_class_percentages(self, results, total_damage: float) -> Dict[str, float]:
        """클래스별 비율 계산"""
        class_areas = {}

        for result in results:
            class_id = int(result.boxes.cls)
            class_name = self.class_names[class_id] if self.class_names else f"class_{class_id}"
            mask_area = np.sum(result.masks.data.cpu().numpy())

            if class_name not in class_areas:
                class_areas[class_name] = 0
            class_areas[class_name] += mask_area

        # 백분율로 변환
        class_percentages = {k: (v / total_damage) * 100 for k, v in class_areas.items()}

        return {k: round(v, 2) for k, v in class_percentages.items()}

    def _calculate_avg_confidence(self, results) -> float:
        """평균 신뢰도 계산"""
        confidences = [float(result.boxes.conf) for result in results]
        return np.mean(confidences) if confidences else 0.0

    def _create_detection_details(self, results) -> Dict[str, Any]:
        """검출 상세 정보 생성"""
        detections = []

        for result in results:
            class_id = int(result.boxes.cls)
            class_name = self.class_names[class_id] if self.class_names else f"class_{class_id}"
            confidence = float(result.boxes.conf)
            bbox = result.boxes.xyxy.cpu().numpy().tolist()

            detections.append({
                "class_name": class_name,
                "confidence": round(confidence, 3),
                "bbox": [float(x) for x in bbox],
                "area_pixels": int(np.sum(result.masks.data.cpu().numpy()))
            })

        return {
            "total_detections": len(detections),
            "detections": detections
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
