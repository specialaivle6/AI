"""
로깅 설정 및 유틸리티
환경별 로그 레벨과 포맷을 관리
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from app.core.config import settings


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None
) -> None:
    """
    로깅 시스템 초기화

    Args:
        log_level: 로그 레벨 (기본값: settings.log_level)
        log_file: 로그 파일 경로 (기본값: settings.log_file)
    """
    log_level = log_level or settings.log_level
    log_file = log_file or settings.log_file

    # 로그 디렉토리 생성
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # 로그 포맷 설정
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)-20s | "
        "%(funcName)-15s:%(lineno)-3d | %(message)s"
    )

    # 날짜 포맷
    date_format = "%Y-%m-%d %H:%M:%S"

    # 기본 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # 기존 핸들러 제거
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_formatter = logging.Formatter(log_format, date_format)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # 파일 핸들러 (로테이션)
    if not settings.debug:  # 프로덕션 환경에서만 파일 로깅
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=_parse_size(settings.log_max_size),
            backupCount=settings.log_backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(log_format, date_format)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("ultralytics").setLevel(logging.WARNING)


def _parse_size(size_str: str) -> int:
    """크기 문자열을 바이트로 변환 (예: '10MB' -> 10485760)"""
    size_str = size_str.upper()
    if size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('GB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        return int(size_str)


def get_logger(name: str) -> logging.Logger:
    """이름을 지정한 로거 반환"""
    return logging.getLogger(name)


class LoggerMixin:
    """로거를 제공하는 믹스인 클래스"""

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__name__)


def log_performance(func_name: str, duration: float, **kwargs) -> None:
    """성능 로깅 헬퍼 함수"""
    logger = get_logger("performance")

    details = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.info(f"⏱️  {func_name} completed in {duration:.3f}s | {details}")


def log_api_request(
    method: str,
    path: str,
    user_id: Optional[str] = None,
    panel_id: Optional[int] = None,
    processing_time: Optional[float] = None
) -> None:
    """API 요청 로깅"""
    logger = get_logger("api")

    details = []
    if user_id:
        details.append(f"user_id={user_id}")
    if panel_id:
        details.append(f"panel_id={panel_id}")
    if processing_time:
        details.append(f"duration={processing_time:.3f}s")

    detail_str = " | " + " | ".join(details) if details else ""
    logger.info(f"🌐 {method} {path}{detail_str}")


def log_model_status(model_name: str, status: str, **kwargs) -> None:
    """모델 상태 로깅"""
    logger = get_logger("model")

    details = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    status_emoji = {
        "loading": "⏳",
        "loaded": "✅",
        "failed": "❌",
        "unloading": "🔄"
    }.get(status, "ℹ️")

    logger.info(f"{status_emoji} {model_name} {status} | {details}")


def log_analysis_result(
    analysis_type: str,
    success: bool,
    duration: float,
    **metadata
) -> None:
    """분석 결과 로깅"""
    logger = get_logger("analysis")

    status_emoji = "✅" if success else "❌"
    status_text = "SUCCESS" if success else "FAILED"

    details = " | ".join([f"{k}={v}" for k, v in metadata.items()])
    logger.info(
        f"{status_emoji} {analysis_type} {status_text} | "
        f"duration={duration:.3f}s | {details}"
    )
