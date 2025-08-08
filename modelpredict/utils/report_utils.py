from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from datetime import datetime
import matplotlib.pyplot as plt
import os

def estimate_lifespan(predicted_kwh, actual_kwh, install_date, current_date, threshold=0.8):
    """
    태양광 패널의 성능 저하율 기반 예상 수명 계산 함수
    """
    performance_ratio = actual_kwh / predicted_kwh
    months_used = (current_date - install_date).days / 30
    degradation_so_far = 1.0 - performance_ratio

    if degradation_so_far <= 0 or months_used == 0:
        return 25.0  # 최대 수명 보장

    monthly_degradation = degradation_so_far / months_used
    months_to_threshold = (performance_ratio - threshold) / monthly_degradation
    estimated_total_months = months_used + months_to_threshold
    estimated_years = estimated_total_months / 12

    return round(max(0.0, estimated_years), 1)

def generate_report(predicted, actual, status, user_id, lifespan=None):
    """
    예측 결과 기반 PDF 리포트 생성 함수
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("reports", exist_ok=True)
    report_path = f"reports/{user_id}_{timestamp}.pdf"
    chart_path = f"reports/{user_id}_{timestamp}_chart.png"

    # 막대그래프 저장
    plt.figure(figsize=(4, 4))
    plt.bar(["Predicted", "Actual"], [predicted, actual], color=["blue", "orange"])
    plt.title("Power Generation (kWh)")
    plt.ylabel("kWh")
    plt.tight_layout()
    plt.savefig(chart_path)
    plt.close()

    # PDF 리포트 생성
    doc = SimpleDocTemplate(report_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("📊 Solar Panel Performance Report", styles['Title']))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(f"Client ID: {user_id}", styles['Normal']))
    story.append(Paragraph(f"Generated at: {timestamp}", styles['Normal']))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(f"✅ Status: <b>{status}</b>", styles['Heading2']))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Image(chart_path, width=10 * cm, height=8 * cm))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(f"- Predicted Generation: {predicted:.2f} kWh", styles['Normal']))
    story.append(Paragraph(f"- Actual Generation: {actual:.2f} kWh", styles['Normal']))
    story.append(Paragraph(f"- Performance Ratio: {(actual / predicted):.2f}", styles['Normal']))
    
    if lifespan:
        lifespan_months = lifespan * 12
        story.append(Paragraph(f"🔧 Estimated Remaining Lifespan: {lifespan_months:.0f} months", styles["Normal"]))

    doc.build(story)
    os.remove(chart_path)

    return report_path
