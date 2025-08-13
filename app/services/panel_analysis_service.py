"""
통합 패널 분석 서비스

AI 분석 + DB 연동을 통합하여 비즈니스 요구사항에 맞는 완전한 서비스를 제공합니다.
"""

import io
from typing import Optional
from uuid import UUID
from datetime import date
import logging

from app.services.damage_analyzer import DamageAnalyzer
from app.services.database_service import DatabaseService, AIResultMapper
from app.models.schemas import (
    AnalysisRequest, AnalysisResponse,
    PanelImageCreate, PanelImageReportCreate,
    PanelStatus, Decision, RequestStatus
)

logger = logging.getLogger(__name__)


class PanelAnalysisService:
    """통합 패널 분석 서비스"""

    def __init__(self):
        self.damage_analyzer = DamageAnalyzer()
        self.db_service = DatabaseService()
        self.mapper = AIResultMapper()
        self.is_initialized = False

    async def initialize(self):
        """서비스 초기화"""
        await self.damage_analyzer.initialize()
        self.is_initialized = True
        logger.info("통합 패널 분석 서비스 초기화 완료")

    def is_ready(self) -> bool:
        """서비스 준비 상태 확인"""
        return self.is_initialized and self.damage_analyzer.is_loaded()

    async def analyze_panel_with_db_integration(
        self,
        image_bytes: bytes,
        request: AnalysisRequest,
        filename: str = "uploaded_image"
    ) -> AnalysisResponse:
        """
        패널 이미지 분석 + DB 연동

        1. AI 모델로 이미지 분석
        2. PanelImage 레코드 생성
        3. PanelImageReport 레코드 생성
        4. 통합 결과 반환
        """
        if not self.is_ready():
            raise RuntimeError("서비스가 초기화되지 않았습니다.")

        logger.info(f"통합 분석 시작: panel_id={request.panel_id}, user_id={request.user_id}")

        # 1. AI 모델 분석
        ai_result = await self.damage_analyzer.analyze_damage(image_bytes, filename)

        # 2. AI 결과를 DB 스키마에 맞게 매핑
        panel_status = self.mapper.map_to_panel_status(ai_result['damage_analysis'])
        decision = self.mapper.map_to_decision(ai_result['business_assessment'])
        damage_degree = self.mapper.calculate_damage_degree(ai_result['damage_analysis'])

        # 3. PanelImage 레코드 생성
        panel_image_data = PanelImageCreate(
            panel_id=request.panel_id,
            user_id=request.user_id,
            film_date=date.today(),
            panel_imageurl=request.panel_imageurl or f"uploads/{filename}",
            is_analysis=True  # 분석 완료 상태로 설정
        )

        panel_image = await self.db_service.create_panel_image(panel_image_data)

        # 4. PanelImageReport 레코드 생성
        report_data = PanelImageReportCreate(
            panel_id=request.panel_id,
            user_id=request.user_id,
            status=panel_status,
            damage_degree=damage_degree if panel_status != PanelStatus.NORMAL else None,
            decision=decision,
            request_status=RequestStatus.REQUESTING  # 초기 상태
        )

        report = await self.db_service.create_panel_image_report(report_data)

        # 5. 통합 응답 생성
        response = AnalysisResponse(
            # 기존 AI 분석 결과
            image_info=ai_result['image_info'],
            damage_analysis=ai_result['damage_analysis'],
            business_assessment=ai_result['business_assessment'],
            detection_details=ai_result['detection_details'],
            confidence_score=ai_result['confidence_score'],
            timestamp=ai_result['timestamp'],

            # DB 연동 정보
            panel_image_id=panel_image.id,
            panel_image_report_id=report.id,
            recommended_status=panel_status,
            recommended_decision=decision
        )

        logger.info(f"통합 분석 완료: panel_image_id={panel_image.id}, report_id={report.id}")
        return response

    async def analyze_image_url(self, request: AnalysisRequest) -> AnalysisResponse:
        """
        이미지 URL을 통한 분석 (파일 업로드 없이)
        """
        if not request.panel_imageurl:
            raise ValueError("이미지 URL이 필요합니다.")

        # TODO: URL에서 이미지 다운로드 및 분석
        # 현재는 예시로 빈 바이트를 전달
        logger.info(f"URL 기반 분석: {request.panel_imageurl}")
        raise NotImplementedError("URL 기반 분석은 아직 구현되지 않았습니다.")

    async def get_panel_analysis_history(self, panel_id: int):
        """패널의 분석 이력 조회"""
        images = await self.db_service.get_panel_images_by_panel(panel_id)
        reports = await self.db_service.get_panel_image_reports_by_panel(panel_id)

        return {
            "panel_id": panel_id,
            "images": images,
            "reports": reports,
            "total_analyses": len(images)
        }

    async def update_report_status(self, report_id: int, status: RequestStatus) -> bool:
        """리포트 상태 업데이트 (관리자용)"""
        return await self.db_service.update_report_status(report_id, status)

    async def batch_analyze_with_db(self, files_data: list, requests: list[AnalysisRequest]):
        """일괄 분석 + DB 연동"""
        if len(files_data) != len(requests):
            raise ValueError("파일 수와 요청 수가 일치하지 않습니다.")

        results = []
        for i, (image_bytes, request) in enumerate(zip(files_data, requests)):
            try:
                result = await self.analyze_panel_with_db_integration(
                    image_bytes, request, f"batch_image_{i}"
                )
                results.append(result)
            except Exception as e:
                logger.error(f"일괄 분석 중 오류 (index {i}): {str(e)}")
                results.append({"error": str(e), "panel_id": request.panel_id})

        return {
            "total_processed": len(results),
            "successful": len([r for r in results if "error" not in r]),
            "failed": len([r for r in results if "error" in r]),
            "results": results
        }
