#!/usr/bin/env python3
"""
Gera PDF da documentação FP&A combinando todos os arquivos Markdown.
Uso: python _gerar_pdf.py
"""

import re
import sys
import os
from pathlib import Path
from datetime import date

# ── Garantir reportlab instalado ─────────────────────────────────────────────
try:
    from reportlab.lib.pagesizes import A4
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "reportlab"], check=True)
    from reportlab.lib.pagesizes import A4

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, HRFlowable,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Configuração de fontes ────────────────────────────────────────────────────
# Tenta registrar Arial (Windows) para suporte a Unicode (→ ↓ × ◦ etc.)
# Se falhar, usa Helvetica + substituições ASCII.

FONTS_DIR = r"C:\Windows\Fonts"
FONT_NORMAL = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_ITALIC = "Helvetica-Oblique"
FONT_BOLDITALIC = "Helvetica-BoldOblique"
FONT_MONO = "Courier"
USE_UNICODE = False

def _register_fonts():
    global FONT_NORMAL, FONT_BOLD, FONT_ITALIC, FONT_BOLDITALIC, USE_UNICODE
    registered = False
    try:
        pdfmetrics.registerFont(TTFont("FPANormal", os.path.join(FONTS_DIR, "arial.ttf")))
        pdfmetrics.registerFont(TTFont("FPABold",   os.path.join(FONTS_DIR, "arialbd.ttf")))
        pdfmetrics.registerFont(TTFont("FPAItalic", os.path.join(FONTS_DIR, "ariali.ttf")))
        pdfmetrics.registerFont(TTFont("FPABold2",  os.path.join(FONTS_DIR, "arialbi.ttf")))
        from reportlab.lib.fonts import addMapping
        addMapping("FPANormal", 0, 0, "FPANormal")
        addMapping("FPANormal", 1, 0, "FPABold")
        addMapping("FPANormal", 0, 1, "FPAItalic")
        addMapping("FPANormal", 1, 1, "FPABold2")
        FONT_NORMAL = "FPANormal"
        FONT_BOLD   = "FPABold"
        FONT_ITALIC = "FPAItalic"
        FONT_BOLDITALIC = "FPABold2"
        USE_UNICODE = True
        registered = True
    except Exception as e:
        print(f"  Arial nao disponivel ({e}), usando Helvetica")
    if registered:
        print("  Fonte Arial registrada (Unicode completo)")

_register_fonts()

# Substituições para Helvetica (quando Unicode não disponível)
_SUBS = {
    "→": "->", "←": "<-", "↓": "v", "↑": "^",
    "↔": "<->", "◦": "-", "•": "*", "✓": "[OK]",
    "✗": "[X]", "✘": "[X]", "’": "'", "‘": "'",
    "“": '"', "”": '"', "–": "-", "—": "--",
    "·": "*",
}

def _sanitize(text: str) -> str:
    if USE_UNICODE:
        return text
    for ch, repl in _SUBS.items():
        text = text.replace(ch, repl)
    return text

# ── Dimensões e Cores ─────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4
MARGIN = 2.5 * cm
AW = PAGE_W - 2 * MARGIN  # largura disponível

C_DARK   = colors.HexColor("#1e3a5f")
C_BLUE   = colors.HexColor("#2563eb")
C_LBLUE  = colors.HexColor("#eff6ff")
C_GRAY   = colors.HexColor("#f1f5f9")
C_BORDER = colors.HexColor("#cbd5e1")
C_BLACK  = colors.HexColor("#0f172a")
C_MUTED  = colors.HexColor("#64748b")
C_CBKG   = colors.HexColor("#f8fafc")


def _ps(name, **kw) -> ParagraphStyle:
    d = dict(fontName=FONT_NORMAL, fontSize=10, textColor=C_BLACK, leading=14,
             spaceBefore=0, spaceAfter=4)
    d.update(kw)
    return ParagraphStyle(name, **d)


