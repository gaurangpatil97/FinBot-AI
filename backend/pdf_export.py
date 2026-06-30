import matplotlib
matplotlib.use("Agg")

import io
import json
import re
import os
from typing import List, Dict, Any

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import matplotlib.pyplot as plt
import openai
from fastapi import HTTPException
from config import settings

# Import the session DB to fetch messages
from app.db import sessions_db
from app.core.calculation_agent import fetch_metric, compute_answer, HARDCODED_FORMULAS
from app.core.chart_builder import build_chart_data, get_available_years

# Register DejaVu Sans for Rupee symbol support
dejavu_path = os.path.join(matplotlib.get_data_path(), 'fonts', 'ttf', 'DejaVuSans.ttf')
dejavu_bold_path = os.path.join(matplotlib.get_data_path(), 'fonts', 'ttf', 'DejaVuSans-Bold.ttf')
pdfmetrics.registerFont(TTFont('DejaVuSans', dejavu_path))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', dejavu_bold_path))
# We also need a generic bold-italic/italic if needed, but reportlab supports basic mapping
from reportlab.lib.fonts import addMapping
addMapping('DejaVuSans', 0, 0, 'DejaVuSans')
addMapping('DejaVuSans', 1, 0, 'DejaVuSans-Bold')


def _resolve_excel_source_name(company_slug: str) -> str:
    try:
        with open(settings.COMPANIES_FILE, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception:
        return "Financial Data.xlsx"

    company = next((item for item in payload.get("companies", []) if item.get("slug") == company_slug), None)
    if not company:
        return "Financial Data.xlsx"

    for file_record in company.get("files", []):
        if file_record.get("file_type") != "excel":
            continue

        filename = file_record.get("filename")
        if isinstance(filename, str) and filename.strip():
            return filename.strip()

    return "Financial Data.xlsx"

# Theme constants (match globals.css)
BACKGROUND_COLOR = HexColor("#e8ddc7")  # cream background for PDF page background (optional)
TABLE_BORDER_COLOR = HexColor("#a8a193")  # warm‑grey borders for tables
TEXT_COLOR = colors.black

def render_chart_image(chart_data: Dict[str, Any]) -> io.BytesIO:
    """Render a chart (bar / line / combo) using Matplotlib and return PNG bytes.
    The function respects the theme defined in globals.css.
    """
    fig, ax = plt.subplots(figsize=(8, 4), facecolor="#e8ddc7")  # cream background
    chart_type = chart_data.get("chart_type", "bar")
    x_axis = chart_data.get("x_axis", [])
    series = chart_data.get("series", [])
    secondary = chart_data.get("secondary_y_axis", False)
    ax2 = None
    if chart_type == "combo":
        ax2 = ax.twinx()

    for s in series:
        name = s.get("name", "")
        data = s.get("data", [])
        if chart_type == "line":
            ax.plot(x_axis, data, label=name, marker="o", linewidth=2, color="#111111")
        elif chart_type == "bar":
            ax.bar(x_axis, data, label=name, color="#857c6b")
        elif chart_type == "combo":
            # First series as bar, others as line
            if series.index(s) == 0:
                ax.bar(x_axis, data, label=name, color="#857c6b")
            else:
                ax2.plot(x_axis, data, label=name, marker="o", linewidth=2, color="#111111")

    ax.set_title(chart_data.get("title", ""))
    ax.set_xlabel("")
    
    y_label = chart_data.get("y_axis_label", "Value (Cr)")
    if chart_type == "combo":
        ax.set_ylabel(f"{series[0].get('name', 'Value')} ({y_label})" if series else y_label)
        if ax2 and len(series) > 1:
            ax2.set_ylabel(f"{series[1].get('name', 'Value')} ({y_label})")
    else:
        ax.set_ylabel(y_label)

    ax.grid(True, color="#a8a193", linewidth=0.5, alpha=0.7)
    
    if ax2:
        ax2.grid(False)
        lines_1, labels_1 = ax.get_legend_handles_labels()
        lines_2, labels_2 = ax2.get_legend_handles_labels()
        ax.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper left", ncol=2, framealpha=0.9)
    else:
        ax.legend(loc="upper left", ncol=max(1, len(series)), framealpha=0.9)
        
    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf

def _parse_markdown_to_flowables(text: str, answer_style: ParagraphStyle) -> List[Any]:
    """Very simple markdown parser for headings, tables and paragraphs.
    Returns a list of ReportLab flowables.
    """
    flowables: List[Any] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Apply bold formatting globally to the line
        line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)

        if line.startswith("## "):
            # Heading2
            heading = line[3:]
            style = ParagraphStyle(name="Heading2", fontName="DejaVuSans-Bold", fontSize=14, leading=16, spaceAfter=6, textColor=TEXT_COLOR)
            flowables.append(Paragraph(heading, style))
            i += 1
        elif line.startswith("- ") or line.startswith("* "):
            # Bullet point
            bullet_text = line[2:].strip()
            style = ParagraphStyle(name="Bullet", parent=answer_style, leftIndent=15, bulletIndent=5)
            flowables.append(Paragraph(f"• {bullet_text}", style))
            i += 1
        elif "|" in line and "---" in (lines[i + 1] if i + 1 < len(lines) else ""):
            # Table detected (markdown header row then separator)
            header = [h.strip() for h in line.split("|") if h.strip()]
            i += 2
            rows = []
            while i < len(lines) and "|" in lines[i]:
                row = [re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', c.strip()) for c in lines[i].split("|") if c.strip()]
                rows.append(row)
                i += 1
            table_data = [header] + rows
            tbl = Table(table_data, hAlign="LEFT")
            tbl.setStyle(
                TableStyle(
                    [
                        ("GRID", (0, 0), (-1, -1), 0.5, TABLE_BORDER_COLOR),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                        ("TEXTCOLOR", (0, 0), (-1, -1), TEXT_COLOR),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("FONTNAME", (0, 0), (-1, -1), "DejaVuSans"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ]
                )
            )
            flowables.append(tbl)
            flowables.append(Spacer(1, 8))
        elif line:
            # Regular paragraph
            flowables.append(Paragraph(line, answer_style))
            i += 1
        else:
            i += 1
    return flowables

def generate_transcript_pdf(session_id: str) -> bytes:
    """Generate a PDF transcript for a given session.
    Returns the PDF as raw bytes.
    """
    messages = sessions_db.get_messages(session_id)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)

    # Styles
    styles = getSampleStyleSheet()
    question_style = ParagraphStyle(name="Question", fontName="DejaVuSans-Bold", fontSize=11, leading=13, textColor=TEXT_COLOR, spaceAfter=6, backColor=HexColor("#f0f0f0"))
    answer_style = ParagraphStyle(name="Answer", fontName="DejaVuSans", fontSize=10, leading=12, textColor=TEXT_COLOR, spaceAfter=8)

    story: List[Any] = []

    if not messages:
        placeholder = Paragraph("No transcript available for this session.", answer_style)
        story.append(placeholder)
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    for msg in messages:
        msg_flowables = []
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "user":
            content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', content)
            msg_flowables.append(Paragraph(f"<b>{content}</b>", question_style))
            msg_flowables.append(Spacer(1, 6))
        else:
            flowables = _parse_markdown_to_flowables(content, answer_style)
            for f in flowables:
                msg_flowables.append(f)
            chart_data = msg.get("chart_data")
            if chart_data:
                img_buf = render_chart_image(chart_data)
                img = Image(img_buf, width=500, height=250, hAlign="CENTER")
                msg_flowables.append(Spacer(1, 6))
                msg_flowables.append(img)
                msg_flowables.append(Spacer(1, 6))
            msg_flowables.append(Spacer(1, 12))
        
        story.append(KeepTogether(msg_flowables))
        
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

def generate_summary_pdf(session_id: str) -> bytes:
    """Generate an AI-summarized PDF report for a given session.
    Returns the PDF as raw bytes.
    """
    messages = sessions_db.get_messages(session_id)
    session = sessions_db.get_session(session_id)
    company_name = "Unknown Company"
    if session and "company_slug" in session:
        company_name = session["company_slug"].replace("_", " ").title()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name="Title", fontName="DejaVuSans-Bold", fontSize=18, leading=22, textColor=TEXT_COLOR, spaceAfter=18, alignment=1)
    answer_style = ParagraphStyle(name="Answer", fontName="DejaVuSans", fontSize=10, leading=12, textColor=TEXT_COLOR, spaceAfter=8)

    story: List[Any] = []

    if not messages:
        story.append(Paragraph(f"FinBot — {company_name} Summary Report", title_style))
        story.append(Paragraph("No session data available to summarize.", answer_style))
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    # 1. Build the transcript for the LLM
    transcript_lines = []
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "user":
            transcript_lines.append(f"User: {content}")
        else:
            transcript_lines.append(f"AI: {content}")
    
    full_transcript = "\n\n".join(transcript_lines)

    # 2. Ask GPT to summarize
    prompt = f"""You are a financial AI assistant. Read the following session transcript and generate a structured summary.
    Extract the key findings, important financial numbers/metrics mentioned, and overall conclusions.
    Format your response in Markdown using the following structure:
    ## Key Findings
    (bulleted list)
    ## Key Metrics
    (bulleted list of important numbers/ratios)
    ## Conclusions
    (short paragraph or bullets)

    Transcript:
    {full_transcript}
    """
    
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    summary_text = response.choices[0].message.content.strip()

    # 3. Build the PDF
    story.append(Paragraph(f"FinBot — {company_name} Summary Report", title_style))
    story.append(Spacer(1, 12))

    summary_flowables = _parse_markdown_to_flowables(summary_text, answer_style)
    for f in summary_flowables:
        story.append(f)

    # 4. Append any charts from the session at the end
    charts_appended = False
    for msg in messages:
        chart_data = msg.get("chart_data")
        if chart_data:
            if not charts_appended:
                heading_style = ParagraphStyle(name="Heading2", fontName="DejaVuSans-Bold", fontSize=14, leading=16, spaceAfter=6, textColor=TEXT_COLOR)
                story.append(Spacer(1, 12))
                story.append(Paragraph("Supporting Charts", heading_style))
                charts_appended = True
            
            img_buf = render_chart_image(chart_data)
            img = Image(img_buf, width=500, height=250, hAlign="CENTER")
            chart_flowables = [
                Spacer(1, 6),
                img,
                Spacer(1, 12)
            ]
            story.append(KeepTogether(chart_flowables))
            
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

