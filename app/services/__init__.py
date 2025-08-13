"""
Services Package - AI 분석 서비스들

백엔드 연동을 위한 순수 AI 분석 서비스들을 포함합니다.
YOLOv8 기반 손상 분석에 집중하며, DB 연동은 백엔드에서 처리합니다.
"""

from .damage_analyzer import DamageAnalyzer

__all__ = ["DamageAnalyzer"]
