import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ResultProcessor:
    def __init__(self):
        # 클래스별 심각도 정의
        self.severity_levels = {
            'Clean': 0,
            'Bird-drop': 1,
            'Dusty': 1,
            'Snow-Covered': 1,
            'Electrical-damage': 3,  # 심각 - 즉시 조치 필요
            'Physical-Damage': 3  # 심각 - 즉시 조치 필요
        }

        # 클래스별 권장 조치사항
        self.recommendations = {
            'Clean': {
                'action': '정상',
                'priority': 'low',
                'description': '패널 상태가 양호합니다. 정기 점검만 수행하세요.',
                'estimated_cost': 0,
                'urgency': '없음'
            },
            'Bird-drop': {
                'action': '청소',
                'priority': 'medium',
                'description': '조류 배설물로 인한 성능 저하가 예상됩니다. 청소를 권장합니다.',
                'estimated_cost': 40000,
                'urgency': '1주일 내'
            },
            'Dusty': {
                'action': '청소',
                'priority': 'medium',
                'description': '먼지나 오염물질로 인한 성능 저하가 예상됩니다. 청소를 권장합니다.',
                'estimated_cost': 50000,
                'urgency': '1주일 내'
            },
            'Snow-Covered': {
                'action': '제설',
                'priority': 'medium',
                'description': '눈으로 인한 발전량 저하입니다. 안전한 제설 작업이 필요합니다.',
                'estimated_cost': 30000,
                'urgency': '날씨 개선 후'
            },
            'Electrical-damage': {
                'action': '전기 수리',
                'priority': 'high',
                'description': '전기적 손상이 감지되었습니다. 즉시 전문가 점검이 필요합니다.',
                'estimated_cost': 200000,
                'urgency': '즉시'
            },
            'Physical-Damage': {
                'action': '물리적 수리/교체',
                'priority': 'high',
                'description': '물리적 손상이 감지되었습니다. 안전상 즉시 조치가 필요합니다.',
                'estimated_cost': 300000,
                'urgency': '즉시'
            }
        }

    def process_prediction(self, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI 예측 결과를 비즈니스 로직에 맞게 후처리

        Args:
            prediction: 모델의 원시 예측 결과

        Returns:
            Dict: 가공된 최종 결과
        """
        try:
            predicted_class = prediction['predicted_class']
            confidence = prediction['confidence']
            class_probabilities = prediction['class_probabilities']

            # 기본 결과 구성
            result = {
                'predicted_class': predicted_class,
                'confidence': round(confidence, 4),
                'class_probabilities': {
                    k: round(v, 4) for k, v in class_probabilities.items()
                },
                'severity_level': self.severity_levels.get(predicted_class, 0),
                'recommendations': self.recommendations.get(predicted_class, {}),
                'requires_immediate_action': self._requires_immediate_action(predicted_class, confidence),
                'confidence_warning': self._get_confidence_warning(confidence),
                'alternative_possibilities': self._get_alternative_possibilities(class_probabilities, confidence)
            }

            # 특별 처리 로직
            result.update(self._apply_business_rules(prediction))

            logger.info(f"결과 후처리 완료: {predicted_class} (심각도: {result['severity_level']})")
            return result

        except Exception as e:
            logger.error(f"결과 후처리 중 오류: {str(e)}")
            raise e

    def _requires_immediate_action(self, predicted_class: str, confidence: float) -> bool:
        """즉시 조치가 필요한지 판단"""
        # Physical-Damage나 Electrical-damage는 무조건 즉시 조치
        if predicted_class in ['Physical-Damage', 'Electrical-damage']:
            return True

        # 신뢰도가 낮은 경우에도 안전을 위해 재검토 권장
        if confidence < 0.6:
            return True

        return False

    def _get_confidence_warning(self, confidence: float) -> str:
        """신뢰도에 따른 경고 메시지"""
        if confidence < 0.5:
            return "신뢰도가 매우 낮습니다. 전문가 재검토를 강력히 권장합니다."
        elif confidence < 0.7:
            return "신뢰도가 낮습니다. 추가 이미지나 전문가 검토를 권장합니다."
        elif confidence < 0.85:
            return "보통 수준의 신뢰도입니다."
        else:
            return "높은 신뢰도입니다."

    def _get_alternative_possibilities(self, class_probabilities: Dict[str, float], main_confidence: float) -> List[
        Dict]:
        """대안 가능성 분석"""
        # 메인 예측 제외하고 정렬
        alternatives = []

        for class_name, prob in class_probabilities.items():
            if prob > 0.1 and prob < main_confidence:  # 10% 이상의 확률을 가진 대안들
                alternatives.append({
                    'class': class_name,
                    'probability': round(prob, 4),
                    'severity': self.severity_levels.get(class_name, 0)
                })

        # 확률 순으로 정렬
        alternatives.sort(key=lambda x: x['probability'], reverse=True)

        return alternatives[:2]  # 상위 2개만 반환

    def _apply_business_rules(self, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """비즈니스 규칙 적용"""
        predicted_class = prediction['predicted_class']
        confidence = prediction['confidence']
        class_probabilities = prediction['class_probabilities']

        business_rules = {}

        # 규칙 1: Physical/Electrical damage의 False Negative 방지
        physical_prob = class_probabilities.get('Physical-Damage', 0)
        electrical_prob = class_probabilities.get('Electrical-damage', 0)

        if (physical_prob > 0.2 or electrical_prob > 0.2) and predicted_class not in ['Physical-Damage',
                                                                                      'Electrical-damage']:
            business_rules['damage_risk_warning'] = True
            business_rules[
                'damage_risk_message'] = f"손상 가능성이 감지되었습니다. (물리적: {physical_prob:.2f}, 전기적: {electrical_prob:.2f}) 추가 검토를 권장합니다."

        # 규칙 2: 신뢰도가 낮을 때 보수적 접근
        if confidence < 0.6:
            business_rules['conservative_approach'] = True
            business_rules['conservative_message'] = "신뢰도가 낮아 보수적 접근을 권장합니다. 가능한 한 전문가 검토를 받으세요."

        # 규칙 3: Clean vs Dusty vs Bird-drop 구분 어려움 대응
        clean_prob = class_probabilities.get('Clean', 0)
        dusty_prob = class_probabilities.get('Dusty', 0)
        bird_drop_prob = class_probabilities.get('Bird-drop', 0)

        # 청결 관련 클래스들 간 혼동이 있는지 확인
        clean_related_probs = [clean_prob, dusty_prob, bird_drop_prob]
        max_diff = max(clean_related_probs) - min(clean_related_probs)

        if max_diff < 0.3:
            business_rules['cleanliness_ambiguity'] = True
            business_rules['cleanliness_message'] = "청결 상태 판단이 모호합니다. 더 선명한 이미지로 재분석을 권장합니다."

        return business_rules