"""
커스텀 예외 클래스 정의 (v3.0 - API 명세서 완전 호환)
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


# === 모델 관련 예외 ===

class ModelNotLoadedException(AIServiceException):
    """AI 모델이 로드되지 않았을 때 발생하는 예외"""

    def __init__(self, ai_model_name: str, model_path: str):
        message = f"{ai_model_name} AI 모델이 로드되지 않았습니다"
        details = {"model_path": model_path, "ai_model_name": ai_model_name}
        super().__init__(message, "MODEL_NOT_LOADED", details)


class ModelLoadFailedException(AIServiceException):
    """AI 모델 로딩 실패 시 발생하는 예외"""

    def __init__(self, ai_model_name: str, model_path: str, reason: str):
        message = f"{ai_model_name} AI 모델 로딩 실패: {reason}"
        details = {"model_path": model_path, "reason": reason, "ai_model_name": ai_model_name}
        super().__init__(message, "MODEL_LOAD_FAILED", details)


# === 이미지 처리 관련 예외 ===

class ImageProcessingException(AIServiceException):
    """이미지 처리 관련 기본 예외"""

    def __init__(self, message: str, error_code: str, image_info: Optional[Dict[str, Any]] = None):
        details = {"image_info": image_info} if image_info else {}
        super().__init__(message, error_code, details)


class InvalidImageUrlException(ImageProcessingException):
    """잘못된 이미지 URL 형식 예외 (API 명세서 대응)"""

    def __init__(self, url: str, reason: str = "URL 형식이 올바르지 않습니다"):
        message = f"잘못된 이미지 URL: {reason}"
        image_info = {"url": url, "reason": reason}
        super().__init__(message, "INVALID_IMAGE_URL", image_info)


class ImageDownloadException(ImageProcessingException):
    """이미지 다운로드 실패 예외"""

    def __init__(self, url: str, reason: str):
        message = f"이미지 다운로드 실패: {reason}"
        image_info = {"url": url, "reason": reason}
        super().__init__(message, "IMAGE_DOWNLOAD_FAILED", image_info)


class ImageValidationException(ImageProcessingException):
    """이미지 검증 실패 예외"""

    def __init__(self, reason: str, file_info: Optional[Dict[str, Any]] = None):
        message = f"이미지 검증 실패: {reason}"
        super().__init__(message, "INVALID_IMAGE_FORMAT", file_info)


class ImageTooLargeException(ImageProcessingException):
    """이미지 크기 초과 예외 (API 명세서 대응)"""

    def __init__(self, file_size: int, max_size: int = 20971520):  # 20MB
        message = f"이미지 크기가 너무 큽니다: {file_size}bytes (최대: {max_size}bytes)"
        image_info = {"file_size": file_size, "max_size": max_size}
        super().__init__(message, "IMAGE_TOO_LARGE", image_info)


# === 입력 검증 관련 예외 ===

class ValidationException(AIServiceException):
    """입력 데이터 검증 실패 예외 (API 명세서 대응)"""

    def __init__(self, field_name: str, value: Any, reason: str):
        message = f"입력 검증 실패 - {field_name}: {reason}"
        details = {"field": field_name, "value": str(value), "reason": reason}
        super().__init__(message, "VALIDATION_ERROR", details)


# === 분석 관련 예외 ===

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


# === 리포트 생성 관련 예외 ===

class ReportGenerationException(AIServiceException):
    """리포트 생성 실패 예외"""

    def __init__(self, message: str, report_type: str = "PDF"):
        full_message = f"{report_type} 리포트 생성 실패: {message}"
        details = {"report_type": report_type}
        super().__init__(full_message, "REPORT_GENERATION_FAILED", details)


# === 시스템 관련 예외 ===

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


class ServiceUnavailableException(AIServiceException):
    """서비스 일시 중단 예외 (API 명세서 대응)"""

    def __init__(self, service_name: str, reason: str):
        message = f"{service_name} 서비스가 일시적으로 사용할 수 없습니다: {reason}"
        details = {"service_name": service_name, "reason": reason}
        super().__init__(message, "SERVICE_UNAVAILABLE", details)


# === HTTP 상태 코드 매핑 (API 명세서와 일치) ===

EXCEPTION_STATUS_MAPPING = {
    # 400 Bad Request
    InvalidImageUrlException: 400,
    ImageDownloadException: 400,
    ImageValidationException: 400,
    ImageTooLargeException: 400,

    # 422 Unprocessable Entity
    ValidationException: 422,

    # 500 Internal Server Error
    DamageAnalysisException: 500,
    PerformanceAnalysisException: 500,
    ReportGenerationException: 500,
    ConfigurationException: 500,
    AnalysisException: 500,
    ModelLoadFailedException: 500,

    # 503 Service Unavailable
    ModelNotLoadedException: 503,
    ResourceException: 503,
    ServiceUnavailableException: 503,

    # 504 Gateway Timeout
    TimeoutException: 504,
}


def get_http_status_code(exception: Exception) -> int:
    """예외 타입에 따른 HTTP 상태 코드 반환"""
    return EXCEPTION_STATUS_MAPPING.get(type(exception), 500)


def get_error_details(exception: AIServiceException) -> Dict[str, Any]:
    """API 응답용 에러 상세 정보 생성"""
    return {
        "error": exception.error_code or "UNKNOWN_ERROR",
        "message": exception.message,
        "details": exception.details
    }
