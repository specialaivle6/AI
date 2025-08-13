"""
API Package - API 라우터 및 엔드포인트

백엔드 연동을 위한 API 라우터 관리 패키지입니다.
향후 다양한 AI 서비스들의 라우터 분리 및 버전 관리를 위해 준비되었습니다.
현재는 main.py에서 직접 엔드포인트를 관리하고 있으며, 서비스 확장 시 이곳에 라우터들을 분리할 예정입니다.

예상 구조:
- damage_analysis.py - 손상 분석 API 라우터
- performance_analysis.py - 성능 분석 API 라우터 (향후)
- maintenance_prediction.py - 유지보수 예측 API 라우터 (향후)
"""

# 향후 API 라우터들이 추가될 예정
__all__ = []
