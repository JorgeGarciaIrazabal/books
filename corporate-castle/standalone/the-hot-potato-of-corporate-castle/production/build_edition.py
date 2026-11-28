#!/usr/bin/env python3
"""Build the typographic cover, typeset 6x9 PDF, and reflowable EPUB 3 for
The Hot Potato of Corporate Castle (Preview Edition: Prologue & Chapter One).

Reads all chapters registered in book.json strictly from manuscript/*.md
without altering story wording.

Run with ReportLab and Pillow:
    uv run --with reportlab --with pillow python production/build_edition.py
"""
from __future__ import annotations

import hashlib
import html
import json
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

BOOK = Path(__file__).resolve().parents[1]
OUT = BOOK / "exports"

XHTML_NS = "http://www.w3.org/1999/xhtml"
OPF_NS = "http://www.idpf.org/2007/opf"
EPUB_NS = "http://www.idpf.org/2007/ops"

FONT_CANDIDATES = {
    "regular": [
        Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"),
        Path("C:/Windows/Fonts/georgia.ttf"),
        Path("C:/Windows/Fonts/times.ttf"),
    ],
    "bold": [
        Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"),
        Path("C:/Windows/Fonts/georgiab.ttf"),
        Path("C:/Windows/Fonts/timesbd.ttf"),
    ],
    "italic": [
        Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"),
        Path("C:/Windows/Fonts/georgiai.ttf"),
        Path("C:/Windows/Fonts/timesi.ttf"),
    ],
    "bold_italic": [
        Path("/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf"),
        Path("C:/Windows/Fonts/georgiaz.ttf"),
        Path("C:/Windows/Fonts/timesbi.ttf"),
    ],
    "sans": [
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeui.ttf"),
    ],
    "sans_bold": [
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf"),
    ],
}


def pick_font(role: str) -> Path:
    for cand in FONT_CANDIDATES[role]:
        if cand.is_file():
            return cand
    raise FileNotFoundError(f"No TTF font found for role {role!r}")


PAGE = (6 * inch, 9 * inch)
MARGIN_X = 48
MARGIN_TOP = 52
MARGIN_BOTTOM = 48

INK = HexColor("#22262e")
MUTED = HexColor("#5e6573")
BRASS = HexColor("#b48b48")
LAVENDER = HexColor("#9a86b3")

EPUB_CSS = """\
html { font-size: 100%; }
body { margin: 5%; font-family: Georgia, "Liberation Serif", "DejaVu Serif", serif; line-height: 1.6; color: #22262e; }
p { margin: 0 0 0.9em; orphans: 2; widows: 2; }
h1 { font-size: 1.65em; line-height: 1.25; margin: 1em 0 1em; break-after: avoid; page-break-after: avoid; }
hr.scene-break { border: 0; text-align: center; margin: 1.5em auto; width: 4em; border-top: 1px solid #b48b48; }
nav li { margin-bottom: 0.6em; }
.cover-page { margin: 0; padding: 0; text-align: center; background: #1d2430; }
.cover-page img { max-width: 100%; max-height: 98vh; height: auto; }
.title-page { text-align: center; margin: 14% 8% 8%; }
.title-page .kicker { font-family: system-ui, sans-serif; font-size: 0.85em; letter-spacing: 0.2em; text-transform: uppercase; color: #5e6573; margin: 0 0 2.4em; }
.title-page h1 { font-size: 2.25em; line-height: 1.18; margin: 0; font-weight: normal; }
.title-page .rule { width: 4.5em; border: 0; border-top: 1px solid #b48b48; margin: 2em auto; }
.title-page .subtitle { font-style: italic; font-size: 1.1em; color: #4d5563; margin: 0 0 2.4em; }
.title-page .note { font-family: system-ui, sans-serif; font-size: 0.8em; letter-spacing: 0.08em; text-transform: uppercase; color: #5e6573; }
"""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def is_scene_break(block: str) -> bool:
    return block.strip() in {"---", "***", "* * *"}


