from __future__ import annotations

import re
from pathlib import Path

import markdown as md_lib


def save_output(content: str, out_path: str | Path) -> Path:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    if out.suffix.lower() == ".pdf":
        export_cv_pdf(content, out)
    else:
        out.write_text(content, encoding="utf-8")

    return out


def export_cv_pdf(markdown_text: str, out_path: str | Path) -> Path:
    """Render a polished CV markdown into a nicely laid-out PDF."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, HRFlowable, ListFlowable, ListItem,
    )
    from reportlab.lib.enums import TA_LEFT

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # ── Styles ────────────────────────────────────────────────────────────────
    NAVY = colors.HexColor("#1a1a2e")
    DARK = colors.HexColor("#2c3e50")
    GREY = colors.HexColor("#555555")
    BLUE = colors.HexColor("#2563eb")

    base = getSampleStyleSheet()

    s_name = ParagraphStyle("Name", fontName="Helvetica-Bold", fontSize=20,
                            textColor=NAVY, spaceAfter=2, leading=24)
    s_contact = ParagraphStyle("Contact", fontName="Helvetica", fontSize=9,
                               textColor=GREY, spaceAfter=10, leading=13)
    s_section = ParagraphStyle("Section", fontName="Helvetica-Bold", fontSize=10,
                               textColor=NAVY, spaceBefore=12, spaceAfter=3,
                               leading=14, textTransform="uppercase",
                               letterSpacing=0.8)
    s_role = ParagraphStyle("Role", fontName="Helvetica-Bold", fontSize=9,
                            textColor=DARK, spaceBefore=7, spaceAfter=1, leading=13)
    s_body = ParagraphStyle("Body", fontName="Helvetica", fontSize=9,
                            textColor=colors.black, leading=13, spaceAfter=2)
    s_bullet = ParagraphStyle("Bullet", fontName="Helvetica", fontSize=9,
                              textColor=colors.black, leading=13,
                              leftIndent=12, firstLineIndent=-10, spaceAfter=1)
    s_link = ParagraphStyle("Link", parent=s_body, textColor=BLUE)

    # ── Parse markdown lines into flowables ───────────────────────────────────
    doc = SimpleDocTemplate(
        str(out), pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
    )

    story = []
    lines = markdown_text.splitlines()
    i = 0

    def _clean(text: str) -> str:
        """Strip markdown bold/italic markers and convert links."""
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
        text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
        text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2" color="#2563eb">\1</a>', text)
        return text

    while i < len(lines):
        line = lines[i].rstrip()

        if line.startswith("# "):
            story.append(Paragraph(line[2:], s_name))
            # next non-empty line(s) until h2 = contact block
            i += 1
            contact_parts = []
            while i < len(lines) and not lines[i].startswith("#"):
                l = lines[i].strip()
                if l and not l.startswith("-"):
                    contact_parts.append(_clean(l))
                i += 1
            if contact_parts:
                story.append(Paragraph("  |  ".join(contact_parts), s_contact))
            story.append(HRFlowable(width="100%", thickness=1.5, color=NAVY, spaceAfter=4))
            continue

        elif line.startswith("## "):
            story.append(Spacer(1, 2))
            story.append(Paragraph(line[3:], s_section))
            story.append(HRFlowable(width="100%", thickness=0.5,
                                    color=colors.HexColor("#d0d0d0"), spaceAfter=3))

        elif line.startswith("### "):
            story.append(Paragraph(_clean(line[4:]), s_role))

        elif line.startswith("- ") or line.startswith("* "):
            story.append(Paragraph("• " + _clean(line[2:]), s_bullet))

        elif line.startswith("**") and line.endswith("**"):
            story.append(Paragraph(_clean(line), s_body))

        elif line.strip():
            story.append(Paragraph(_clean(line), s_body))

        i += 1

    doc.build(story)
    return out
