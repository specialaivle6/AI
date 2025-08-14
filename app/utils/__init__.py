"""
Utils Package - 유틸리티 함수들

이미지 처리, 성능 계산, PDF 리포트 생성 등 공통으로 사용되는 헬퍼 함수들을 포함합니다.
개선된 예외 처리와 설정 기반 검증 기능을 제공합니다.
"""

from .image_utils import (
    # S3 연동
    download_image_from_s3,
    get_image_info,

    # 이미지 검증 및 처리
    validate_image_file,
    preprocess_image_for_ai,
    optimize_image_for_storage,
    create_thumbnail,
    extract_image_metadata
)

from .performance_utils import (
    # 데이터 파일 관리
    find_data_file,

    # 지역 및 모델 유틸리티
    find_nearest_region,
    canonicalize_model_name,
    get_model_specs,

    # 비용 추정
    estimate_panel_cost
)

from .report_generator import (
    # 성능 분석
    estimate_lifespan,

    # PDF 리포트 생성
    generate_performance_report
)

__all__ = [
    # 이미지 처리
    "download_image_from_s3",
    "get_image_info",
    "validate_image_file",
    "preprocess_image_for_ai",
    "optimize_image_for_storage",
    "create_thumbnail",
    "extract_image_metadata",

    # 데이터 파일 관리
    "find_data_file",

    # 성능 유틸리티
    "find_nearest_region",
    "canonicalize_model_name",
    "get_model_specs",
    "estimate_panel_cost",
    "estimate_lifespan",

    # 리포트 생성
    "generate_performance_report"
]

# 패키지 메타데이터
__version__ = "3.0.0"
__description__ = "Solar Panel AI Service Utilities"
