"""
PDF 리포트 생성 유틸리티
new_service의 고급 리포트 생성 기능 완전 통합
"""

import os
import matplotlib
matplotlib.use("Agg")  # 서버용 백엔드 설정
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

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
from uuid import uuid4  # ← 추가

logger = logging.getLogger(__name__)

# 전역 변수 안전 초기화
_RL_FONT_REG, _RL_FONT_BOLD = None, None


def _is_valid_font_file(font_path: Path) -> bool:
    try:
        if not font_path.exists() or font_path.stat().st_size < 1000:
            return False

        with open(font_path, 'rb') as f:
            header = f.read(8)

        valid_headers = [
            b'OTTO',
            b'\x00\x01\x00\x00',
            b'true',
            b'typ1',
            b'ttcf'
        ]

        if header.startswith(b'\r\n\r\n') or header.startswith(b'\x0D\x0A\x0D\x0A'):
            logger.warning(f"⚠️ 폰트 파일이 CRLF 변환으로 손상됨: {font_path}")
            return False

        for valid_header in valid_headers:
            if header.startswith(valid_header):
                return True

        logger.warning(f"⚠️ 지원되지 않는 폰트 형식: {font_path} (header: {header.hex()})")
        return False

    except Exception as e:
        logger.warning(f"⚠️ 폰트 파일 검증 실패: {font_path} - {e}")
        return False


def _find_font_in_roots(candidates, roots):
    for root in roots:
        root = Path(root)
        if not root.exists():
            continue

        for name in candidates:
            font_path = root / name
            if _is_valid_font_file(font_path):
                logger.info(f"✅ 유효한 폰트 발견: {font_path}")
                return str(font_path.resolve())
            elif font_path.exists():
                logger.warning(f"⚠️ 손상된 폰트 파일 발견: {font_path}")

    return None


def _try_system_fonts():
    system_fonts = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.otf",
        "/usr/share/fonts/truetype/noto/NotoSansKR-Regular.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansKR-Regular.otf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumMyeongjo.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/gulim.ttc",
    ]

    for font_path in system_fonts:
        path_obj = Path(font_path)
        if _is_valid_font_file(path_obj):
            try:
                pdfmetrics.registerFont(TTFont('SystemKorean', str(path_obj)))
                logger.info(f"✅ 시스템 한글 폰트 로드 성공: {font_path}")

                if "Noto" in font_path:
                    plt.rcParams["font.family"] = ["Noto Sans CJK KR", "DejaVu Sans"]
                elif "Nanum" in font_path:
                    plt.rcParams["font.family"] = ["NanumGothic", "DejaVu Sans"]
                elif "malgun" in font_path:
                    plt.rcParams["font.family"] = ["Malgun Gothic", "DejaVu Sans"]
                else:
                    plt.rcParams["font.family"] = ["DejaVu Sans"]

                plt.rcParams["axes.unicode_minus"] = False
                return 'SystemKorean', 'SystemKorean'

            except Exception as e:
                logger.warning(f"⚠️ 시스템 폰트 등록 실패: {font_path} - {e}")
                continue

    return None, None


