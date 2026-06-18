import os
import uuid
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas as pdf_canvas
import re
from config import PDFS_DIR


def clean_text(text: str) -> str:
    """Remove markdown and special chars that break PDF rendering"""
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    text = re.sub(r'#{1,6}\s+', '', text)
    text = text.replace('&', '&amp;').replace('<b>', '\x00b').replace('</b>', '\x01b')
    text = text.replace('<i>', '\x00i').replace('</i>', '\x01i')
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    text = text.replace('\x00b', '<b>').replace('\x01b', '</b>')
    text = text.replace('\x00i', '<i>').replace('\x01i', '</i>')
    return text


def get_styles():
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=22,
        textColor=colors.HexColor('#1a237e'),
        spaceAfter=12,
        spaceBefore=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
    )

    heading1_style = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#283593'),
        spaceAfter=8,
        spaceBefore=14,
        fontName='Helvetica-Bold',
        borderPad=4,
    )

    heading2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor('#3949ab'),
        spaceAfter=6,
        spaceBefore=10,
        fontName='Helvetica-Bold',
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        spaceAfter=6,
        spaceBefore=2,
        alignment=TA_JUSTIFY,
        fontName='Helvetica',
    )

    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=styles['Normal'],
        fontSize=11,
        leading=15,
        spaceAfter=4,
        spaceBefore=2,
        leftIndent=20,
        bulletIndent=10,
        fontName='Helvetica',
    )

    code_style = ParagraphStyle(
        'CustomCode',
        parent=styles['Code'],
        fontSize=10,
        leading=14,
        spaceAfter=6,
        spaceBefore=4,
        leftIndent=20,
        fontName='Courier',
        backColor=colors.HexColor('#f5f5f5'),
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#5c6bc0'),
        spaceAfter=20,
        spaceBefore=2,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique',
    )

    return {
        'title': title_style,
        'h1': heading1_style,
        'h2': heading2_style,
        'body': body_style,
        'bullet': bullet_style,
        'code': code_style,
        'subtitle': subtitle_style,
    }


def parse_ai_response_to_story(content: str, styles: dict) -> list:
    """Convert AI markdown-like text to ReportLab story elements"""
    story = []
    lines = content.split('\n')

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            story.append(Spacer(1, 6))
            continue

        if line_stripped.startswith('### '):
            story.append(Paragraph(clean_text(line_stripped[4:]), styles['h2']))
        elif line_stripped.startswith('## '):
            story.append(Paragraph(clean_text(line_stripped[3:]), styles['h1']))
        elif line_stripped.startswith('# '):
            story.append(Paragraph(clean_text(line_stripped[2:]), styles['h1']))
        elif line_stripped.startswith(('- ', '* ', '• ')):
            bullet_text = '• ' + clean_text(line_stripped[2:])
            story.append(Paragraph(bullet_text, styles['bullet']))
        elif re.match(r'^\d+\.\s', line_stripped):
            story.append(Paragraph(clean_text(line_stripped), styles['bullet']))
        elif line_stripped.startswith('---') or line_stripped.startswith('___'):
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#c5cae9')))
            story.append(Spacer(1, 8))
        else:
            story.append(Paragraph(clean_text(line_stripped), styles['body']))

    return story


def create_pdf(filename: str, title: str, subtitle: str, content: str, video_title: str = "") -> str:
    """Create a styled PDF and return the filepath"""
    filepath = os.path.join(PDFS_DIR, f"{filename}_{uuid.uuid4().hex[:8]}.pdf")
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2.5*cm,
        bottomMargin=2.5*cm,
    )

    styles = get_styles()
    story = []

    # Header
    story.append(Paragraph("📚 AI Study Assistant", styles['subtitle']))
    story.append(Paragraph(title, styles['title']))

    if video_title:
        story.append(Paragraph(f"Source: {clean_text(video_title)}", styles['subtitle']))
    if subtitle:
        story.append(Paragraph(subtitle, styles['subtitle']))

    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#3949ab')))
    story.append(Spacer(1, 16))

    # Content
    story.extend(parse_ai_response_to_story(content, styles))

    # Footer spacer
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#c5cae9')))
    story.append(Paragraph("Generated by AI Study Assistant Bot", styles['subtitle']))

    doc.build(story)
    return filepath


def create_quiz_pdf(filename: str, title: str, questions: list, answers: list, video_title: str = "") -> tuple[str, str]:
    """Create quiz PDF and answer key PDF, return both paths"""
    styles = get_styles()

    # Quiz PDF
    quiz_path = os.path.join(PDFS_DIR, f"{filename}_quiz_{uuid.uuid4().hex[:8]}.pdf")
    doc = SimpleDocTemplate(quiz_path, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2.5*cm, bottomMargin=2.5*cm)
    story = [
        Paragraph("📚 AI Study Assistant", styles['subtitle']),
        Paragraph(title, styles['title']),
    ]
    if video_title:
        story.append(Paragraph(f"Source: {clean_text(video_title)}", styles['subtitle']))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#3949ab')))
    story.append(Spacer(1, 16))
    story.extend(parse_ai_response_to_story("\n".join(questions), styles))
    doc.build(story)

    # Answer Key PDF
    ans_path = os.path.join(PDFS_DIR, f"{filename}_answers_{uuid.uuid4().hex[:8]}.pdf")
    doc2 = SimpleDocTemplate(ans_path, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2.5*cm, bottomMargin=2.5*cm)
    story2 = [
        Paragraph("📚 AI Study Assistant", styles['subtitle']),
        Paragraph(f"{title} — Answer Key", styles['title']),
    ]
    if video_title:
        story2.append(Paragraph(f"Source: {clean_text(video_title)}", styles['subtitle']))
    story2.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#3949ab')))
    story2.append(Spacer(1, 16))
    story2.extend(parse_ai_response_to_story("\n".join(answers), styles))
    doc2.build(story2)

    return quiz_path, ans_path