def _build_styles() -> dict:
    return {
        "cover_title": _ps("ct", fontSize=26, fontName=FONT_BOLD,
                            textColor=C_DARK, alignment=TA_CENTER, spaceAfter=10),
        "cover_sub":   _ps("cs", fontSize=15, textColor=C_BLUE,
                            alignment=TA_CENTER, spaceAfter=28),
        "cover_desc":  _ps("cd", fontSize=11, textColor=C_MUTED,
                            alignment=TA_CENTER, leading=17),
        "cover_date":  _ps("cdt", fontSize=9, textColor=C_MUTED, alignment=TA_CENTER),
        "toc_name":    _ps("tn", fontSize=11, fontName=FONT_BOLD, textColor=C_DARK),
        "toc_desc":    _ps("td2", fontSize=10),
        "sec_title":   _ps("st", fontSize=20, fontName=FONT_BOLD, textColor=C_DARK, spaceAfter=4),
        "sec_sub":     _ps("ss", fontSize=10, textColor=C_MUTED),
        "h1": _ps("h1", fontSize=17, fontName=FONT_BOLD, textColor=C_DARK,   spaceBefore=16, spaceAfter=6),
        "h2": _ps("h2", fontSize=14, fontName=FONT_BOLD, textColor=C_DARK,   spaceBefore=12, spaceAfter=5),
        "h3": _ps("h3", fontSize=12, fontName=FONT_BOLD, textColor=colors.HexColor("#1e40af"), spaceBefore=9, spaceAfter=4),
        "h4": _ps("h4", fontSize=10, fontName=FONT_BOLD, spaceBefore=7, spaceAfter=3),
        "h5": _ps("h5", fontSize=9,  fontName=FONT_ITALIC, spaceBefore=5, spaceAfter=2),
        "h6": _ps("h6", fontSize=9,  fontName=FONT_ITALIC, textColor=C_MUTED, spaceBefore=5, spaceAfter=2),
        "body":  _ps("body", spaceBefore=2, spaceAfter=5),
        "bq":    _ps("bq", fontName=FONT_ITALIC, fontSize=9.5, textColor=C_MUTED, spaceBefore=4, spaceAfter=4),
        "li":    _ps("li",  leftIndent=16, spaceBefore=2, spaceAfter=2),
        "li2":   _ps("li2", leftIndent=30, spaceBefore=1, spaceAfter=1, fontSize=9.5),
        "th":    _ps("th",  fontSize=9, fontName=FONT_BOLD, textColor=colors.white),
        "td":    _ps("td",  fontSize=9, leading=12),
        "code":  _ps("code", fontName=FONT_MONO, fontSize=8, leading=11),
        "footer":_ps("footer", fontSize=8, textColor=C_MUTED),
    }


ST = _build_styles()


# ── Helpers de formatação ─────────────────────────────────────────────────────

def esc(t: str) -> str:
    """Escapa XML para ReportLab (deve rodar ANTES de fmt)."""
    return _sanitize(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fmt(t: str) -> str:
    """Aplica formatação inline Markdown (deve rodar APÓS esc)."""
    # Código inline — backtick
    t = re.sub(
        r'`([^`]+)`',
        lambda m: f'<font name="{FONT_MONO}" size="8" color="#1e3a5f">{m.group(1)}</font>',
        t,
    )
    # Bold+Italic
    t = re.sub(r'\*\*\*(.+?)\*\*\*', rf'<b><i>\1</i></b>', t)
    # Bold
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    # Italic
    t = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'<i>\1</i>', t)
    return t


def _code_block(lines: list[str]) -> Table:
    code = "<br/>".join(esc(ln) for ln in lines) or "&nbsp;"
    t = Table([[Paragraph(code, ST["code"])]], colWidths=[AW])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C_CBKG),
        ("BOX",           (0,0),(-1,-1), 0.5, C_BORDER),
        ("LEFTPADDING",   (0,0),(-1,-1), 10),
        ("RIGHTPADDING",  (0,0),(-1,-1), 10),
        ("TOPPADDING",    (0,0),(-1,-1), 8),
        ("BOTTOMPADDING", (0,0),(-1,-1), 8),
    ]))
    return t


def _make_table(rows: list[str]) -> Table | None:
    data = []
    for r in rows:
        if re.match(r'^\|[-| :]+\|$', r.strip()):
            continue
        cells = [c.strip() for c in r.strip().strip("|").split("|")]
        data.append(cells)
    if not data:
        return None
    ncols = max(len(r) for r in data)
    for r in data:
        while len(r) < ncols:
            r.append("")
    tdata = []
    for i, row in enumerate(data):
        st = ST["th"] if i == 0 else ST["td"]
        tdata.append([Paragraph(fmt(esc(c)), st) for c in row])
    cw = AW / ncols
    t = Table(tdata, colWidths=[cw] * ncols, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0), C_DARK),
        ("GRID",          (0,0),(-1,-1), 0.4, C_BORDER),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.white, C_GRAY]),
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ("LEFTPADDING",   (0,0),(-1,-1), 6),
        ("RIGHTPADDING",  (0,0),(-1,-1), 6),
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
    ]))
    return t


