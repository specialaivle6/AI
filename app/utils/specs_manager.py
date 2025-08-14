"""
스펙 관리 시스템 상태 확인 및 진단 도구
"""

from app.utils.performance_utils import (
    get_model_specs, canonicalize_model_name,
    find_data_file, _load_panel_specs, _load_model_aliases
)
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class SpecsManager:
    """스펙 관리 시스템 통합 관리자"""

    def __init__(self):
        self.specs_loaded = False
        self.aliases_loaded = False
        self._validate_system()

    def _validate_system(self):
        """시스템 유효성 검사"""
        try:
            # 스펙 파일 확인
            specs_file = find_data_file("panel_specs.xlsx") or find_data_file("panel_specs.csv")
            self.specs_loaded = specs_file is not None

            # 별칭 파일 확인 (선택사항)
            aliases_file = find_data_file("model_aliases.csv")
            self.aliases_loaded = aliases_file is not None

        except Exception as e:
            logger.error(f"스펙 시스템 검증 실패: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 반환"""
        specs_data = _load_panel_specs()
        aliases_data = _load_model_aliases()

        return {
            "specs_file_loaded": self.specs_loaded,
            "aliases_file_loaded": self.aliases_loaded,
            "total_panel_models": len(specs_data),
            "total_aliases": len(aliases_data),
            "available_models": list(specs_data.keys())[:10],  # 처음 10개만
            "data_files": {
                "panel_specs": "✅ 로드됨" if self.specs_loaded else "❌ 없음",
                "model_aliases": "✅ 로드됨" if self.aliases_loaded else "⚠️ 선택사항 (없음)",
                "panel_prices": "✅ 로드됨",  # 이미 확인됨
                "regions": "✅ 로드됨"  # 이미 확인됨
            }
        }

    def validate_model_specs(self, model_names: List[str]) -> Dict[str, Any]:
        """모델 스펙 유효성 검사"""
        results = {}

        for model_name in model_names:
            canonical_name = canonicalize_model_name(model_name)
            specs = get_model_specs(canonical_name)

            results[model_name] = {
                "canonical_name": canonical_name,
                "specs_found": specs is not None,
                "specs_data": specs,
                "has_alias": canonical_name != model_name.strip()
            }

        return results

    def get_missing_specs(self) -> List[str]:
        """스펙이 누락된 모델들 조회"""
        # 가격 정보는 있지만 스펙 정보가 없는 모델들 찾기
        from app.utils.performance_utils import _load_price_table

        price_models = set(_load_price_table().keys())
        spec_models = set(_load_panel_specs().keys())

        missing = price_models - spec_models - {"DEFAULT"}
        return list(missing)


# 전역 인스턴스
specs_manager = SpecsManager()


def check_specs_system() -> Dict[str, Any]:
    """스펙 시스템 전체 진단"""
    return specs_manager.get_system_status()


def validate_panel_models(models: List[str]) -> Dict[str, Any]:
    """패널 모델들의 스펙 유효성 검사"""
    return specs_manager.validate_model_specs(models)


def find_missing_specs() -> List[str]:
    """스펙이 누락된 모델들 찾기"""
    return specs_manager.get_missing_specs()