def load_chapters() -> tuple[dict, list[dict]]:
    meta = json.loads((BOOK / "book.json").read_text(encoding="utf-8"))
    chapters: list[dict] = []
    for idx, rel in enumerate(meta["chapters"]):
        src = BOOK / rel
        raw_bytes = src.read_bytes()
        raw = raw_bytes.decode("utf-8").replace("\r\n", "\n").strip()
        heading, body = raw.split("\n", 1)
        if not heading.startswith("# "):
            raise ValueError(f"Expected '# ' heading in {rel}")
        title = heading[2:].strip()
        blocks = [norm(p) for p in re.split(r"\n\s*\n", body.strip()) if p.strip()]
        slug = "prologue" if idx == 0 and title.lower().startswith("prologue") else f"chapter-{idx:02d}"
        chapters.append(
            {
                "id": slug,
                "filename": f"{slug}.xhtml",
                "source": rel,
                "title": title,
                "blocks": blocks,
                "sha256": sha256_bytes(raw_bytes),
                "is_prologue": slug == "prologue",
            }
        )
    return meta, chapters


def md_to_rl_xml(text: str) -> str:
    escaped = html.escape(text, quote=False)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    return re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", escaped)


def md_to_xhtml_inline(text: str) -> str:
    escaped = html.escape(text, quote=False)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    return re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", escaped)


def strip_md_markers(text: str) -> str:
    cleaned = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    return re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"\1", cleaned)


def draw_centered(draw: ImageDraw.ImageDraw, width: int, y: int, text: str, font: ImageFont.FreeTypeFont, fill: tuple[int, int, int]) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (width - tw) / 2
    draw.text((x, y), text, font=font, fill=fill)
    return y + th


