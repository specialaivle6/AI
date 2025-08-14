"""
PDF 리포트 생성 유틸리티
new_service의 리포트 생성 기능을 통합
"""

import os
import matplotlib
matplotlib.use("Agg")  # 서버용 백엔드 설정
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

import logging

logger = logging.getLogger(__name__)


def _setup_korean_fonts():
    """한글 폰트 설정"""
    try:
        # Windows 맑은 고딕 시도
        win_reg = Path(r"C:\Windows\Fonts\malgun.ttf")
        win_bold = Path(r"C:\Windows\Fonts\malgunbd.ttf")
        if win_reg.exists() and win_bold.exists():
            pdfmetrics.registerFont(TTFont("KR-Regular", str(win_reg)))
            pdfmetrics.registerFont(TTFont("KR-Bold", str(win_bold)))
            plt.rcParams["font.family"] = ["Malgun Gothic"]
            plt.rcParams["axes.unicode_minus"] = False
            return "KR-Regular", "KR-Bold"

        # 프로젝트 Noto 폰트 시도
        project_root = Path(__file__).parents[2]  # AI 프로젝트 루트
        noto_reg = project_root / "fonts" / "NotoSansKR-Regular.otf"
        noto_bold = project_root / "fonts" / "NotoSansKR-Bold.otf"

        if noto_reg.exists() and noto_bold.exists():
            pdfmetrics.registerFont(TTFont("KR-Regular", str(noto_reg)))
            pdfmetrics.registerFont(TTFont("KR-Bold", str(noto_bold)))
            plt.rcParams["font.family"] = ["Noto Sans CJK KR"]
            plt.rcParams["axes.unicode_minus"] = False
            return "KR-Regular", "KR-Bold"

    except Exception as e:
        logger.warning(f"한글 폰트 설정 실패: {e}")

    # 폴백
    plt.rcParams["font.family"] = ["DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    return "Helvetica", "Helvetica-Bold"


# 폰트 초기화
_RL_FONT_REG, _RL_FONT_BOLD = _setup_korean_fonts()


def estimate_lifespan(predicted_kwh: float, actual_kwh: float,
                     install_date, current_date, threshold: float = 0.8) -> float:
    """패널 수명 예측"""
    try:
        performance_ratio = actual_kwh / predicted_kwh
        months_used = (current_date - install_date).days / 30
        degradation_so_far = 1.0 - performance_ratio

        if degradation_so_far <= 0 or months_used == 0:
            return 25.0

        monthly_degradation = degradation_so_far / months_used
        months_to_threshold = (performance_ratio - threshold) / monthly_degradation
        estimated_total_months = months_used + months_to_threshold
        estimated_years = estimated_total_months / 12

        return round(max(0.0, estimated_years), 1)
    except:
        return 25.0


def _status_kor_and_color(status: str) -> tuple:
    """상태를 한글과 색상으로 변환"""
    s = (status or "").lower()
    if "degraded" in s:
        return "성능저하 패널", "#EF4444"
    if "excellent" in s:
        return "우수 패널", "#16A34A"
    return "정상 패널", "#F59E0B"


def generate_performance_report(predicted: float, actual: float, status: str,
                              user_id: str, lifespan: Optional[float] = None,
                              cost: Optional[int] = None) -> str:
    """
    성능 예측 PDF 리포트 생성

    Args:
        predicted: 예측 발전량
        actual: 실제 발전량
        status: 패널 상태
        user_id: 사용자 ID
        lifespan: 예상 수명 (년)
        cost: 예상 비용

    Returns:
        str: 생성된 PDF 파일 경로
    """
    # 타임스탬프 및 경로 설정
    ts_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ts_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    # reports 폴더 생성
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    report_path = reports_dir / f"{user_id}_{ts_id}.pdf"
    bar_chart_path = reports_dir / f"{user_id}_{ts_id}_bar.png"
    pr_chart_path = reports_dir / f"{user_id}_{ts_id}_pr.png"

    # 색상 팔레트
    COLORS = {
        "pred": "#4F46E5",
        "act": "#06B6D4",
        "grid": "#E5E7EB",
    }

    # 성능 지표 계산
    pr = (actual / predicted) if predicted > 0 else 0.0
    status_label_kor, status_color = _status_kor_and_color(status)

    try:
        # 메인 막대 그래프 생성
        fig, ax = plt.subplots(figsize=(8.5, 4.8))
        bars = ax.bar(["예측 발전량", "실측 발전량"], [predicted, actual],
                      color=[COLORS["pred"], COLORS["act"]],
                      edgecolor="white", linewidth=0.8)
        ax.set_title("발전량 비교 (kWh)", fontweight="bold")
        ax.set_ylabel("kWh")
        ax.grid(True, axis="y", linestyle="--", linewidth=0.6, color=COLORS["grid"])

        # 막대 위에 수치 표시
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}', ha='center', va='bottom')

        fig.tight_layout()
        fig.savefig(bar_chart_path, dpi=160, bbox_inches='tight')
        plt.close(fig)

        # PR 게이지 생성
        fig, ax = plt.subplots(figsize=(8.5, 1.2))
        x_pos = max(0.0, min(float(pr), 1.0))

        ax.barh([0], [1.0], color=COLORS["grid"])  # 배경
        ax.barh([0], [x_pos], color=status_color)  # 실제 PR

        ax.set_xlim(0, 1)
        ax.set_yticks([])
        ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_xticklabels(["0", "0.2", "0.4", "0.6", "0.8", "1.0"])
        ax.set_title("성능비율(PR) 게이지", fontweight="bold")
        ax.grid(False)

        # PR 수치 표시
        ha = "right" if x_pos > 0.85 else "left"
        ax.annotate(f"{pr:.2f}", xy=(x_pos, 0),
                   xytext=(6 if ha == "left" else -6, 0),
                   textcoords="offset points", va="center", ha=ha, fontweight="bold")

        fig.tight_layout()
        fig.savefig(pr_chart_path, dpi=160, transparent=True, bbox_inches='tight')
        plt.close(fig)

        # PDF 스타일 설정
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="KR-Title", fontName=_RL_FONT_BOLD,
                                fontSize=18, leading=22, alignment=TA_LEFT))
        styles.add(ParagraphStyle(name="KR-H2", fontName=_RL_FONT_BOLD,
                                fontSize=13, leading=18))
        styles.add(ParagraphStyle(name="KR-Body", fontName=_RL_FONT_REG,
                                fontSize=11, leading=16))

        # PDF 문서 생성
        doc = SimpleDocTemplate(str(report_path), pagesize=A4,
                              leftMargin=30, rightMargin=30,
                              topMargin=32, bottomMargin=32)
        story = []

        # 제목 및 메타데이터
        story.append(Paragraph("태양광 패널 성능 예측 및 비용 예측 보고서", styles["KR-Title"]))
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"• 고객 ID: {user_id}", styles["KR-Body"]))
        story.append(Paragraph(f"• 보고서 생성일시: {ts_str}", styles["KR-Body"]))
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#DDDDDD")))
        story.append(Spacer(1, 10))

        # 성능 요약 테이블
        status_chip = Paragraph(f'<font color="{status_color}">{status_label_kor}</font>',
                               styles["KR-Body"])

        table_data = [
            ["항목", "값"],
            ["예측 발전량 (kWh)", f"{predicted:.2f}"],
            ["실제 발전량 (kWh)", f"{actual:.2f}"],
            ["성능비율 (실측/예측)", f"{pr:.2f}"],
            ["판정", status_chip],
        ]

        if lifespan:
            table_data.append(["예상 잔여 수명", f"약 {lifespan*12:.0f} 개월"])

        table = Table(table_data, repeatRows=1, colWidths=[6*cm, 9*cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#F3F4F6")),
            ("FONTNAME", (0,0), (-1,0), _RL_FONT_BOLD),
            ("FONTNAME", (0,1), (0,-1), _RL_FONT_BOLD),
            ("FONTNAME", (1,1), (1,-1), _RL_FONT_REG),
            ("ALIGN", (0,0), (-1,0), "CENTER"),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#FAFAFA")]),
            ("LEFTPADDING", (0,0), (-1,-1), 6),
            ("RIGHTPADDING", (0,0), (-1,-1), 6),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ]))

        story.append(Paragraph("1) 성능 요약", styles["KR-H2"]))
        story.append(table)
        story.append(Spacer(1, 8))

        # 차트 추가
        story.append(Image(str(bar_chart_path), width=16*cm, height=9.2*cm))
        story.append(Spacer(1, 8))
        story.append(Image(str(pr_chart_path), width=16*cm, height=2.2*cm))
        story.append(Spacer(1, 12))

        # 교체/비용 섹션
        need_replace = ("성능저하" in status_label_kor)
        immediate_cost = cost if need_replace else 0

        story.append(Paragraph("2) 교체/비용", styles["KR-H2"]))
        story.append(Paragraph(f"- 교체 여부: {'교체가 필요합니다!' if need_replace else '교체 불필요'}",
                              styles["KR-Body"]))
        story.append(Paragraph(f"- 예상 교체 비용(자재+폐기+인건비): {immediate_cost:,} 원",
                              styles["KR-Body"]))

        if not need_replace:
            story.append(Paragraph("  * 정상/우수 판정의 패널은 비용을 0원으로 표시합니다.",
                                 styles["KR-Body"]))

        # PDF 생성
        doc.build(story)

        # 임시 이미지 파일 삭제
        for temp_file in [bar_chart_path, pr_chart_path]:
            try:
                temp_file.unlink()
            except FileNotFoundError:
                pass

        logger.info(f"✅ PDF 리포트 생성 완료: {report_path}")
        return str(report_path)

    except Exception as e:
        logger.error(f"PDF 리포트 생성 실패: {e}")
        # 임시 파일 정리
        for temp_file in [bar_chart_path, pr_chart_path]:
            try:
                temp_file.unlink()
            except:
                pass
        raise
