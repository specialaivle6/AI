"""
API Package - API 라우터 및 엔드포인트

태양광 패널 AI 서비스를 위한 API 라우터 관리 패키지입니다.
현재는 main.py에서 직접 엔드포인트를 관리하고 있으며, 향후 서비스 확장 시
개별 라우터로 분리하여 관리할 예정입니다.

향후 예상 구조:
- damage_routes.py - 손상 분석 API 라우터
- performance_routes.py - 성능 예측 API 라우터
- health_routes.py - 헬스체크 API 라우터
- admin_routes.py - 관리용 API 라우터
"""

# 현재는 main.py에서 직접 관리하므로 비어있음
__all__ = []

# 패키지 메타데이터
__version__ = "3.0.0"
__description__ = "Solar Panel AI Service API Routes"

# API 버전 관리
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# 향후 라우터 분리 시 사용할 공통 설정
ROUTER_CONFIG = {
    "damage_analysis": {
        "prefix": f"{API_PREFIX}/damage-analysis",
        "tags": ["Damage Analysis"],
        "dependencies": []
    },
    "performance_analysis": {
        "prefix": f"{API_PREFIX}/performance-analysis",
        "tags": ["Performance Analysis"],
        "dependencies": []
    },
    "health": {
        "prefix": "/health",
        "tags": ["Health Check"],
        "dependencies": []
    }
}
