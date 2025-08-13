"""
데이터베이스 연동 서비스

PanelImage와 PanelImageReport 테이블과의 연동을 담당합니다.
실제 구현에서는 SQLAlchemy ORM 또는 직접 SQL 쿼리를 사용할 수 있습니다.
"""

from typing import Optional, List
from uuid import UUID
from datetime import date
import logging

from app.models.schemas import (
    PanelImageCreate, PanelImageResponse,
    PanelImageReportCreate, PanelImageReportResponse,
    PanelStatus, Decision, RequestStatus
)

logger = logging.getLogger(__name__)


class DatabaseService:
    """데이터베이스 연동 서비스"""

    def __init__(self):
        # 실제 구현에서는 DB 연결 설정
        # self.db = get_database_connection()
        pass

    async def create_panel_image(self, panel_image: PanelImageCreate) -> PanelImageResponse:
        """패널 이미지 레코드 생성"""
        # TODO: 실제 DB INSERT 구현
        logger.info(f"패널 이미지 생성: panel_id={panel_image.panel_id}, user_id={panel_image.user_id}")

        # 임시 응답 (실제로는 DB에서 생성된 ID 반환)
        return PanelImageResponse(
            id=1,  # DB에서 생성된 ID
            panel_id=panel_image.panel_id,
            user_id=panel_image.user_id,
            film_date=panel_image.film_date,
            panel_imageurl=panel_image.panel_imageurl,
            is_analysis=panel_image.is_analysis
        )

    async def update_panel_image_analysis_status(self, image_id: int, is_analyzed: bool) -> bool:
        """패널 이미지 분석 상태 업데이트"""
        # TODO: 실제 DB UPDATE 구현
        logger.info(f"패널 이미지 분석 상태 업데이트: id={image_id}, is_analysis={is_analyzed}")
        return True

    async def create_panel_image_report(self, report: PanelImageReportCreate) -> PanelImageReportResponse:
        """패널 이미지 리포트 생성"""
        # TODO: 실제 DB INSERT 구현
        logger.info(f"패널 리포트 생성: panel_id={report.panel_id}, status={report.status}")

        # 임시 응답 (실제로는 DB에서 생성된 ID 반환)
        return PanelImageReportResponse(
            id=1,  # DB에서 생성된 ID
            panel_id=report.panel_id,
            user_id=report.user_id,
            status=report.status,
            damage_degree=report.damage_degree,
            decision=report.decision,
            request_status=report.request_status,
            created_at=date.today()
        )

    async def get_panel_image(self, image_id: int) -> Optional[PanelImageResponse]:
        """패널 이미지 조회"""
        # TODO: 실제 DB SELECT 구현
        logger.info(f"패널 이미지 조회: id={image_id}")
        return None

    async def get_panel_images_by_panel(self, panel_id: int) -> List[PanelImageResponse]:
        """특정 패널의 모든 이미지 조회"""
        # TODO: 실제 DB SELECT 구현
        logger.info(f"패널별 이미지 목록 조회: panel_id={panel_id}")
        return []

    async def get_panel_image_reports_by_panel(self, panel_id: int) -> List[PanelImageReportResponse]:
        """특정 패널의 모든 리포트 조회"""
        # TODO: 실제 DB SELECT 구현
        logger.info(f"패널별 리포트 목록 조회: panel_id={panel_id}")
        return []

    async def update_report_status(self, report_id: int, status: RequestStatus) -> bool:
        """리포트 상태 업데이트"""
        # TODO: 실제 DB UPDATE 구현
        logger.info(f"리포트 상태 업데이트: id={report_id}, status={status}")
        return True


class AIResultMapper:
    """AI 분석 결과를 DB 스키마에 맞게 매핑하는 서비스"""

    @staticmethod
    def map_to_panel_status(damage_analysis: dict) -> PanelStatus:
        """AI 분석 결과를 패널 상태로 매핑"""
        overall_damage = damage_analysis.get('overall_damage_percentage', 0)
        critical_damage = damage_analysis.get('critical_damage_percentage', 0)
        contamination = damage_analysis.get('contamination_percentage', 0)

        if critical_damage > 5:
            return PanelStatus.DAMAGE
        elif contamination > 10:
            return PanelStatus.CONTAMINATION
        else:
            return PanelStatus.NORMAL

    @staticmethod
    def map_to_decision(business_assessment: dict) -> Decision:
        """AI 비즈니스 평가를 조치 결정으로 매핑"""
        priority = business_assessment.get('priority', 'LOW')
        recommendations = business_assessment.get('recommendations', [])

        if priority in ['URGENT', 'HIGH']:
            if any('수리' in rec or '교체' in rec for rec in recommendations):
                return Decision.REPLACEMENT
            else:
                return Decision.REPAIR
        elif priority == 'MEDIUM':
            return Decision.REPAIR
        else:
            return Decision.SIMPLE_CLEANING

    @staticmethod
    def calculate_damage_degree(damage_analysis: dict) -> int:
        """손상 정도를 1-10 척도로 계산"""
        overall_damage = damage_analysis.get('overall_damage_percentage', 0)
        critical_damage = damage_analysis.get('critical_damage_percentage', 0)

        # 심각한 손상이 있으면 높은 점수
        if critical_damage > 20:
            return 10
        elif critical_damage > 10:
            return 8
        elif critical_damage > 5:
            return 6
        elif overall_damage > 30:
            return 5
        elif overall_damage > 15:
            return 3
        elif overall_damage > 5:
            return 2
        else:
            return 1
