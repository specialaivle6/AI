"""
Core Package - 핵심 설정 및 구성

백엔드 연동을 위한 AI 서비스 설정 관리를 담당합니다.
S3 연동, 모델 설정, API 설정 등을 포함합니다.
"""

from .config import Settings, settings

__all__ = ["Settings", "settings"]
