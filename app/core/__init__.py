"""
Core Package - 핵심 시스템 구성 요소

설정 관리, 예외 처리, 로깅 시스템 등 애플리케이션의 핵심 인프라를 제공합니다.
모든 모듈에서 공통으로 사용되는 기반 클래스와 유틸리티를 포함합니다.
"""

from .config import (
    # 설정 관리
    settings,
    create_directories,
    get_model_info,
    validate_settings
)

from .exceptions import (
    # 기본 예외
    AIServiceException,

    # 모델 관련 예외
    ModelNotLoadedException,
    ModelLoadFailedException,

    # 이미지 처리 예외
    ImageProcessingException,
    ImageDownloadException,
    ImageValidationException,

    # 분석 관련 예외
    AnalysisException,
    DamageAnalysisException,
    PerformanceAnalysisException,

    # 기타 예외
    ReportGenerationException,
    ConfigurationException,
    ResourceException,
    TimeoutException,

    # 유틸리티
    get_http_status_code,
    EXCEPTION_STATUS_MAPPING
)

from .logging_config import (
    # 로깅 설정
    setup_logging,
    get_logger,

    # 로깅 유틸리티
    log_performance,
    log_api_request,
    log_model_status,
    log_analysis_result,

    # 믹스인 클래스
    LoggerMixin
)

__all__ = [
    # 설정 관리
    "settings",
    "create_directories",
    "get_model_info",
    "validate_settings",

    # 예외 클래스
    "AIServiceException",
    "ModelNotLoadedException",
    "ModelLoadFailedException",
    "ImageProcessingException",
    "ImageDownloadException",
    "ImageValidationException",
    "AnalysisException",
    "DamageAnalysisException",
    "PerformanceAnalysisException",
    "ReportGenerationException",
    "ConfigurationException",
    "ResourceException",
    "TimeoutException",
    "get_http_status_code",
    "EXCEPTION_STATUS_MAPPING",

    # 로깅
    "setup_logging",
    "get_logger",
    "log_performance",
    "log_api_request",
    "log_model_status",
    "log_analysis_result",
    "LoggerMixin"
]

# 패키지 메타데이터
__version__ = "3.0.0"
__description__ = "Solar Panel AI Service Core Components"

# 패키지 초기화
def initialize_core():
    """핵심 시스템 초기화"""
    # 디렉토리 생성
    create_directories()

    # 로깅 시스템 초기화
    setup_logging()

    # 설정 검증
    issues = validate_settings()
    if issues:
        logger = get_logger(__name__)
        logger.warning("설정 검증에서 문제가 발견되었습니다:")
        for issue in issues:
            logger.warning(f"  - {issue}")

# 자동 초기화 (옵션)
# initialize_core()