def _blockquote(lines: list[str]) -> Table:
    text = " ".join(ln.strip().lstrip(">").strip() for ln in lines)
    t = Table([[Paragraph(fmt(esc(text)), ST["bq"])]], colWidths=[AW])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), C_LBLUE),
        ("LINEBEFORE",   (0,0),(0,-1), 3, C_BLUE),
        ("LEFTPADDING",  (0,0),(-1,-1), 14),
        ("RIGHTPADDING", (0,0),(-1,-1), 10),
        ("TOPPADDING",   (0,0),(-1,-1), 6),
        ("BOTTOMPADDING",(0,0),(-1,-1), 6),
    ]))
    return t


# ── Parser Markdown ───────────────────────────────────────────────────────────

def _is_special(s: str) -> bool:
    """Retorna True se a linha deve interromper acumulação de parágrafo."""
    return (
        not s
        or s.startswith("#")
        or s.startswith("|")
        or s.startswith(">")
        or s.startswith("```")
        or bool(re.match(r'^[-*+]\s', s))
        or bool(re.match(r'^\d+\.\s', s))
        or bool(re.match(r'^[-*_]{3,}\s*$', s))
    )


def parse_md(content: str) -> list:
    flows = []
    lines = content.split("\n")
    i = 0

    while i < len(lines):
        ln  = lines[i]
        s   = ln.strip()

        # Linha em branco
        if not s:
            i += 1
            continue

        # Bloco de código
        if s.startswith("```"):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1
            flows += [Spacer(1, 4), _code_block(code_lines), Spacer(1, 8)]
            continue

        # Linha horizontal
        if re.match(r'^[-*_]{3,}\s*$', s):
            flows += [Spacer(1,6), HRFlowable(width="100%", thickness=0.4, color=C_BORDER), Spacer(1,6)]
            i += 1
            continue

        # Heading
        m = re.match(r'^(#{1,6})\s+(.+)$', ln)
        if m:
            lvl = len(m.group(1))
            txt = fmt(esc(m.group(2).strip()))
            hk  = f"h{min(lvl, 6)}"
            if lvl == 1:
                flows += [Spacer(1,8), HRFlowable(width="100%", thickness=1.5, color=C_DARK), Spacer(1,4)]
            elif lvl == 2:
                flows.append(Spacer(1, 6))
            flows.append(Paragraph(txt, ST[hk]))
            i += 1
            continue

        # Tabela
        if s.startswith("|"):
            tbl_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                tbl_lines.append(lines[i])
                i += 1
            t = _make_table(tbl_lines)
            if t:
                flows += [Spacer(1,6), t, Spacer(1,10)]
            continue

        # Blockquote
        if s.startswith(">"):
            bq_lines = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                bq_lines.append(lines[i])
                i += 1
            flows += [Spacer(1,4), _blockquote(bq_lines), Spacer(1,8)]
            continue

        # Item de lista
        m = re.match(r'^(\s*)([-*+]|\d+\.)\s+(.+)$', ln)
        if m:
            indent = len(m.group(1))
            txt    = fmt(esc(m.group(3)))
            bullet = "->" if (m.group(2)[0].isdigit()) else ("*" if indent < 4 else "-")
            st     = ST["li"] if indent < 4 else ST["li2"]
            flows.append(Paragraph(f"{bullet}  {txt}", st))
            i += 1
            continue

        # Parágrafo — acumula linhas consecutivas
        para = []
        while i < len(lines) and not _is_special(lines[i].strip()):
            para.append(lines[i].strip())
            i += 1
        if para:
            txt = fmt(esc(" ".join(para)))
            flows.append(Paragraph(txt, ST["body"]))

    return flows


# ── Capa ──────────────────────────────────────────────────────────────────────

