"""Shared PDF building blocks (styles, tables, figures, callouts) for the paper and the summary."""
from datetime import datetime
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, Spacer, Table, TableStyle, HRFlowable
import config

P = config.PALETTE
INK, PRIMARY, TEAL, AMBER, CORAL, MIST, GRID, MUTED = (colors.HexColor(P[k]) for k in
                                                       ("ink", "primary", "teal", "amber", "coral", "mist", "grid", "muted"))
PAGE_W, PAGE_H = 595.27, 841.89
LM = RM = 48
TM, BM = 64, 52
FRAME_W, FRAME_H = PAGE_W - LM - RM, PAGE_H - TM - BM

S = {
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9.4, leading=13.6, alignment=TA_JUSTIFY,
                           textColor=INK, spaceAfter=5),
    "small": ParagraphStyle("small", fontName="Helvetica", fontSize=8.2, leading=11, textColor=INK, alignment=TA_LEFT),
    "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=17, leading=21, textColor=INK, spaceAfter=2),
    "kicker": ParagraphStyle("kicker", fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=CORAL, spaceAfter=1),
    "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=PRIMARY, spaceBefore=5, spaceAfter=3),
    "cap": ParagraphStyle("cap", fontName="Helvetica-Oblique", fontSize=7.8, leading=10, textColor=MUTED, spaceAfter=6),
    "bullet": ParagraphStyle("bullet", fontName="Helvetica", fontSize=9.2, leading=13, textColor=INK,
                             leftIndent=12, bulletIndent=2, spaceAfter=2.5, alignment=TA_LEFT),
    "callout": ParagraphStyle("callout", fontName="Helvetica", fontSize=9.2, leading=13, textColor=INK, alignment=TA_LEFT),
    "cell": ParagraphStyle("cell", fontName="Helvetica", fontSize=8, leading=10, textColor=INK),
    "cellb": ParagraphStyle("cellb", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=colors.white),
}


def today():
    return datetime.now().strftime("%d %B %Y")


def P_(text, style="body"):
    return Paragraph(text, S[style])


def section_head(num, kicker, title):
    return [P_(f"SECTION {num:02d}  |  {kicker.upper()}", "kicker"), P_(title, "h1"),
            HRFlowable(width="100%", thickness=1.6, color=AMBER, spaceBefore=1, spaceAfter=7)]


def bullets(items, style="bullet"):
    return [Paragraph(t, S[style], bulletText="\u2022") for t in items]


def callout(title, text, color=PRIMARY, width=FRAME_W):
    inner = [Paragraph(f"<b><font color='{P['primary']}'>{title}</font></b>", S["callout"]), Paragraph(text, S["callout"])]
    t = Table([[inner]], colWidths=[width])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), MIST), ("LINEBEFORE", (0, 0), (0, -1), 3.5, color),
                           ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return t


class FigCounter:
    n = 0


def figure(path, width_mm, caption):
    FigCounter.n += 1
    with PILImage.open(path) as im:
        w, h = im.size
    wpt = width_mm * mm
    img = Image(str(path), width=wpt, height=wpt * h / w)
    img.hAlign = "CENTER"
    return [img, P_(f"<b>Figure {FigCounter.n}.</b> {caption}", "cap")]


def table(rows, col_widths=None, header=True, align_right_from=1, font=8):
    data = []
    for i, r in enumerate(rows):
        row = []
        for j, c in enumerate(r):
            st = S["cellb"] if (header and i == 0) else S["cell"]
            row.append(Paragraph(str(c), st))
        data.append(row)
    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    style = [("BACKGROUND", (0, 0), (-1, 0), PRIMARY if header else MIST),
             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("LINEBELOW", (0, 0), (-1, -1), .4, GRID),
             ("TOPPADDING", (0, 0), (-1, -1), 3.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
             ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5)]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), MIST))
    t.setStyle(TableStyle(style))
    return t


def fmt_int(v):
    return f"{int(round(v)):,}"


def pct(v, d=1):
    return f"{v:.{d}f}%"


def strength(v):
    if v != v:
        return "undetermined"
    return "negligible" if v < .05 else "weak" if v < .15 else "moderate" if v < .30 else "strong"


def sig_text(c):
    if not c:
        return "could not be tested"
    return "statistically significant (p " + ("< 0.001" if c["p"] < .001 else f"= {c['p']:.3f}") + ")" if c["p"] < .05 \
        else f"not statistically significant (p = {c['p']:.2f})"
