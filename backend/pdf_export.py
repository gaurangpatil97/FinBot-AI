import io
import json
import re
import os
import matplotlib
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

# Import the session DB to fetch messages
from app.db import sessions_db

# Register DejaVu Sans for Rupee symbol support
dejavu_path = os.path.join(matplotlib.get_data_path(), 'fonts', 'ttf', 'DejaVuSans.ttf')
dejavu_bold_path = os.path.join(matplotlib.get_data_path(), 'fonts', 'ttf', 'DejaVuSans-Bold.ttf')
pdfmetrics.registerFont(TTFont('DejaVuSans', dejavu_path))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', dejavu_bold_path))
# We also need a generic bold-italic/italic if needed, but reportlab supports basic mapping
from reportlab.lib.fonts import addMapping
addMapping('DejaVuSans', 0, 0, 'DejaVuSans')
addMapping('DejaVuSans', 1, 0, 'DejaVuSans-Bold')

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
                ax.plot(x_axis, data, label=name, marker="o", linewidth=2, color="#111111")
    ax.set_title(chart_data.get("title", ""))
    ax.set_xlabel("")
    y_label = chart_data.get("y_axis_label")
    if y_label:
        ax.set_ylabel(y_label)
    ax.grid(True, color="#a8a193", linewidth=0.5, alpha=0.7)
    ax.legend()
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

