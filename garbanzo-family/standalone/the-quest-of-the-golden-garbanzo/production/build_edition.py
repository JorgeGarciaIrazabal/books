#!/usr/bin/env python3
"""Build the publication cover, typeset PDF, and reflowable EPUB 3 for
The Quest of the Golden Garbanzo.

Reads chapter order and prose strictly from book.json and manuscript/*.md
without altering story wording. Run with ReportLab and Pillow:
    uv run --with reportlab --with pillow python production/build_edition.py
"""
from __future__ import annotations

import hashlib
import html
import json
import math
import re
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile, ZipInfo

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
)
from reportlab.platypus.tableofcontents import TableOfContents

BOOK = Path(__file__).resolve().parents[1]
OUT = BOOK / "exports"

XHTML_NS = "http://www.w3.org/1999/xhtml"
OPF_NS = "http://www.idpf.org/2007/opf"
EPUB_NS = "http://www.idpf.org/2007/ops"

FONT_REGULAR = Path(r"C:\Windows\Fonts\georgia.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\georgiab.ttf")
FONT_ITALIC = Path(r"C:\Windows\Fonts\georgiai.ttf")
FONT_BOLD_ITALIC = Path(r"C:\Windows\Fonts\georgiaz.ttf")
FONT_SANS = Path(r"C:\Windows\Fonts\arial.ttf")

PAGE = (6 * inch, 9 * inch)
MARGIN_X = 48
MARGIN_TOP = 52
MARGIN_BOTTOM = 50

INK = HexColor("#2b241d")
MUTED = HexColor("#6c5f4e")
GOLD = HexColor("#b5812a")

EPUB_CSS = """\
html { font-size: 100%; }
body { margin: 5%; font-family: Georgia, "DejaVu Serif", serif; line-height: 1.55; color: #2b241d; }
p { margin: 0 0 0.85em; orphans: 2; widows: 2; }
h1 { font-size: 1.65em; line-height: 1.22; margin: 1em 0 0.9em; break-after: avoid; page-break-after: avoid; }
code { font-family: system-ui, sans-serif; font-size: 0.9em; letter-spacing: 0.03em; }
nav li { margin-bottom: 0.6em; }
.cover-page { margin: 0; padding: 0; text-align: center; background: #fbf5e8; }
.cover-page img { max-width: 100%; max-height: 98vh; height: auto; }
.title-page { text-align: center; margin: 12% 8% 8%; }
.title-page .kicker { font-family: system-ui, sans-serif; font-size: 0.85em; letter-spacing: 0.18em; text-transform: uppercase; color: #6c5f4e; margin: 0 0 2.5em; }
.title-page h1 { font-size: 2.3em; line-height: 1.15; margin: 0; font-weight: normal; }
.title-page .rule { width: 4em; border: 0; border-top: 1px solid #b5812a; margin: 2em auto; }
.title-page .subtitle { font-style: italic; font-size: 1.1em; color: #5a4d3f; margin: 0 0 2.5em; }
.title-page .note { font-family: system-ui, sans-serif; font-size: 0.8em; letter-spacing: 0.06em; color: #6c5f4e; }
"""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def load_chapters() -> tuple[dict, list[dict]]:
    meta = json.loads((BOOK / "book.json").read_text(encoding="utf-8"))
    paths = meta["chapters"]
    if len(paths) != 10 or len(set(paths)) != len(paths):
        raise ValueError("Expected 10 distinct chapters in book.json")
    chapters = []
    for index, rel in enumerate(paths, 1):
        raw_bytes = (BOOK / rel).read_bytes()
        raw = raw_bytes.decode("utf-8").strip()
        heading, body = raw.split("\n", 1)
        if not heading.startswith("# "):
            raise ValueError(f"Expected '# ' heading in {rel}")
        title = heading[2:].strip()
        paragraphs = [norm(p) for p in re.split(r"\n\s*\n", body.strip()) if p.strip()]
        chapters.append(
            {
                "number": index,
                "source": rel,
                "title": title,
                "paragraphs": paragraphs,
                "sha256": sha256_bytes(raw_bytes),
            }
        )
    return meta, chapters


def md_to_rl_xml(text: str) -> str:
    escaped = html.escape(text, quote=False)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", escaped)
    return re.sub(r"`([^`]+?)`", r"<font face='Label' size='9.5'>\1</font>", escaped)