def _cover_page() -> list:
    docs = [
        ("README",            "Visao geral, stack, setup e deploy"),
        ("API",               "Referencia completa de endpoints"),
        ("Banco de Dados",    "Schema, tabelas, views e migrations"),
        ("ETL",               "Pipeline SIA -> DW"),
        ("Queries",           "Todas as queries: ETL, DW, API e Views"),
        ("Decisoes Tecnicas", "Architecture Decision Records"),
    ]
    toc = Table(
        [[Paragraph(f"<b>{n}</b>", ST["toc_name"]),
          Paragraph(d, ST["toc_desc"])] for n, d in docs],
        colWidths=[5*cm, AW - 5*cm],
    )
    toc.setStyle(TableStyle([
        ("ROWBACKGROUNDS",(0,0),(-1,-1), [C_GRAY, colors.white]),
        ("TOPPADDING",   (0,0),(-1,-1), 8),
        ("BOTTOMPADDING",(0,0),(-1,-1), 8),
        ("LEFTPADDING",  (0,0),(-1,-1), 12),
        ("RIGHTPADDING", (0,0),(-1,-1), 12),
        ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
        ("LINEABOVE",    (0,0),(-1,0),  0.5, C_BORDER),
        ("LINEBELOW",    (0,-1),(-1,-1),0.5, C_BORDER),
    ]))
    return [
        Spacer(1, 4*cm),
        Paragraph("FP&amp;A Financeiro", ST["cover_title"]),
        Paragraph("Documentacao Tecnica", ST["cover_sub"]),
        HRFlowable(width="50%", thickness=2, color=C_BLUE, hAlign="CENTER"),
        Spacer(1, 1*cm),
        Paragraph(
            "Plataforma interna de planejamento orcamentario e acompanhamento "
            "Realizado x Orcado, integrada ao ERP System SIA.",
            ST["cover_desc"],
        ),
        Spacer(1, 1.5*cm),
        toc,
        Spacer(1, 2*cm),
        Paragraph(f"Gerado em {date.today().strftime('%d/%m/%Y')}", ST["cover_date"]),
        PageBreak(),
    ]


def _section_header(title: str, subtitle: str) -> list:
    ht = Table(
        [[Paragraph(esc(title),    ST["sec_title"])],
         [Paragraph(esc(subtitle), ST["sec_sub"])]],
        colWidths=[AW],
    )
    ht.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), C_GRAY),
        ("LEFTPADDING",  (0,0),(-1,-1), 16),
        ("TOPPADDING",   (0,0),(0,0),   16),
        ("BOTTOMPADDING",(0,-1),(-1,-1),14),
        ("LINEBELOW",    (0,-1),(-1,-1), 2, C_DARK),
    ]))
    return [ht, Spacer(1, 14)]


# ── Cabeçalho / Rodapé ───────────────────────────────────────────────────────

def _on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont(FONT_NORMAL if USE_UNICODE else "Helvetica", 8)
    canvas.setFillColor(C_MUTED)
    y = 1.2 * cm
    canvas.drawString(MARGIN, y, "FP&A Financeiro - Documentacao Tecnica")
    canvas.drawRightString(PAGE_W - MARGIN, y, f"Pagina {canvas.getPageNumber()}")
    canvas.setStrokeColor(C_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 1.5*cm, PAGE_W - MARGIN, 1.5*cm)
    canvas.restoreState()


# ── Main ─────────────────────────────────────────────────────────────────────

FILES = [
    (r"C:\Users\thiago.gaitkoski\financeiro-fpa\README.md",
     "README",
     "Visao geral, stack, setup e deploy"),
    (r"C:\Users\thiago.gaitkoski\financeiro-fpa\docs\API.md",
     "API - Referencia Completa",
     "Todos os endpoints com parametros e exemplos"),
    (r"C:\Users\thiago.gaitkoski\financeiro-fpa\docs\BANCO_DE_DADOS.md",
     "Banco de Dados",
     "Schema completo: tabelas, colunas, views e migrations"),
    (r"C:\Users\thiago.gaitkoski\financeiro-fpa\docs\ETL.md",
     "ETL",
     "Pipeline SIA -> DW: extracao, transformacao e carga"),
    (r"C:\Users\thiago.gaitkoski\financeiro-fpa\docs\QUERIES.md",
     "Queries",
     "Todas as queries do projeto: ETL (SIA), carga DW, API analitica e views"),
    (r"C:\Users\thiago.gaitkoski\financeiro-fpa\docs\DECISOES_TECNICAS.md",
     "Decisoes Tecnicas",
     "Architecture Decision Records (ADRs)"),
]
OUTPUT = r"C:\Users\thiago.gaitkoski\financeiro-fpa\docs\FPA_Documentacao_Tecnica.pdf"


def main():
    doc = SimpleDocTemplate(
        OUTPUT, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=2*cm, bottomMargin=2*cm,
        title="FP&A Financeiro - Documentacao Tecnica",
    )

    story = _cover_page()

    for idx, (fpath, title, subtitle) in enumerate(FILES):
        p = Path(fpath)
        if not p.exists():
            print(f"  SKIP (não encontrado): {fpath}")
            continue
        content = p.read_text(encoding="utf-8")
        story.extend(_section_header(title, subtitle))
        story.extend(parse_md(content))
        if idx < len(FILES) - 1:
            story.append(PageBreak())

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    print(f"\nPDF gerado: {OUTPUT}")


if __name__ == "__main__":
    main()