def _setup_korean_fonts():
    logger.info("🔤 한글 폰트 초기화 시작...")

    try:
        win_reg = Path(r"C:\Windows\Fonts\malgun.ttf")
        win_bold = Path(r"C:\Windows\Fonts\malgunbd.ttf")

        if _is_valid_font_file(win_reg) and _is_valid_font_file(win_bold):
            try:
                pdfmetrics.registerFont(TTFont("KR-Regular", str(win_reg)))
                pdfmetrics.registerFont(TTFont("KR-Bold", str(win_bold)))
                plt.rcParams["font.family"] = ["Malgun Gothic", "DejaVu Sans"]
                plt.rcParams["axes.unicode_minus"] = False
                logger.info("✅ Windows 맑은 고딕 폰트 로드 성공")
                return "KR-Regular", "KR-Bold"
            except Exception as e:
                logger.warning(f"⚠️ Windows 폰트 등록 실패: {e}")

        here = Path(__file__).resolve()
        roots = []

        if os.environ.get("FONT_DIR"):
            roots.append(os.environ["FONT_DIR"])

        roots.extend([
            here.parents[2] / "fonts",
            here.parents[1] / "fonts",
            here.parent / "fonts",
            Path.cwd() / "fonts",
            Path("/app/fonts"),
        ])

        reg_candidates = [
            "NotoSansKR-Regular.otf",
            "NotoSansCJKkr-Regular.otf",
            "NotoSansKR-Regular.ttf"
        ]
        bold_candidates = [
            "NotoSansKR-Bold.otf",
            "NotoSansCJKkr-Bold.otf",
            "NotoSansKR-Bold.ttf"
        ]

        reg_path = _find_font_in_roots(reg_candidates, roots)
        bold_path = _find_font_in_roots(bold_candidates, roots)

        if reg_path and bold_path:
            try:
                pdfmetrics.registerFont(TTFont("KR-Regular", reg_path))
                pdfmetrics.registerFont(TTFont("KR-Bold", bold_path))
                plt.rcParams["font.family"] = ["Noto Sans CJK KR", "DejaVu Sans"]
                plt.rcParams["axes.unicode_minus"] = False
                logger.info(f"✅ 프로젝트 Noto 폰트 로드 성공: {reg_path}")
                return "KR-Regular", "KR-Bold"
            except Exception as e:
                logger.warning(f"⚠️ 프로젝트 폰트 등록 실패: {e}")

        sys_reg, sys_bold = _try_system_fonts()
        if sys_reg and sys_bold:
            return sys_reg, sys_bold

    except Exception as e:
        logger.error(f"❌ 한글 폰트 초기화 중 오류: {e}")

    logger.info("ℹ️ 한글 폰트 로드 실패 - 기본 폰트 사용 (영문만 지원)")
    plt.rcParams["font.family"] = ["DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    return "Helvetica", "Helvetica-Bold"


def _get_korean_fonts():
    global _RL_FONT_REG, _RL_FONT_BOLD

    if _RL_FONT_REG is None or _RL_FONT_BOLD is None:
        try:
            _RL_FONT_REG, _RL_FONT_BOLD = _setup_korean_fonts()
        except Exception as e:
            logger.error(f"❌ 폰트 지연 로딩 실패: {e}")
            _RL_FONT_REG, _RL_FONT_BOLD = 'Helvetica', 'Helvetica-Bold'

    if _RL_FONT_REG is None:
        _RL_FONT_REG = 'Helvetica'
    if _RL_FONT_BOLD is None:
        _RL_FONT_BOLD = 'Helvetica-Bold'

    return _RL_FONT_REG, _RL_FONT_BOLD


# 전역 폰트 초기화 시도
try:
    _RL_FONT_REG, _RL_FONT_BOLD = _setup_korean_fonts()
    logger.info(f"🔤 전역 폰트 초기화 완료: {_RL_FONT_REG}, {_RL_FONT_BOLD}")
except Exception as e:
    logger.warning(f"⚠️ 전역 폰트 초기화 실패, 지연 로딩 사용: {e}")
    _RL_FONT_REG, _RL_FONT_BOLD = "Helvetica", "Helvetica-Bold"


def _add_value_labels(ax):
    for p in ax.patches:
        v = p.get_height()
        ax.text(p.get_x() + p.get_width() / 2, v, f"{v:.1f}", ha="center", va="bottom")


def estimate_lifespan(predicted_kwh: float, actual_kwh: float,
                     install_date, current_date, threshold: float = 0.8) -> float:
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
    s = (status or "").lower()
    if "degraded" in s:
        return "성능저하 패널", "#EF4444"
    if "excellent" in s:
        return "우수 패널", "#16A34A"
    return "정상 패널", "#F59E0B"


# ---- 그래프/피처 표시 유틸 -------------------------------------------------
def _small_bar_chart(predicted: float, actual: float, out_path: str):
    fig, ax = plt.subplots(figsize=(6.0, 3.0), dpi=210)  # 2:1 고정

    bars = ax.bar(["예측", "실측"], [predicted, actual], width=0.55, linewidth=0)
    ax.grid(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_alpha(0.4)
    ax.spines["bottom"].set_alpha(0.4)

    ymax = max(predicted, actual)
    ax.set_ylim(0, ymax * 1.18 if ymax > 0 else 1.0)

    for p in bars:
        v = p.get_height()
        ax.text(p.get_x() + p.get_width()/2, v, f"{v:.1f}", ha="center", va="bottom",
                fontsize=10, fontweight="bold")

    ax.set_ylabel("kWh", fontsize=10)
    ax.tick_params(labelsize=10)

    fig.tight_layout(pad=0.6)
    fig.savefig(out_path, dpi=180, bbox_inches="tight", facecolor="white", pad_inches=0.02)
    plt.close(fig)


def _pr_gauge(pr: float, color: str, out_path: str):
    pr = max(0.0, min(float(pr), 1.0))

    fig, ax = plt.subplots(figsize=(6.0, 1.8), dpi=210)  # 10:3.0 고정
    ax.axis("off")

    x0, y0, w, h = 0.05, 0.40, 0.90, 0.34
    ax.add_patch(Rectangle((x0, y0), w, h, transform=ax.transAxes, color="#E5E7EB"))
    ax.add_patch(Rectangle((x0, y0), w * pr, h, transform=ax.transAxes, color=color))

    for t in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0):
        ax.text(x0 + w*t, y0 - 0.18, f"{t:.1f}", ha="center", va="center",
                fontsize=9, color="#6B7280", transform=ax.transAxes)

    x_lbl = min(x0 + w*pr, x0 + w)
    ha = "right" if pr > 0.88 else "left"
    ax.text(x_lbl, y0 + h/2, f"PR {pr:.2f}", ha=ha, va="center",
            fontsize=10, fontweight="bold", color="#111827", transform=ax.transAxes)

    fig.tight_layout(pad=0.2)
    fig.savefig(out_path, bbox_inches="tight", facecolor="white", pad_inches=0.02)
    plt.close(fig)


def _pretty_feature_name(name: str) -> str:
    mapping = {
        "PMPP_rated_W": "정격출력(W)",
        "Temp_Coeff_per_K": "온도계수(/K)",
        "Annual_Degradation_Rate": "연간 열화율",
        "Install_Angle": "설치 각도(°)",
        "Avg_Temp": "평균 기온(°C)",
        "Avg_Humidity": "평균 습도(%)",
        "Avg_Windspeed": "평균 풍속(m/s)",
        "Avg_Sunshine": "평균 일조(h)",
        "Elapsed_Months": "경과 개월",
    }
    if name in mapping: return mapping[name]
    if name.startswith("Panel_Model_"): return "패널 모델: " + name.replace("Panel_Model_", "")
    if name.startswith("Install_Direction_"): return "설치 방향: " + name.replace("Install_Direction_", "")
    if name.startswith("Region_"): return "지역: " + name.replace("Region_", "")
    return name
# -------------------------------------------------------------------------------


def _unique_path(path: str) -> str:
    base, ext = os.path.splitext(path)
    i, out = 1, path
    while os.path.exists(out):
        out = f"{base}_{i}{ext}"
        i += 1
    return out


def generate_report(predicted: float, actual: float, status: str, user_id: str,
                   lifespan: Optional[float] = None, cost: Optional[CostEstimate] = None,
                   extras: Optional[Dict[str, Any]] = None) -> str:
    """
    안전한 PDF 리포트 생성 - 폰트 문제 대응

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
    font_reg, font_bold = _get_korean_fonts()

    ts_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ts_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")  # ← 변경: 마이크로초 포함
    uniq = uuid4().hex[:6]  # ← 추가: 고유 suffix
    os.makedirs("reports", exist_ok=True)
    os.makedirs("temp", exist_ok=True)
    report_path = _unique_path(f"reports/{user_id}_{ts_id}_{uniq}.pdf")  # ← 변경: 고유 경로
    bar_chart = f"temp/{user_id}_{ts_id}_{uniq}_bar.png"  # ← 변경: uniq 포함
    pr_chart = f"temp/{user_id}_{ts_id}_{uniq}_pr.png"    # ← 변경: uniq 포함

    COLORS = {
        "pred": "#4F46E5",
        "act": "#06B6D4",
        "ok": "#16A34A",
        "warn": "#F59E0B",
        "bad": "#EF4444",
        "grid": "#E5E7EB",
    }

    pr = (actual / predicted) if predicted > 0 else 0.0
    status_label_kor, status_color = _status_kor_and_color(status)

    _small_bar_chart(predicted, actual, bar_chart)
    _pr_gauge(pr, status_color, pr_chart)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="KR-Title", fontName=font_bold, fontSize=18, leading=22,
                              alignment=TA_LEFT, spaceAfter=3))
    styles.add(ParagraphStyle(name="KR-H2", fontName=font_bold, fontSize=12.5, leading=16,
                              spaceBefore=0, spaceAfter=3))
    styles.add(ParagraphStyle(name="KR-Body", fontName=font_reg, fontSize=10.5, leading=15))
    styles.add(ParagraphStyle(name="KR-Small", fontName=font_reg, fontSize=9.0, leading=13))

    doc = SimpleDocTemplate(
        report_path, pagesize=A4,
        leftMargin=30, rightMargin=30, topMargin=28, bottomMargin=22
    )
    story = []

    story.append(Paragraph("태양광 패널 성능 예측 및 비용 예측 보고서", styles["KR-Title"]))
    story.append(Paragraph(f"• 고객 ID: {user_id}", styles["KR-Body"]))
    story.append(Paragraph(f"• 보고서 생성일시: {ts_str}", styles["KR-Body"]))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#DDDDDD")))
    story.append(Spacer(1, 6))

    story.append(Paragraph("패널 정보 요약", styles["KR-H2"]))

    extras = extras or {}

    if isinstance(extras, dict) and ("panel_info" in extras or "feature_snapshot" in extras or "top_impacts" in extras):
        snap = extras.get("feature_snapshot") or {}
        panel_info = extras.get("panel_info") or {}
    else:
        snap = {}
        panel_info = extras

    num = snap.get("numeric", {}) or {}
    cat = snap.get("categorical", {}) or {}

    model_name = panel_info.get("model_name") or cat.get("Panel_Model", "")
    install = (panel_info.get("installation") or {})
    install_date = install.get("date", "")
    install_angle = install.get("angle", num.get("Install_Angle", ""))
    install_dir = install.get("direction", cat.get("Install_Direction", ""))

    region = cat.get("Region", "")
    if not region:
        loc = install.get("location") or {}
        lat, lon = loc.get("latitude"), loc.get("longitude")
        if lat is not None and lon is not None:
            region = f"{lat}, {lon}"

    rows_info = [
        ["패널 모델", model_name],
        ["지역", region],
        ["설치일", install_date],
        ["설치 각도(°)", f"{install_angle}"],
        ["설치 방향", install_dir],
    ]
    info_table = Table([["항목","값"]] + rows_info, repeatRows=1, colWidths=[5.2*cm, 8.8*cm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#F3F4F6")),
        ("FONTNAME", (0,0), (-1,0), font_bold),
        ("FONTNAME", (0,1), (0,-1), font_bold),
        ("FONTNAME", (1,1), (1,-1), font_reg),
        ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#FAFAFA")]),
        ("FONTSIZE", (0,0), (-1,-1), 9.0),
        ("LEFTPADDING", (0,0), (-1,-1), 2),
        ("RIGHTPADDING", (0,0), (-1,-1), 2),
        ("TOPPADDING", (0,0), (-1,-1), 2),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 6))

    status_chip = Paragraph(f'<font color="{status_color}">{status_label_kor}</font>', styles["KR-Body"])
    rows = [
        ["예측 발전량 (kWh)", f"{predicted:.2f}"],
        ["실제 발전량 (kWh)", f"{actual:.2f}"],
        ["성능비율 (실측/예측)", f"{pr:.2f}"],
        ["판정", status_chip],
    ]
    if lifespan:
        rows.append(["예상 잔여 수명", f"약 {lifespan*12:.0f} 개월"])

    table = Table([["항목", "값"]] + rows, repeatRows=1, colWidths=[5.2*cm, 8.8*cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#F3F4F6")),
        ("FONTNAME", (0,0), (-1,0), font_bold),
        ("FONTNAME", (0,1), (0,-1), font_bold),
        ("FONTNAME", (1,1), (1,-1), font_reg),
        ("ALIGN", (0,0), (-1,0), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#FAFAFA")]),
        ("LEFTPADDING", (0,0), (-1,-1), 2),
        ("RIGHTPADDING", (0,0), (-1,-1), 2),
        ("TOPPADDING", (0,0), (-1,-1), 2),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
        ("FONTSIZE", (0,0), (-1,-1), 9.0),
    ]))

    story.append(Paragraph("1) 성능 요약", styles["KR-H2"]))
    story.append(table)
    story.append(Spacer(1, 4))

    story.append(Image(bar_chart, width=10.0*cm, height=5.0*cm))
    story.append(Spacer(1, 2))
    story.append(Image(pr_chart,  width=10.0*cm, height=3.0*cm))
    story.append(Spacer(1, 2))

    story.append(Paragraph("2) 예측 근거", styles["KR-H2"]))
    story.append(Paragraph(
        "• 기여도 부호: + 는 예측 발전량을 높이는 방향, - 는 낮추는 방향입니다. 절댓값이 클수록 영향력이 큽니다. (범주형은 현재 선택된 항목만 고려)",
        styles["KR-Small"]
    ))
    story.append(Spacer(1, 3))

    top_impacts: List[Tuple[str, float]] = (extras.get("top_impacts") or [])[:5]
    rows_imp = [[i, _pretty_feature_name(k), f"{v:+.3f}"] for i, (k, v) in enumerate(top_impacts[:5], 1)]

    imp_table = Table([["순위", "피처", "기여도 (ΔkWh)"]] + rows_imp,
                      colWidths=[1.8*cm, 8.1*cm, 3.5*cm])
    imp_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#F3F4F6")),
        ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ("FONTNAME", (0,0), (-1,0), font_bold),
        ("FONTNAME", (0,1), (-1,-1), font_reg),
        ("ALIGN", (0,0), (0,-1), "CENTER"),
        ("ALIGN", (2,1), (2,-1), "RIGHT"),
        ("FONTSIZE", (0,0), (-1,-1), 9.0),
        ("LEFTPADDING", (0,0), (-1,-1), 3),
        ("RIGHTPADDING", (0,0), (-1,-1), 3),
        ("TOPPADDING", (0,0), (-1,-1), 2),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
    ]))
    if rows_imp:
        story.append(imp_table)
        story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("• 중요 피처 정보를 계산할 수 없어 표시하지 않습니다.", styles["KR-Small"]))
        story.append(Spacer(1, 6))

    need_replace = ("성능저하" in status_label_kor)
    immediate = int(cost.immediate_cost) if cost else 0

    story.append(Paragraph("3) 교체/비용", styles["KR-H2"]))
    story.append(Paragraph(f"- 교체 여부: {'교체 필요' if need_replace else '교체 불필요'}", styles["KR-Body"]))
    story.append(Paragraph(f"- 예상 교체 비용(자재+폐기+인건비): {immediate:,} 원", styles["KR-Body"]))

    if not need_replace:
        story.append(Paragraph("  * 정상/우수 판정의 패널은 비용을 0원으로 표시합니다.", styles["KR-Small"]))
        if cost and cost.future_cost_year and cost.future_cost_total:
            story.append(Paragraph(f"- 예상 미래 교체: {cost.future_cost_year}년, 비용 {cost.future_cost_total:,}원", styles["KR-Small"]))

    doc.build(story)

    for p in (bar_chart, pr_chart):
        try:
            os.remove(p)
        except FileNotFoundError:
            pass

    return report_path


# 기존 호환성을 위한 별칭 함수들
def generate_performance_report(predicted: float, actual: float, status: str,
                              user_id: str, lifespan: Optional[float] = None,
                              cost: Optional[int] = None, extras: Optional[Dict[str, Any]] = None,) -> str:
    """기존 호환성을 위한 래퍼 함수"""
    cost_estimate = None
    if cost is not None:
        cost_estimate = CostEstimate(immediate_cost=cost, future_cost_year=None, future_cost_total=None)

    return generate_report(predicted, actual, status, user_id, lifespan, cost_estimate, extras)
