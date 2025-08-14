"""
PDF 리포트 생성 유틸리티
new_service의 고급 리포트 생성 기능 완전 통합
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
from app.utils.performance_utils import CostEstimate

logger = logging.getLogger(__name__)


def _find_font_in_roots(candidates, roots):
    """여러 경로에서 폰트 파일 탐색"""
    for root in roots:
        root = Path(root)
        for name in candidates:
            p = root / name
            if p.exists():
                return str(p.resolve())
    return None


def _setup_korean_fonts():
    """new_service와 동일한 고급 한글 폰트 설정"""
    # 1) Windows '맑은 고딕' 우선
    win_reg = Path(r"C:\Windows\Fonts\malgun.ttf")
    win_bold = Path(r"C:\Windows\Fonts\malgunbd.ttf")
    if win_reg.exists() and win_bold.exists():
        pdfmetrics.registerFont(TTFont("KR-Regular", str(win_reg)))
        pdfmetrics.registerFont(TTFont("KR-Bold", str(win_bold)))
        plt.rcParams["font.family"] = ["Malgun Gothic"]
        plt.rcParams["axes.unicode_minus"] = False
        return "KR-Regular", "KR-Bold"

    # 2) 프로젝트/환경 폴더에서 Noto Sans KR 찾기
    here = Path(__file__).resolve()
    roots = []
    if os.environ.get("FONT_DIR"):
        roots.append(os.environ["FONT_DIR"])
    roots += [
        here.parents[1] / "fonts",   # project_root/fonts
        here.parent / "fonts",       # utils/fonts
        Path.cwd() / "fonts",        # working_dir/fonts
    ]
    reg = _find_font_in_roots(
        ["NotoSansKR-Regular.otf", "NotoSansCJKkr-Regular.otf"], roots
    )
    bld = _find_font_in_roots(
        ["NotoSansKR-Bold.otf", "NotoSansCJKkr-Bold.otf"], roots
    )
    if reg and bld:
        pdfmetrics.registerFont(TTFont("KR-Regular", reg))
        pdfmetrics.registerFont(TTFont("KR-Bold", bld))
        plt.rcParams["font.family"] = ["Noto Sans CJK KR"]
        plt.rcParams["axes.unicode_minus"] = False
        return "KR-Regular", "KR-Bold"

    # 3) 폴백
    plt.rcParams["font.family"] = ["DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    return "Helvetica", "Helvetica-Bold"


# 폰트 초기화
_RL_FONT_REG, _RL_FONT_BOLD = _setup_korean_fonts()


def _add_value_labels(ax):
    """막대 그래프에 값 라벨 추가"""
    for p in ax.patches:
        v = p.get_height()
        ax.text(p.get_x() + p.get_width() / 2, v, f"{v:.1f}", ha="center", va="bottom")


def estimate_lifespan(predicted_kwh: float, actual_kwh: float,
                     install_date, current_date, threshold: float = 0.8) -> float:
    """패널 수명 예측 (new_service와 동일한 로직)"""
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
    """상태를 한글과 색상으로 변환 (new_service와 동일)"""
    s = (status or "").lower()
    if "degraded" in s:
        return "성능저하 패널", "#EF4444"   # 빨강
    if "excellent" in s:
        return "우수 패널", "#16A34A"       # 초록
    return "정상 패널", "#F59E0B"          # 주황(Healthy)


def generate_report(predicted: float, actual: float, status: str, user_id: str,
                   lifespan: Optional[float] = None, cost: Optional[CostEstimate] = None) -> str:
    """
    new_service와 동일한 고급 리포트 생성

    Args:
        predicted: 예측 발전량
        actual: 실제 발전량
        status: 현재 상태
        user_id: 사용자 ID
        lifespan: 예상 수명 (년)
        cost: 비용 추정 결과

    Returns:
        str: 생성된 PDF 파일 경로
    """
    # 공통 타임스탬프/경로
    ts_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ts_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("reports", exist_ok=True)
    report_path = f"reports/{user_id}_{ts_id}.pdf"
    bar_chart = f"reports/{user_id}_{ts_id}_bar.png"
    pr_chart = f"reports/{user_id}_{ts_id}_pr.png"

    # 색상 팔레트
    COLORS = {
        "pred": "#4F46E5",   # 인디고
        "act": "#06B6D4",    # 청록
        "ok": "#16A34A",     # 초록
        "warn": "#F59E0B",   # 주황
        "bad": "#EF4444",    # 빨강
        "grid": "#E5E7EB",   # 회색
    }

    # 성능 지표
    pr = (actual / predicted) if predicted > 0 else 0.0
    status_label_kor, status_color = _status_kor_and_color(status)

    # 메인 막대 그래프 저장 (크게)
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    bars = ax.bar(["예측 발전량", "실측 발전량"], [predicted, actual],
                  edgecolor="white", linewidth=0.8,
                  color=[COLORS["pred"], COLORS["act"]])
    ax.set_title("발전량 비교 (kWh)")
    ax.set_ylabel("kWh")
    ax.grid(True, axis="y", linestyle="--", linewidth=0.6, color=COLORS["grid"])
    for p in bars:
        ax.text(p.get_x() + p.get_width()/2, p.get_height(),
                f"{p.get_height():.1f}", ha="center", va="bottom")
    fig.tight_layout()
    fig.savefig(bar_chart, dpi=160)
    plt.close(fig)

    # PR 게이지(수평 바) 저장
    fig, ax = plt.subplots(figsize=(8.5, 1.2))
    x_pos = max(0.0, min(float(pr), 1.0))  # 0~1 클램프
    ax.barh([0], [1.0], color=COLORS["grid"])         # 배경
    ax.barh([0], [x_pos], color=status_color)         # 실제 PR
    ax.set_xlim(0, 1)
    ax.set_yticks([])
    ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_xticklabels(["0", "0.2", "0.4", "0.6", "0.8", "1.0"])
    ax.set_title("성능비율(PR) 게이지")
    ax.grid(False)
    ha = "right" if x_pos > 0.85 else "left"
    ax.annotate(
        f"{pr:.2f}", xy=(x_pos, 0),
        xytext=(6 if ha == "left" else -6, 0),
        textcoords="offset points",
        va="center", ha=ha, fontweight="bold"
    )
    fig.tight_layout()
    fig.savefig(pr_chart, dpi=160, transparent=True)
    plt.close(fig)

    # PDF 스타일
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="KR-Title", fontName=_RL_FONT_BOLD, fontSize=18, leading=22, alignment=TA_LEFT))
    styles.add(ParagraphStyle(name="KR-H2", fontName=_RL_FONT_BOLD, fontSize=13, leading=18))
    styles.add(ParagraphStyle(name="KR-Body", fontName=_RL_FONT_REG, fontSize=11, leading=16))

    # PDF 본문
    doc = SimpleDocTemplate(
        report_path, pagesize=A4,
        leftMargin=30, rightMargin=30, topMargin=32, bottomMargin=32
    )
    story = []

    # 제목/메타
    story.append(Paragraph("태양광 패널 성능 예측 및 비용 예측 보고서", styles["KR-Title"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"• 고객 ID: {user_id}", styles["KR-Body"]))
    story.append(Paragraph(f"• 보고서 생성일시: {ts_str}", styles["KR-Body"]))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#DDDDDD")))
    story.append(Spacer(1, 10))

    # 1) 성능 요약 (표) — 판정 칸은 Paragraph로 색 입힘
    status_chip = Paragraph(f'<font color="{status_color}">{status_label_kor}</font>', styles["KR-Body"])
    rows = [
        ["예측 발전량 (kWh)", f"{predicted:.2f}"],
        ["실제 발전량 (kWh)", f"{actual:.2f}"],
        ["성능비율 (실측/예측)", f"{pr:.2f}"],
        ["판정", status_chip],
    ]
    if lifespan:
        rows.append(["예상 잔여 수명", f"약 {lifespan*12:.0f} 개월"])

    table = Table([["항목", "값"]] + rows, repeatRows=1, colWidths=[6*cm, 9*cm])
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
    story.append(Image(bar_chart, width=16*cm, height=9.2*cm))   # 크게
    story.append(Spacer(1, 8))
    story.append(Image(pr_chart, width=16*cm, height=2.2*cm))
    story.append(Spacer(1, 12))

    # 2) 교체/비용 — CostEstimate 객체 활용
    need_replace = ("성능저하" in status_label_kor)
    immediate = int(cost.immediate_cost) if cost else 0

    story.append(Paragraph("2) 교체/비용", styles["KR-H2"]))
    story.append(Paragraph(f"- 교체 여부: {'교체가 필요합니다!' if need_replace else '교체 불필요'}", styles["KR-Body"]))
    story.append(Paragraph(f"- 예상 교체 비용(자재+폐기+인건비): {immediate:,} 원", styles["KR-Body"]))

    if not need_replace:
        story.append(Paragraph("  * 정상/우수 판정의 패널은 비용을 0원으로 표시합니다.", styles["KR-Body"]))

        # 미래 교체 정보 추가
        if cost and cost.future_cost_year and cost.future_cost_total:
            story.append(Paragraph(f"- 예상 미래 교체: {cost.future_cost_year}년, 비용 {cost.future_cost_total:,}원", styles["KR-Body"]))

    # 생성
    doc.build(story)

    # 임시 이미지 삭제
    for p in (bar_chart, pr_chart):
        try:
            os.remove(p)
        except FileNotFoundError:
            pass

    return report_path


# 기존 호환성을 위한 별칭 함수들
def generate_performance_report(predicted: float, actual: float, status: str,
                              user_id: str, lifespan: Optional[float] = None,
                              cost: Optional[int] = None) -> str:
    """기존 호환성을 위한 래퍼 함수"""
    # int cost를 CostEstimate로 변환
    cost_estimate = None
    if cost is not None:
        cost_estimate = CostEstimate(immediate_cost=cost, future_cost_year=None, future_cost_total=None)

    return generate_report(predicted, actual, status, user_id, lifespan, cost_estimate)