def md_to_xhtml_inline(text: str) -> str:
    escaped = html.escape(text, quote=False)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", escaped)
    return re.sub(r"`([^`]+?)`", r"<code>\1</code>", escaped)


def strip_md_markers(text: str) -> str:
    cleaned = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    cleaned = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"\1", cleaned)
    return re.sub(r"`([^`]+?)`", r"\1", cleaned)


def draw_centered_text(draw: ImageDraw.ImageDraw, text: str, y: int, font: ImageFont.FreeTypeFont, fill: str, width: int = 1440) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(((width - tw) / 2, y), text, font=font, fill=fill)
    return y + th


def build_cover(output: Path) -> bytes:
    scale = 2
    w, h = 720 * scale, 1080 * scale
    im = Image.new("RGB", (w, h), "#fbf5e8")
    draw = ImageDraw.Draw(im)

    # Outer and inner warm gold frames
    draw.rectangle([28 * scale, 28 * scale, w - 29 * scale, h - 29 * scale], outline="#b5812a", width=3 * scale)
    draw.rectangle([40 * scale, 40 * scale, w - 41 * scale, h - 41 * scale], outline="#d4b26a", width=1 * scale)

    f_kicker = ImageFont.truetype(str(FONT_SANS), 22 * scale)
    f_title = ImageFont.truetype(str(FONT_BOLD), 60 * scale)
    f_sub = ImageFont.truetype(str(FONT_ITALIC), 26 * scale)
    f_foot = ImageFont.truetype(str(FONT_SANS), 18 * scale)

    draw_centered_text(draw, "G A R B A N Z O   F A M I L Y", 130 * scale, f_kicker, "#6c5f4e", w)

    # Golden sunburst & chickpea seed emblem
    cx, cy = w // 2, 330 * scale
    for deg in range(0, 360, 20):
        rad = math.radians(deg)
        r_in = 62 * scale
        r_out = (98 if deg % 40 == 0 else 82) * scale
        x1 = cx + r_in * math.cos(rad)
        y1 = cy + r_in * math.sin(rad)
        x2 = cx + r_out * math.cos(rad)
        y2 = cy + r_out * math.sin(rad)
        draw.line([(x1, y1), (x2, y2)], fill="#c88d2a", width=(3 if deg % 40 == 0 else 2) * scale)
    draw.ellipse([cx - 52 * scale, cy - 52 * scale, cx + 52 * scale, cy + 52 * scale], fill="#f4dfaa", outline="#b5812a", width=3 * scale)
    draw.ellipse([cx - 34 * scale, cy - 28 * scale, cx + 34 * scale, cy + 32 * scale], fill="#d89b32", outline="#9c6a19", width=3 * scale)
    draw.arc([cx - 18 * scale, cy - 22 * scale, cx + 12 * scale, cy + 10 * scale], start=190, end=330, fill="#fff2cc", width=3 * scale)

    # Title block
    y = 485 * scale
    for line in ("The Quest", "of the Golden", "Garbanzo"):
        y = draw_centered_text(draw, line, y, f_title, "#2b241d", w) + 16 * scale

    draw.line([(w // 2 - 70 * scale, y + 26 * scale), (w // 2 + 70 * scale, y + 26 * scale)], fill="#b5812a", width=2 * scale)
    draw_centered_text(draw, "A Fun, Dramatic Family Adventure", y + 54 * scale, f_sub, "#5a4d3f", w)
    draw_centered_text(draw, "TEN CHAPTERS  ·  TEXT EDITION", h - 120 * scale, f_foot, "#6c5f4e", w)

    im = im.resize((720, 1080), Image.LANCZOS)
    output.parent.mkdir(parents=True, exist_ok=True)
    im.save(output, "JPEG", quality=92, optimize=True, progressive=False)
    return output.read_bytes()


class BookDoc(BaseDocTemplate):
    def __init__(self, filename: str, **kwargs):
        super().__init__(filename, **kwargs)
        self._chapter_keys: dict[str, str] = {}

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == "ChapterTitle":
            text = flowable.getPlainText()
            key = f"chapter-{len(self._chapter_keys) + 1:02d}"
            self._chapter_keys[key] = text
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=0, closed=False)
            self.notify("TOCEntry", (0, text, self.page))


def draw_plain_page(canv: canvas.Canvas, doc: BookDoc):
    pass


def draw_body_page(canv: canvas.Canvas, doc: BookDoc):
    canv.saveState()
    width, height = PAGE
    canv.setFillColor(INK)
    canv.setFont("Label", 7.5)
    canv.drawString(MARGIN_X, height - 30, "THE QUEST OF THE GOLDEN GARBANZO")
    canv.setFillColor(MUTED)
    canv.drawRightString(width - MARGIN_X, height - 30, "GARBANZO FAMILY")
    canv.setStrokeColor(GOLD)
    canv.setLineWidth(0.45)
    canv.line(MARGIN_X, height - 37, width - MARGIN_X, height - 37)
    canv.setFont("Story", 9)
    canv.setFillColor(MUTED)
    canv.drawCentredString(width / 2, 26, str(doc.page))
    canv.restoreState()


def build_pdf(meta: dict, chapters: list[dict], output: Path) -> tuple[bytes, int]:
    for name, path in [
        ("Story", FONT_REGULAR),
        ("StoryBold", FONT_BOLD),
        ("StoryItalic", FONT_ITALIC),
        ("StoryBoldItalic", FONT_BOLD_ITALIC),
        ("Label", FONT_SANS),
    ]:
        pdfmetrics.registerFont(TTFont(name, str(path)))
    pdfmetrics.registerFontFamily(
        "Story",
        normal="Story",
        bold="StoryBold",
        italic="StoryItalic",
        boldItalic="StoryBoldItalic",
    )

    body_style = ParagraphStyle(
        "Body", fontName="Story", fontSize=10.3, leading=14.6, textColor=INK,
        spaceAfter=5.0, alignment=0,
    )
    chapter_style = ParagraphStyle(
        "ChapterTitle", fontName="StoryBold", fontSize=15.5, leading=19.5, textColor=INK,
        spaceBefore=0, spaceAfter=14, keepWithNext=1,
    )
    title_style = ParagraphStyle(
        "Title", fontName="StoryBold", fontSize=26, leading=31, textColor=INK,
        alignment=TA_CENTER, spaceAfter=12,
    )
    series_style = ParagraphStyle(
        "Series", fontName="Label", fontSize=9, leading=14, textColor=MUTED,
        alignment=TA_CENTER, spaceAfter=26, charSpace=2.0,
    )
    sub_style = ParagraphStyle(
        "Sub", fontName="StoryItalic", fontSize=12, leading=17, textColor=MUTED,
        alignment=TA_CENTER, spaceBefore=14, spaceAfter=0,
    )
    notice_style = ParagraphStyle(
        "Notice", fontName="Label", fontSize=8, leading=12, textColor=MUTED,
        alignment=TA_CENTER, spaceBefore=30,
    )
    toc_head = ParagraphStyle(
        "TocHead", fontName="StoryBold", fontSize=16, leading=20, textColor=INK,
        spaceBefore=0, spaceAfter=16,
    )

    frame = Frame(
        MARGIN_X,
        MARGIN_BOTTOM,
        PAGE[0] - 2 * MARGIN_X,
        PAGE[1] - MARGIN_TOP - MARGIN_BOTTOM,
        id="body",
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    doc = BookDoc(
        str(output),
        pagesize=PAGE,
        leftMargin=MARGIN_X,
        rightMargin=MARGIN_X,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
        title=meta["title"],
        subject="Garbanzo Family adventure story",
        author="Garbanzo Family",
        creator="Book Studio",
    )
    doc.addPageTemplates(
        [
            PageTemplate(id="Plain", frames=[frame], onPage=draw_plain_page),
            PageTemplate(id="Body", frames=[frame], onPage=draw_body_page),
        ]
    )

    story = [
        Spacer(1, 95),
        Paragraph("GARBANZO FAMILY", series_style),
        Paragraph("The Quest of the<br/>Golden Garbanzo", title_style),
        Paragraph("A Fun, Dramatic Family Adventure", sub_style),
        Paragraph("TEN CHAPTERS", notice_style),
        PageBreak(),
        NextPageTemplate("Body"),
        Paragraph("Contents", toc_head),
    ]
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(
            "TOCEntry", fontName="Story", fontSize=10, leading=15, textColor=INK,
            leftIndent=0, firstLineIndent=0, spaceBefore=2,
        )
    ]
    toc.dotsMinLevel = -1
    story.append(toc)
    story.append(PageBreak())

    for idx, chapter in enumerate(chapters):
        if idx:
            story.append(PageBreak())
        story.append(Paragraph(html.escape(chapter["title"], quote=False), chapter_style))
        for p in chapter["paragraphs"]:
            story.append(Paragraph(md_to_rl_xml(p), body_style))

    doc.multiBuild(story)
    return output.read_bytes(), doc.page


def _xhtml(title: str, body: str, body_class: str = "") -> str:
    cls_attr = f' class="{body_class}"' if body_class else ""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<!DOCTYPE html>\n"
        f'<html xmlns="{XHTML_NS}" xmlns:epub="{EPUB_NS}" lang="en" xml:lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8"/>\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1"/>\n'
        f"<title>{html.escape(title, quote=False)}</title>\n"
        '<link rel="stylesheet" type="text/css" href="style.css"/>\n'
        "</head>\n"
        f"<body{cls_attr}>\n{body}\n</body>\n"
        "</html>\n"
    )


def build_epub(meta: dict, chapters: list[dict], cover_bytes: bytes, output: Path) -> bytes:
    entries: dict[str, str | bytes] = {}
    entries["style.css"] = EPUB_CSS
    entries["cover.jpg"] = cover_bytes
    entries["cover.xhtml"] = _xhtml(
        f"{meta['title']} Cover",
        '<section epub:type="cover"><img src="cover.jpg" alt="Cover of The Quest of the Golden Garbanzo"/></section>',
        "cover-page",
    )
    entries["title.xhtml"] = _xhtml(
        meta["title"],
        '<section class="title-page" epub:type="titlepage">\n'
        '  <p class="kicker">Garbanzo Family</p>\n'
        f'  <h1>{html.escape(meta["title"], quote=False)}</h1>\n'
        '  <hr class="rule" aria-hidden="true"/>\n'
        '  <p class="subtitle">A Fun, Dramatic Family Adventure</p>\n'
        '  <p class="note">Ten Chapters</p>\n'
        "</section>",
    )

    ch_files = []
    for ch in chapters:
        fname = f"chapter-{ch['number']:02d}.xhtml"
        paras = "\n".join(f"<p>{md_to_xhtml_inline(p)}</p>" for p in ch["paragraphs"])
        entries[fname] = _xhtml(
            ch["title"],
            f'<section epub:type="chapter" role="doc-chapter" id="chapter-{ch["number"]}">\n'
            f'<h1>{html.escape(ch["title"], quote=False)}</h1>\n'
            f"{paras}\n"
            "</section>",
        )
        ch_files.append((fname, ch["title"], ch["paragraphs"]))

    toc = [("title.xhtml", meta["title"])] + [(f, t) for f, t, _ in ch_files]
    nav_links = "\n".join(
        f'      <li><a href="{fname}">{html.escape(label, quote=False)}</a></li>'
        for fname, label in toc
    )
    entries["nav.xhtml"] = _xhtml(
        "Contents",
        '<nav epub:type="toc" id="toc" role="doc-toc">\n'
        "  <h1>Contents</h1>\n"
        f"  <ol>\n{nav_links}\n  </ol>\n"
        "</nav>\n"
        '<nav epub:type="landmarks" hidden="hidden">\n'
        "  <h2>Landmarks</h2>\n"
        "  <ol>\n"
        '    <li><a epub:type="cover" href="cover.xhtml">Cover</a></li>\n'
        '    <li><a epub:type="titlepage" href="title.xhtml">Title Page</a></li>\n'
        '    <li><a epub:type="bodymatter" href="chapter-01.xhtml">Start Reading</a></li>\n'
        "  </ol>\n"
        "</nav>",
    )

    identifier = "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL, "garbanzo-family/standalone/" + meta["id"]))
    description = (
        "A fun, dramatic, easy-to-read story about how ordinary humans Jorge, Marissa, and six-year-old Clara "
        "braved late-night spreadsheets, a confetti-blasting desk-bot, sneaky Spanish house pitches, and one last "
        "office bonus to earn sunny mornings together in Spain."
    )
    manifest_items = [
        '<item id="style" href="style.css" media-type="text/css"/>',
        '<item id="cover-image" href="cover.jpg" media-type="image/jpeg" properties="cover-image"/>',
        '<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>',
        '<item id="title" href="title.xhtml" media-type="application/xhtml+xml"/>',
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
    ]
    spine_items = ['<itemref idref="cover"/>', '<itemref idref="title"/>']
    for idx, (fname, _, _) in enumerate(ch_files, 1):
        cid = f"chapter-{idx:02d}"
        manifest_items.append(f'<item id="{cid}" href="{fname}" media-type="application/xhtml+xml"/>')
        spine_items.append(f'<itemref idref="{cid}"/>')

    opf = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<package xmlns="{OPF_NS}" version="3.0" unique-identifier="pub-id" xml:lang="en">\n'
        '  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        f'    <dc:identifier id="pub-id">{html.escape(identifier, quote=False)}</dc:identifier>\n'
        f'    <dc:title>{html.escape(meta["title"], quote=False)}</dc:title>\n'
        '    <dc:language>en</dc:language>\n'
        f'    <dc:description>{html.escape(description, quote=False)}</dc:description>\n'
        '    <meta property="rendition:layout">reflowable</meta>\n'
        '    <meta property="dcterms:modified">2026-11-23T23:30:00Z</meta>\n'
        '  </metadata>\n'
        '  <manifest>\n    ' + "\n    ".join(manifest_items) + "\n  </manifest>\n"
        '  <spine>\n    ' + "\n    ".join(spine_items) + "\n  </spine>\n"
        "</package>\n"
    )
    container = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
        '  <rootfiles>\n'
        '    <rootfile full-path="EPUB/package.opf" media-type="application/oebps-package+xml"/>\n'
        '  </rootfiles>\n'
        '</container>\n'
    )

    with ZipFile(output, "w") as zf:
        def add(name: str, val: str | bytes, comp: int = ZIP_DEFLATED):
            info = ZipInfo(name, (2026, 11, 23, 23, 30, 0))
            info.compress_type = comp
            zf.writestr(info, val if isinstance(val, bytes) else val.encode("utf-8"))

        add("mimetype", b"application/epub+zip", ZIP_STORED)
        add("META-INF/container.xml", container)
        add("EPUB/package.opf", opf)
        for fname, val in entries.items():
            add(f"EPUB/{fname}", val)

    # Strict validation of archive and prose fidelity
    with ZipFile(output) as zf:
        assert zf.testzip() is None
        assert zf.infolist()[0].filename == "mimetype"
        assert zf.infolist()[0].compress_type == ZIP_STORED
        assert zf.read("mimetype") == b"application/epub+zip"
        for name in zf.namelist():
            if name.endswith((".xml", ".xhtml", ".opf")):
                ET.fromstring(zf.read(name))
        for fname, title, expected_paras in ch_files:
            tree = ET.fromstring(zf.read(f"EPUB/{fname}"))
            h1 = "".join(tree.find(f".//{{{XHTML_NS}}}h1").itertext())
            assert h1 == title, f"{fname}: title mismatch"
            actual = [norm("".join(p.itertext())) for p in tree.findall(f".//{{{XHTML_NS}}}p")]
            expected_plain = [strip_md_markers(p) for p in expected_paras]
            assert actual == expected_plain, f"{fname}: paragraph prose mismatch"

    return output.read_bytes()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    meta, chapters = load_chapters()
    cover_path = OUT / "cover.jpg"
    cover_bytes = build_cover(cover_path)

    pdf_path = OUT / f"{meta['id']}.pdf"
    pdf_bytes, page_count = build_pdf(meta, chapters, pdf_path)

    epub_path = OUT / f"{meta['id']}.epub"
    epub_bytes = build_epub(meta, chapters, cover_bytes, epub_path)

    summary = {
        "cover": {"path": str(cover_path), "bytes": len(cover_bytes), "sha256": sha256_bytes(cover_bytes)},
        "pdf": {"path": str(pdf_path), "bytes": len(pdf_bytes), "sha256": sha256_bytes(pdf_bytes), "pages": page_count},
        "epub": {"path": str(epub_path), "bytes": len(epub_bytes), "sha256": sha256_bytes(epub_bytes)},
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