def build_cover(output: Path) -> bytes:
    """Create a crisp 720x1080 typographic cover in slate, brass, and muted lavender."""
    w, h = 1440, 2160  # 2x supersampled -> 720x1080
    bg = (29, 36, 48)          # Liability Tower charcoal slate
    panel = (36, 45, 60)
    ivory = (245, 240, 230)
    soft_ivory = (212, 205, 194)
    brass = (196, 155, 86)
    lavender = (176, 154, 204)

    im = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(im)

    # Subtle architectural inner panel
    d.rectangle([88, 88, w - 89, h - 89], fill=panel)

    # Double brass border frame
    d.rectangle([62, 62, w - 63, h - 63], outline=brass, width=5)
    d.rectangle([88, 88, w - 89, h - 89], outline=(138, 114, 72), width=2)

    # Minimal twin-spire geometric motif in the lower middle (Tower of Vibes vs Liability Tower + moat)
    cx = w // 2
    moat_y = 1660
    # Left spire (Tower of Vibes — slender lavender silhouette)
    d.polygon(
        [(cx - 210, moat_y - 24), (cx - 190, moat_y - 280), (cx - 150, moat_y - 340),
         (cx - 110, moat_y - 280), (cx - 90, moat_y - 24)],
        outline=lavender,
        width=4,
    )
    # Right spire (Liability Tower — austere brass silhouette)
    d.polygon(
        [(cx + 90, moat_y - 24), (cx + 100, moat_y - 310), (cx + 150, moat_y - 355),
         (cx + 200, moat_y - 310), (cx + 210, moat_y - 24)],
        outline=brass,
        width=4,
    )
    # Moat line
    d.line([(cx - 270, moat_y), (cx + 270, moat_y)], fill=(120, 134, 154), width=3)

    f_kicker = ImageFont.truetype(str(pick_font("sans_bold")), 36)
    f_title = ImageFont.truetype(str(pick_font("bold")), 116)
    f_sub = ImageFont.truetype(str(pick_font("italic")), 50)
    f_badge = ImageFont.truetype(str(pick_font("sans_bold")), 34)
    f_foot = ImageFont.truetype(str(pick_font("sans")), 30)

    y = 240
    y = draw_centered(d, w, y, "C O R P O R A T E   C A S T L E", f_kicker, brass) + 90

    # Brass + lavender divider
    d.line([(cx - 160, y), (cx - 24, y)], fill=lavender, width=4)
    d.ellipse([cx - 8, y - 8, cx + 8, y + 8], fill=brass)
    d.line([(cx + 24, y), (cx + 160, y)], fill=brass, width=4)
    y += 110

    y = draw_centered(d, w, y, "The Hot Potato", f_title, ivory) + 46
    y = draw_centered(d, w, y, "of", f_sub, soft_ivory) + 34
    y = draw_centered(d, w, y, "Corporate Castle", f_title, ivory) + 110

    # Preview pill box (vertically centered using exact textbbox ascent)
    pill_text = "PREVIEW EDITION"
    bbox = d.textbbox((0, 0), pill_text, font=f_badge)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    pw = tw + 88
    ph = th + 48
    d.rounded_rectangle([cx - pw // 2, y, cx + pw // 2, y + ph], radius=12, outline=lavender, width=3)
    text_y = y + (ph - th) / 2 - bbox[1]
    d.text(((w - tw) / 2, text_y), pill_text, font=f_badge, fill=ivory)

    draw_centered(d, w, 1820, "A Satirical Corporate Fantasy", f_sub, soft_ivory)
    draw_centered(d, w, 1930, "WORK IN PROGRESS  ·  PROLOGUE & CHAPTER ONE", f_foot, brass)

    final = im.resize((720, 1080), Image.LANCZOS)
    output.parent.mkdir(parents=True, exist_ok=True)
    final.save(output, "JPEG", quality=92, optimize=True, progressive=False)
    return output.read_bytes()


class BookDoc(BaseDocTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._bookmark_idx = 0

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == "ChapterTitle":
            text = flowable.getPlainText()
            key = f"chap-{self._bookmark_idx}"
            self._bookmark_idx += 1
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=0, closed=False)


def draw_plain_page(canv: canvas.Canvas, doc: BookDoc):
    pass


def draw_body_page(canv: canvas.Canvas, doc: BookDoc):
    canv.saveState()
    width, height = PAGE
    canv.setFillColor(INK)
    canv.setFont("Label", 7.5)
    canv.drawString(MARGIN_X, height - 32, "THE HOT POTATO OF CORPORATE CASTLE")
    canv.setFillColor(MUTED)
    canv.drawRightString(width - MARGIN_X, height - 32, "PREVIEW EDITION")
    canv.setStrokeColor(BRASS)
    canv.setLineWidth(0.5)
    canv.line(MARGIN_X, height - 39, width - MARGIN_X, height - 39)
    canv.setFont("Story", 9)
    canv.setFillColor(MUTED)
    canv.drawCentredString(width / 2, 28, str(doc.page))
    canv.restoreState()


def build_pdf(meta: dict, chapters: list[dict], cover_path: Path, output: Path) -> tuple[bytes, int]:
    for name, role in [
        ("Story", "regular"),
        ("StoryBold", "bold"),
        ("StoryItalic", "italic"),
        ("StoryBoldItalic", "bold_italic"),
        ("Label", "sans"),
    ]:
        pdfmetrics.registerFont(TTFont(name, str(pick_font(role))))
    pdfmetrics.registerFontFamily(
        "Story",
        normal="Story",
        bold="StoryBold",
        italic="StoryItalic",
        boldItalic="StoryBoldItalic",
    )

    body_style = ParagraphStyle(
        "Body", fontName="Story", fontSize=10.3, leading=14.8, textColor=INK,
        spaceAfter=6.5, alignment=0,
    )
    scene_break_style = ParagraphStyle(
        "SceneBreak", fontName="Story", fontSize=10.5, leading=14, textColor=BRASS,
        alignment=TA_CENTER, spaceBefore=8, spaceAfter=10,
    )
    chapter_style = ParagraphStyle(
        "ChapterTitle", fontName="StoryBold", fontSize=16.5, leading=21, textColor=INK,
        spaceBefore=0, spaceAfter=16, keepWithNext=1,
    )
    title_style = ParagraphStyle(
        "Title", fontName="StoryBold", fontSize=26, leading=32, textColor=INK,
        alignment=TA_CENTER, spaceAfter=12,
    )
    series_style = ParagraphStyle(
        "Series", fontName="Label", fontSize=9, leading=14, textColor=MUTED,
        alignment=TA_CENTER, spaceAfter=28, charSpace=2.0,
    )
    sub_style = ParagraphStyle(
        "Sub", fontName="StoryItalic", fontSize=12.5, leading=18, textColor=MUTED,
        alignment=TA_CENTER, spaceBefore=16, spaceAfter=0,
    )
    notice_style = ParagraphStyle(
        "Notice", fontName="Label", fontSize=8.2, leading=12.5, textColor=MUTED,
        alignment=TA_CENTER, spaceBefore=34,
    )

    frame_w = PAGE[0] - 2 * MARGIN_X
    frame = Frame(
        MARGIN_X,
        MARGIN_BOTTOM,
        frame_w,
        PAGE[1] - MARGIN_TOP - MARGIN_BOTTOM,
        id="body",
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    cover_frame = Frame(0, 0, PAGE[0], PAGE[1], id="cover", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)

    def draw_cover_page(canv: canvas.Canvas, doc: BookDoc):
        canv.drawImage(str(cover_path), 0, 0, width=PAGE[0], height=PAGE[1], preserveAspectRatio=False)

    doc = BookDoc(
        str(output),
        pagesize=PAGE,
        leftMargin=MARGIN_X,
        rightMargin=MARGIN_X,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
        title=f"{meta['title']} (Preview Edition)",
        subject="Corporate Castle satirical fantasy preview edition (Prologue & Chapter One)",
        author="Corporate Castle",
        creator="Book Studio",
    )
    doc.addPageTemplates(
        [
            PageTemplate(id="Cover", frames=[cover_frame], onPage=draw_cover_page),
            PageTemplate(id="Plain", frames=[frame], onPage=draw_plain_page),
            PageTemplate(id="Body", frames=[frame], onPage=draw_body_page),
        ]
    )

    story = [
        NextPageTemplate("Plain"),
        Spacer(1, 1),
        PageBreak(),
        Spacer(1, 115),
        Paragraph("CORPORATE CASTLE", series_style),
        Paragraph("The Hot Potato of<br/>Corporate Castle", title_style),
        Paragraph("A Satirical Corporate Fantasy", sub_style),
        Paragraph("PREVIEW EDITION  ·  PROLOGUE &amp; CHAPTER ONE", notice_style),
        NextPageTemplate("Body"),
    ]
    for chap in chapters:
        story.append(PageBreak())
        story.append(Paragraph(html.escape(chap["title"], quote=False), chapter_style))
        for block in chap["blocks"]:
            if is_scene_break(block):
                story.append(Paragraph("*   *   *", scene_break_style))
            else:
                story.append(Paragraph(md_to_rl_xml(block), body_style))

    doc.build(story)
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
        '<section epub:type="cover"><img src="cover.jpg" alt="Typographic cover of The Hot Potato of Corporate Castle: Preview Edition"/></section>',
        "cover-page",
    )
    entries["title.xhtml"] = _xhtml(
        meta["title"],
        '<section class="title-page" epub:type="titlepage">\n'
        '  <p class="kicker">Corporate Castle</p>\n'
        f'  <h1>{html.escape(meta["title"], quote=False)}</h1>\n'
        '  <hr class="rule" aria-hidden="true"/>\n'
        '  <p class="subtitle">A Satirical Corporate Fantasy</p>\n'
        '  <p class="note">Preview Edition · Prologue &amp; Chapter One</p>\n'
        "</section>",
    )

    toc_items = [f'      <li><a href="title.xhtml">{html.escape(meta["title"], quote=False)}</a></li>']
    manifest_items = [
        '    <item id="style" href="style.css" media-type="text/css"/>',
        '    <item id="cover-image" href="cover.jpg" media-type="image/jpeg" properties="cover-image"/>',
        '    <item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>',
        '    <item id="title" href="title.xhtml" media-type="application/xhtml+xml"/>',
        '    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
    ]
    spine_items = [
        '    <itemref idref="cover"/>',
        '    <itemref idref="title"/>',
    ]

    for chap in chapters:
        body_parts = []
        for block in chap["blocks"]:
            if is_scene_break(block):
                body_parts.append('<hr class="scene-break" aria-hidden="true"/>')
            else:
                body_parts.append(f"<p>{md_to_xhtml_inline(block)}</p>")
        body_html = "\n".join(body_parts)
        epub_type = "prologue" if chap["is_prologue"] else "chapter"
        role = "doc-prologue" if chap["is_prologue"] else "doc-chapter"
        entries[chap["filename"]] = _xhtml(
            chap["title"],
            f'<section epub:type="{epub_type}" role="{role}" id="{chap["id"]}">\n'
            f'<h1>{html.escape(chap["title"], quote=False)}</h1>\n'
            f"{body_html}\n"
            "</section>",
        )
        toc_items.append(
            f'      <li><a href="{chap["filename"]}">{html.escape(chap["title"], quote=False)}</a></li>'
        )
        manifest_items.append(
            f'    <item id="{chap["id"]}" href="{chap["filename"]}" media-type="application/xhtml+xml"/>'
        )
        spine_items.append(f'    <itemref idref="{chap["id"]}"/>')

    first_chap = chapters[0]
    entries["nav.xhtml"] = _xhtml(
        "Contents",
        '<nav epub:type="toc" id="toc" role="doc-toc">\n'
        "  <h1>Contents</h1>\n"
        "  <ol>\n"
        + "\n".join(toc_items)
        + "\n  </ol>\n"
        "</nav>\n"
        '<nav epub:type="landmarks" hidden="hidden">\n'
        "  <h2>Landmarks</h2>\n"
        "  <ol>\n"
        '    <li><a epub:type="cover" href="cover.xhtml">Cover</a></li>\n'
        '    <li><a epub:type="titlepage" href="title.xhtml">Title Page</a></li>\n'
        f'    <li><a epub:type="bodymatter" href="{first_chap["filename"]}">{html.escape(first_chap["title"], quote=False)}</a></li>\n'
        "  </ol>\n"
        "</nav>",
    )

    identifier = "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL, "corporate-castle/standalone/" + meta["id"]))
    description = (
        "Preview edition (Prologue and Chapter One) of The Hot Potato of Corporate Castle, "
        "a satirical corporate fantasy set between the Tower of Vibes, Liability Tower, and the underfunded ER Watch."
    )
    opf = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<package xmlns="{OPF_NS}" version="3.0" unique-identifier="pub-id" xml:lang="en">\n'
        '  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        f'    <dc:identifier id="pub-id">{html.escape(identifier, quote=False)}</dc:identifier>\n'
        f'    <dc:title>{html.escape(meta["title"], quote=False)}</dc:title>\n'
        '    <dc:language>en</dc:language>\n'
        f'    <dc:description>{html.escape(description, quote=False)}</dc:description>\n'
        '    <meta property="rendition:layout">reflowable</meta>\n'
        '    <meta property="dcterms:modified">2026-11-27T22:55:00Z</meta>\n'
        '  </metadata>\n'
        '  <manifest>\n'
        + "\n".join(manifest_items)
        + "\n  </manifest>\n"
        '  <spine>\n'
        + "\n".join(spine_items)
        + "\n  </spine>\n"
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
            info = ZipInfo(name, (2026, 11, 27, 22, 55, 0))
            info.compress_type = comp
            zf.writestr(info, val if isinstance(val, bytes) else val.encode("utf-8"))

        add("mimetype", b"application/epub+zip", ZIP_STORED)
        add("META-INF/container.xml", container)
        add("EPUB/package.opf", opf)
        for fname, val in entries.items():
            add(f"EPUB/{fname}", val)

    # Strict validation of archive and word-for-word prose fidelity for every chapter
    with ZipFile(output) as zf:
        assert zf.testzip() is None
        assert zf.infolist()[0].filename == "mimetype"
        assert zf.infolist()[0].compress_type == ZIP_STORED
        assert zf.read("mimetype") == b"application/epub+zip"
        for name in zf.namelist():
            if name.endswith((".xml", ".xhtml", ".opf")):
                ET.fromstring(zf.read(name))
        for chap in chapters:
            tree = ET.fromstring(zf.read(f"EPUB/{chap['filename']}"))
            h1 = "".join(tree.find(f".//{{{XHTML_NS}}}h1").itertext())
            assert h1 == chap["title"], f"Heading mismatch in {chap['filename']}"
            actual = [norm("".join(p.itertext())) for p in tree.findall(f".//{{{XHTML_NS}}}p")]
            expected_plain = [strip_md_markers(b) for b in chap["blocks"] if not is_scene_break(b)]
            assert actual == expected_plain, f"Prose mismatch in {chap['filename']}"

    return output.read_bytes()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    meta, chapters = load_chapters()
    cover_path = OUT / "cover.jpg"
    cover_bytes = build_cover(cover_path)

    pdf_path = OUT / f"{meta['id']}.pdf"
    pdf_bytes, page_count = build_pdf(meta, chapters, cover_path, pdf_path)

    epub_path = OUT / f"{meta['id']}.epub"
    epub_bytes = build_epub(meta, chapters, cover_bytes, epub_path)

    summary = {
        "edition": "preview-prologue-ch1",
        "chapters": [{"source": c["source"], "title": c["title"], "sha256": c["sha256"]} for c in chapters],
        "cover": {"path": str(cover_path), "bytes": len(cover_bytes), "sha256": sha256_bytes(cover_bytes)},
        "pdf": {"path": str(pdf_path), "bytes": len(pdf_bytes), "sha256": sha256_bytes(pdf_bytes), "pages": page_count},
        "epub": {"path": str(epub_path), "bytes": len(epub_bytes), "sha256": sha256_bytes(epub_bytes)},
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
