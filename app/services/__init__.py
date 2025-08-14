"""
Services Package - AI 분석 서비스들

태양광 패널 손상 분석과 성능 예측을 위한 AI 서비스들을 포함합니다.
개선된 예외 처리, 설정 관리, 로깅 시스템이 적용되었습니다.
"""

from .damage_analyzer import DamageAnalyzer
from .performance_analyzer import PerformanceAnalyzer

__all__ = [
    "DamageAnalyzer",
    "PerformanceAnalyzer"
]

# 패키지 메타데이터
__version__ = "3.0.0"
__description__ = "Solar Panel AI Analysis Services"

# 서비스 상태 확인 헬퍼 함수
def get_services_status(damage_analyzer=None, performance_analyzer=None):
    """
    모든 AI 서비스의 상태를 확인합니다.

    Args:
        damage_analyzer: DamageAnalyzer 인스턴스
        performance_analyzer: PerformanceAnalyzer 인스턴스

    Returns:
        dict: 서비스별 상태 정보
    """
    return {
        "damage_analyzer": {
            "available": damage_analyzer is not None,
            "loaded": damage_analyzer.is_loaded() if damage_analyzer else False
        },
        "performance_analyzer": {
            "available": performance_analyzer is not None,
            "loaded": performance_analyzer.is_loaded() if performance_analyzer else False
        }
    }