def generate_report_pdf(session_id: str, template: str, sections: List[str]) -> bytes:
    session = sessions_db.get_session(session_id)
    if not session or not session.get("company_slug"):
        raise HTTPException(status_code=400, detail="company_slug missing from session")

    company_slug = session["company_slug"]
    company_name = company_slug.replace("_", " ").title()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name="Title", fontName="DejaVuSans-Bold", fontSize=18, leading=22, textColor=TEXT_COLOR, spaceAfter=18, alignment=1)
    answer_style = ParagraphStyle(name="Answer", fontName="DejaVuSans", fontSize=10, leading=12, textColor=TEXT_COLOR, spaceAfter=8)

    story: List[Any] = []
    story.append(Paragraph(f"FinBot — {company_name} Financial Analysis Report", title_style))
    story.append(Spacer(1, 12))

    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    years = get_available_years(company_slug)

    def parse_and_append(markdown_text: str):
        flowables = _parse_markdown_to_flowables(markdown_text, answer_style)
        for f in flowables:
            story.append(f)

    # We must respect the order from the prompt: executive_summary, financial_highlights, ratio_analysis, growth_analysis, risk_factors, sources
    ordered_sections = [
        "executive_summary", "financial_highlights", "ratio_analysis",
        "growth_analysis", "risk_factors", "sources"
    ]

    for section in ordered_sections:
        if section not in sections:
            continue

        if section == "executive_summary":
            metrics_data = {}
            for m in ["Sales", "Net profit", "EBITDA"]:
                arr = []
                for y in years:
                    val = None
                    for sheet in ["profit_loss", "balance_sheet", "cash_flow"]:
                        try:
                            val = fetch_metric(m, sheet, y, company_slug)
                            if val is not None: break
                        except Exception:
                            pass
                    arr.append(f"{y}: {val if val is not None else 'N/A'}")
                metrics_data[m] = ", ".join(arr)
            
            prompt = f"""You are a financial AI. Based on the following raw metrics across available years for {company_name}:
Revenue (Sales): {metrics_data['Sales']}
Net Profit: {metrics_data['Net profit']}
EBITDA: {metrics_data['EBITDA']}

Write a 2-3 paragraph prose overview of the company's financial performance.
Format monetary values with the ₹ symbol and Cr suffix (e.g. ₹5,690 Cr), consistent with the chart axis labels.
Do NOT use a ## heading for the body text, just return the paragraphs directly."""
            response = client.chat.completions.create(model="gpt-4.1-mini", messages=[{"role": "user", "content": prompt}], temperature=0)
            content = response.choices[0].message.content.strip()
            parse_and_append(f"## Executive Summary\n{content}")

        elif section == "financial_highlights":
            parse_and_append("## Financial Highlights\n")
            charts_to_build = [
                ["Sales", "Net profit"],
                ["Sales", "EBITDA"]
            ]
            for pair in charts_to_build:
                try:
                    cdata = build_chart_data(company_slug, metrics=pair, force_raw=True)
                    if len(cdata.series) > 1:
                        cdata.chart_type = "combo"
                    img_buf = render_chart_image(cdata.model_dump())
                    img = Image(img_buf, width=500, height=250, hAlign="CENTER")
                    story.append(KeepTogether([Spacer(1, 6), img, Spacer(1, 12)]))
                except Exception as e:
                    import traceback
                    print(traceback.format_exc())
                    parse_and_append(f"*(Could not generate chart for {pair[0]} vs {pair[1]})*\n")

        elif section == "ratio_analysis":
            fy25_data = {}
            try:
                intent_de = HARDCODED_FORMULAS["debt to equity"].copy()
                intent_de["years"] = ["2025"]
                ans_de = compute_answer(intent_de, company_slug=company_slug)
                fy25_data["Debt to Equity"] = ans_de.get("answer", "N/A") if ans_de else "N/A"
            except Exception:
                fy25_data["Debt to Equity"] = "N/A"
                
            try:
                intent_eb = HARDCODED_FORMULAS["ebitda margin"].copy()
                intent_eb["years"] = ["2025"]
                ans_eb = compute_answer(intent_eb, company_slug=company_slug)
                fy25_data["EBITDA Margin"] = ans_eb.get("answer", "N/A") if ans_eb else "N/A"
            except Exception:
                fy25_data["EBITDA Margin"] = "N/A"
                
            prompt = f"""You are a financial AI. 
For {company_name} in FY25, the computed ratios are:
Debt to Equity: {fy25_data['Debt to Equity']}
EBITDA Margin: {fy25_data['EBITDA Margin']}

Provide a 1-2 sentence interpretation of these ratios. Just return the sentences."""
            response = client.chat.completions.create(model="gpt-4.1-mini", messages=[{"role": "user", "content": prompt}], temperature=0)
            content = response.choices[0].message.content.strip()
            parse_and_append(f"## Ratio Analysis\n{content}")

        elif section == "growth_analysis":
            sales_vals = []
            for y in years:
                val = None
                for sheet in ["profit_loss", "balance_sheet", "cash_flow"]:
                    try:
                        val = fetch_metric("Sales", sheet, y, company_slug)
                        if val is not None: break
                    except Exception:
                        pass
                sales_vals.append(val if val is not None else 0.0)
                
            growth_rates = []
            for i in range(1, len(sales_vals)):
                prev = sales_vals[i-1]
                curr = sales_vals[i]
                if prev != 0.0:
                    growth_rates.append(f"{years[i-1]}->{years[i]}: {round(((curr - prev) / prev) * 100, 2)}%")
                else:
                    growth_rates.append(f"{years[i-1]}->{years[i]}: N/A")
                    
            prompt = f"""You are a financial AI. 
For {company_name}, the Revenue (Sales) YoY growth rates are:
{', '.join(growth_rates)}

Write a brief narration (1-2 paragraphs) analyzing this growth trend. Just return the text."""
            response = client.chat.completions.create(model="gpt-4.1-mini", messages=[{"role": "user", "content": prompt}], temperature=0)
            content = response.choices[0].message.content.strip()
            parse_and_append(f"## Growth Analysis\n{content}")

        elif section == "risk_factors":
            prompt = f"""You are a financial AI. 
Provide 2-3 bullet points on potential risk factors for {company_name}, specifically framed around the FY25 profit decline.
Explicitly frame these as "areas warranting further analysis" to avoid overclaiming.
Return only the bullet points."""
            response = client.chat.completions.create(model="gpt-4.1-mini", messages=[{"role": "user", "content": prompt}], temperature=0)
            content = response.choices[0].message.content.strip()
            parse_and_append(f"## Risk Factors\n{content}")

        elif section == "sources":
            source_name = _resolve_excel_source_name(company_slug)
            sources_text = f"- {source_name}\n- Annual Report PDF\n- Annual Report Images\n- Concall Transcripts"
            parse_and_append(f"## Sources\n{sources_text}")

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
