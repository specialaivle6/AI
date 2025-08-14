"""
커스텀 예외 클래스 정의
AI 서비스의 다양한 에러 상황을 세분화하여 관리
"""

from typing import Optional, Dict, Any


class AIServiceException(Exception):
    """AI 서비스 기본 예외 클래스"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ModelNotLoadedException(AIServiceException):
    """AI 모델이 로드되지 않았을 때 발생하는 예외"""

    def __init__(self, model_name: str, model_path: str):
        message = f"{model_name} 모델이 로드되지 않았습니다"
        details = {"model_path": model_path}
        super().__init__(message, "MODEL_NOT_LOADED", details)


class ModelLoadFailedException(AIServiceException):
    """AI 모델 로딩 실패 시 발생하는 예외"""

    def __init__(self, model_name: str, model_path: str, reason: str):
        message = f"{model_name} 모델 로딩 실패: {reason}"
        details = {"model_path": model_path, "reason": reason}
        super().__init__(message, "MODEL_LOAD_FAILED", details)


class ImageProcessingException(AIServiceException):
    """이미지 처리 관련 예외"""

    def __init__(self, message: str, image_info: Optional[Dict[str, Any]] = None):
        details = {"image_info": image_info} if image_info else {}
        super().__init__(message, "IMAGE_PROCESSING_ERROR", details)


class ImageDownloadException(ImageProcessingException):
    """이미지 다운로드 실패 예외"""

    def __init__(self, url: str, reason: str):
        message = f"이미지 다운로드 실패: {reason}"
        details = {"url": url, "reason": reason}
        super().__init__(message, details)


class ImageValidationException(ImageProcessingException):
    """이미지 검증 실패 예외"""

    def __init__(self, reason: str, file_info: Optional[Dict[str, Any]] = None):
        message = f"이미지 검증 실패: {reason}"
        super().__init__(message, file_info)


class AnalysisException(AIServiceException):
    """AI 분석 관련 예외"""

    def __init__(self, analysis_type: str, message: str, input_info: Optional[Dict[str, Any]] = None):
        full_message = f"{analysis_type} 분석 실패: {message}"
        details = {"analysis_type": analysis_type, "input_info": input_info}
        super().__init__(full_message, "ANALYSIS_FAILED", details)


class DamageAnalysisException(AnalysisException):
    """손상 분석 실패 예외"""

    def __init__(self, message: str, panel_id: Optional[int] = None):
        input_info = {"panel_id": panel_id} if panel_id else None
        super().__init__("손상", message, input_info)


class PerformanceAnalysisException(AnalysisException):
    """성능 예측 분석 실패 예외"""

    def __init__(self, message: str, user_id: Optional[str] = None):
        input_info = {"user_id": user_id} if user_id else None
        super().__init__("성능 예측", message, input_info)


class ReportGenerationException(AIServiceException):
    """리포트 생성 실패 예외"""

    def __init__(self, message: str, report_type: str = "PDF"):
        full_message = f"{report_type} 리포트 생성 실패: {message}"
        details = {"report_type": report_type}
        super().__init__(full_message, "REPORT_GENERATION_FAILED", details)


class ConfigurationException(AIServiceException):
    """설정 관련 예외"""

    def __init__(self, message: str, config_key: Optional[str] = None):
        details = {"config_key": config_key} if config_key else {}
        super().__init__(message, "CONFIGURATION_ERROR", details)


class ResourceException(AIServiceException):
    """리소스 관련 예외 (메모리, 디스크 등)"""

    def __init__(self, resource_type: str, message: str):
        full_message = f"{resource_type} 리소스 오류: {message}"
        details = {"resource_type": resource_type}
        super().__init__(full_message, "RESOURCE_ERROR", details)


class TimeoutException(AIServiceException):
    """타임아웃 예외"""

    def __init__(self, operation: str, timeout_seconds: int):
        message = f"{operation} 작업이 {timeout_seconds}초 제한시간을 초과했습니다"
        details = {"operation": operation, "timeout_seconds": timeout_seconds}
        super().__init__(message, "TIMEOUT_ERROR", details)


# 예외를 HTTP 상태 코드로 매핑
EXCEPTION_STATUS_MAPPING = {
    ModelNotLoadedException: 503,  # Service Unavailable
    ModelLoadFailedException: 503,  # Service Unavailable
    ImageDownloadException: 400,   # Bad Request
    ImageValidationException: 400, # Bad Request
    DamageAnalysisException: 500,  # Internal Server Error
    PerformanceAnalysisException: 500,  # Internal Server Error
    ReportGenerationException: 500,  # Internal Server Error
    ConfigurationException: 500,   # Internal Server Error
    ResourceException: 503,        # Service Unavailable
    TimeoutException: 504,         # Gateway Timeout
}


def get_http_status_code(exception: Exception) -> int:
    """예외 타입에 따른 HTTP 상태 코드 반환"""
    return EXCEPTION_STATUS_MAPPING.get(type(exception), 500)
