#!/usr/bin/env python3
"""Build the illustrated cover, typeset 6x9 PDF, and reflowable EPUB 3 for
The Quest of the Golden Garbanzo.

Reads chapter order and prose strictly from book.json and manuscript/*.md
without altering story wording, and embeds selected local illustrations from
production/illustration-plan.json.

Run with ReportLab and Pillow:
    uv run --with reportlab --with pillow python production/build_edition.py
"""
from __future__ import annotations

import hashlib
import html
import io
import json
import re
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile, ZipInfo

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
)
from reportlab.platypus.tableofcontents import TableOfContents

BOOK = Path(__file__).resolve().parents[1]
OUT = BOOK / "exports"
PLAN_PATH = BOOK / "production" / "illustration-plan.json"
COVER_ART = BOOK / "assets" / "illustrations" / "cover-art.png"

XHTML_NS = "http://www.w3.org/1999/xhtml"
OPF_NS = "http://www.idpf.org/2007/opf"
EPUB_NS = "http://www.idpf.org/2007/ops"

FONT_CANDIDATES = {
    "regular": [
        Path(r"C:\Windows\Fonts\georgia.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"),
    ],
    "bold": [
        Path(r"C:\Windows\Fonts\georgiab.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"),
    ],
    "italic": [
        Path(r"C:\Windows\Fonts\georgiai.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"),
    ],
    "bold_italic": [
        Path(r"C:\Windows\Fonts\georgiaz.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf"),
    ],
    "sans": [
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ],
    "sans_bold": [
        Path(r"C:\Windows\Fonts\arialbd.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
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
MARGIN_BOTTOM = 50

INK = HexColor("#2b241d")
MUTED = HexColor("#6c5f4e")
GOLD = HexColor("#b5812a")

EPUB_CSS = """\
html { font-size: 100%; }
body { margin: 5%; font-family: Georgia, "Liberation Serif", "DejaVu Serif", serif; line-height: 1.55; color: #2b241d; }
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
figure.story-art { margin: 1.4em auto; text-align: center; break-inside: avoid; page-break-inside: avoid; }
figure.story-art img { display: block; margin: 0 auto; max-width: 100%; height: auto; border: 1px solid #d4b26a; border-radius: 4px; }
figure.story-art figcaption { margin-top: 0.45em; font-style: italic; font-size: 0.88em; color: #6c5f4e; line-height: 1.35; }
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


def load_illustrations() -> dict[str, list[dict]]:
    """Map chapter path -> list of selected illustration records."""
    if not PLAN_PATH.is_file():
        return {}
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    by_chapter: dict[str, list[dict]] = {}
    for item in plan.get("illustrations", []):
        if item.get("status") not in ("accepted", "generated") or not item.get("asset"):
            continue
        asset = BOOK / item["asset"]
        if not asset.is_file():
            raise FileNotFoundError(f"Missing illustration asset: {asset}")
        rec = dict(item)
        rec["abs_path"] = asset
        by_chapter.setdefault(item["chapter"], []).append(rec)
    return by_chapter


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


def draw_centered_text_halo(
    base: Image.Image,
    text: str,
    y: int,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
    halo: tuple[int, int, int, int] = (252, 245, 228, 210),
    halo_radius: int = 8,
) -> int:
    w, h = base.size
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bbox = d.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (w - tw) / 2
    # Soft warm-cream halo behind letters for effortless legibility over sunlit clouds
    for dx in (-3, 0, 3):
        for dy in (-3, 0, 3):
            d.text((x + dx, y + dy), text, font=font, fill=halo)
    layer = layer.filter(ImageFilter.GaussianBlur(radius=halo_radius))
    base.alpha_composite(layer)

    fg = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(fg).text((x, y), text, font=font, fill=(*fill, 255))
    base.alpha_composite(fg)
    return y + th


def build_cover(output: Path) -> bytes:
    """Compose a 720x1080 JPEG cover from cover-art.png with crisp serif title typography."""
    w, h = 1440, 2160  # 2x supersampled 720x1080
    art = Image.open(COVER_ART).convert("RGB")
    # Center-crop/resize to exact 2:3 portrait without distortion
    target_ratio = w / h
    aw, ah = art.size
    if aw / ah > target_ratio:
        new_w = int(round(ah * target_ratio))
        left = (aw - new_w) // 2
        art = art.crop((left, 0, left + new_w, ah))
    else:
        new_h = int(round(aw / target_ratio))
        top = (ah - new_h) // 2
        art = art.crop((0, top, aw, top + new_h))
    art = art.resize((w, h), Image.LANCZOS).convert("RGBA")

    # Subtle warm sunlit parchment wash across the top 30% so dark ink pops cleanly
    wash = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wash)
    wash_end = int(h * 0.31)
    for y in range(wash_end):
        t = y / wash_end
        alpha = int(round(135 * (1.0 - t) ** 1.35))
        wd.line([(0, y), (w, y)], fill=(252, 245, 229, alpha))
    art.alpha_composite(wash)

    # Delicate warm-gold inset frame
    frame = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    fd = ImageDraw.Draw(frame)
    fd.rectangle([38, 38, w - 39, h - 39], outline=(196, 146, 56, 215), width=5)
    fd.rectangle([54, 54, w - 55, h - 55], outline=(232, 200, 128, 175), width=2)
    art.alpha_composite(frame)

    f_kicker = ImageFont.truetype(str(pick_font("sans_bold")), 34)
    f_title = ImageFont.truetype(str(pick_font("bold")), 104)
    f_sub = ImageFont.truetype(str(pick_font("italic")), 44)

    y = 84
    y = draw_centered_text_halo(art, "G A R B A N Z O   F A M I L Y", y, f_kicker, (104, 72, 34), halo_radius=6) + 26
    y = draw_centered_text_halo(art, "The Quest of the", y, f_title, (43, 32, 22), halo_radius=10) + 14
    y = draw_centered_text_halo(art, "Golden Garbanzo", y, f_title, (43, 32, 22), halo_radius=10) + 52

    # Short gold accent rule with generous breathing room below title
    r_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(r_layer).line([(w // 2 - 130, y), (w // 2 + 130, y)], fill=(181, 129, 42, 235), width=4)
    art.alpha_composite(r_layer)

    draw_centered_text_halo(
        art, "A Fun, Dramatic Family Adventure", y + 24, f_sub, (74, 54, 34), halo_radius=7
    )

    final = art.convert("RGB").resize((720, 1080), Image.LANCZOS)
    output.parent.mkdir(parents=True, exist_ok=True)
    final.save(output, "JPEG", quality=92, optimize=True, progressive=False)
    return output.read_bytes()


class FramedIllustration(Flowable):
    """Centered storybook illustration with a thin warm-gold border."""

    def __init__(self, image_path: Path, max_width: float):
        super().__init__()
        self.image_path = image_path
        with Image.open(image_path) as im:
            rgb = im.convert("RGB")
            iw, ih = rgb.size
            buf = io.BytesIO()
            rgb.save(buf, "JPEG", quality=90, optimize=True, progressive=False)
            self._jpeg_bytes = buf.getvalue()
        self.draw_w = max_width
        self.draw_h = max_width * (ih / iw)
        self.width = self.draw_w
        self.height = self.draw_h

    def draw(self):
        c = self.canv
        c.saveState()
        c.drawImage(
            ImageReader(io.BytesIO(self._jpeg_bytes)),
            0,
            0,
            width=self.draw_w,
            height=self.draw_h,
            preserveAspectRatio=True,
        )
        c.setStrokeColor(GOLD)
        c.setLineWidth(0.75)
        c.rect(0, 0, self.draw_w, self.draw_h, stroke=1, fill=0)
        c.restoreState()


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


def build_pdf(
    meta: dict,
    chapters: list[dict],
    illustrations: dict[str, list[dict]],
    cover_path: Path,
    output: Path,
) -> tuple[bytes, int]:
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
        "Body", fontName="Story", fontSize=10.3, leading=14.6, textColor=INK,
        spaceAfter=5.0, alignment=0,
    )
    chapter_style = ParagraphStyle(
        "ChapterTitle", fontName="StoryBold", fontSize=15.5, leading=19.5, textColor=INK,
        spaceBefore=0, spaceAfter=14, keepWithNext=1,
    )
    caption_style = ParagraphStyle(
        "Caption", fontName="StoryItalic", fontSize=8.8, leading=12.0, textColor=MUTED,
        alignment=TA_CENTER, spaceBefore=5, spaceAfter=0,
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
        title=meta["title"],
        subject="Garbanzo Family illustrated adventure story",
        author="Garbanzo Family",
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
        Spacer(1, 95),
        Paragraph("GARBANZO FAMILY", series_style),
        Paragraph("The Quest of the<br/>Golden Garbanzo", title_style),
        Paragraph("A Fun, Dramatic Family Adventure", sub_style),
        Paragraph("ILLUSTRATED EDITION  ·  TEN CHAPTERS", notice_style),
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

    art_w = 4.35 * inch
    for idx, chapter in enumerate(chapters):
        if idx:
            story.append(PageBreak())
        story.append(Paragraph(html.escape(chapter["title"], quote=False), chapter_style))
        ch_arts = illustrations.get(chapter["source"], [])
        art_by_anchor: dict[int, list[dict]] = {}
        for rec in ch_arts:
            anchor = min(int(rec.get("anchor_after_paragraph", len(chapter["paragraphs"]))), len(chapter["paragraphs"]))
            art_by_anchor.setdefault(anchor, []).append(rec)

        for p_idx, p in enumerate(chapter["paragraphs"], 1):
            story.append(Paragraph(md_to_rl_xml(p), body_style))
            for rec in art_by_anchor.get(p_idx, []):
                fig = FramedIllustration(rec["abs_path"], art_w)
                fig.hAlign = "CENTER"
                block = [Spacer(1, 8), fig]
                if rec.get("caption"):
                    block.append(Paragraph(html.escape(rec["caption"], quote=False), caption_style))
                block.append(Spacer(1, 10))
                story.append(KeepTogether(block))

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


def encode_epub_jpeg(path: Path, quality: int = 88) -> bytes:
    im = Image.open(path).convert("RGB")
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True, progressive=False)
    return buf.getvalue()


def build_epub(
    meta: dict,
    chapters: list[dict],
    illustrations: dict[str, list[dict]],
    cover_bytes: bytes,
    output: Path,
) -> bytes:
    entries: dict[str, str | bytes] = {}
    entries["style.css"] = EPUB_CSS
    entries["cover.jpg"] = cover_bytes
    entries["cover.xhtml"] = _xhtml(
        f"{meta['title']} Cover",
        '<section epub:type="cover"><img src="cover.jpg" alt="Illustrated cover of The Quest of the Golden Garbanzo"/></section>',
        "cover-page",
    )
    entries["title.xhtml"] = _xhtml(
        meta["title"],
        '<section class="title-page" epub:type="titlepage">\n'
        '  <p class="kicker">Garbanzo Family</p>\n'
        f'  <h1>{html.escape(meta["title"], quote=False)}</h1>\n'
        '  <hr class="rule" aria-hidden="true"/>\n'
        '  <p class="subtitle">A Fun, Dramatic Family Adventure</p>\n'
        '  <p class="note">Illustrated Edition · Ten Chapters</p>\n'
        "</section>",
    )

    image_manifest_items: list[str] = []
    ch_files = []
    for ch in chapters:
        fname = f"chapter-{ch['number']:02d}.xhtml"
        ch_arts = illustrations.get(ch["source"], [])
        art_by_anchor: dict[int, list[dict]] = {}
        for rec in ch_arts:
            anchor = min(int(rec.get("anchor_after_paragraph", len(ch["paragraphs"]))), len(ch["paragraphs"]))
            art_by_anchor.setdefault(anchor, []).append(rec)

        blocks: list[str] = []
        for p_idx, p in enumerate(ch["paragraphs"], 1):
            blocks.append(f"<p>{md_to_xhtml_inline(p)}</p>")
            for rec in art_by_anchor.get(p_idx, []):
                img_id = rec["id"]
                rel_img = f"images/{img_id}.jpg"
                entries[rel_img] = encode_epub_jpeg(rec["abs_path"])
                image_manifest_items.append(
                    f'<item id="{img_id}" href="{rel_img}" media-type="image/jpeg"/>'
                )
                alt_esc = html.escape(rec["alt_text"], quote=True)
                cap_html = (
                    f'\n  <figcaption>{html.escape(rec["caption"], quote=False)}</figcaption>'
                    if rec.get("caption") else ""
                )
                blocks.append(
                    f'<figure class="story-art">\n'
                    f'  <img src="{rel_img}" alt="{alt_esc}"/>'
                    f'{cap_html}\n'
                    f'</figure>'
                )

        body_html = "\n".join(blocks)
        entries[fname] = _xhtml(
            ch["title"],
            f'<section epub:type="chapter" role="doc-chapter" id="chapter-{ch["number"]}">\n'
            f'<h1>{html.escape(ch["title"], quote=False)}</h1>\n'
            f"{body_html}\n"
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
        "An illustrated, easy-to-read family adventure about how ordinary humans Jorge, Marissa, and six-year-old Clara "
        "braved late-night spreadsheets, a confetti-blasting desk-bot, sneaky Spanish house pitches, and one last "
        "office bonus to earn sunny mornings together in Spain."
    )
    manifest_items = [
        '<item id="style" href="style.css" media-type="text/css"/>',
        '<item id="cover-image" href="cover.jpg" media-type="image/jpeg" properties="cover-image"/>',
        '<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>',
        '<item id="title" href="title.xhtml" media-type="application/xhtml+xml"/>',
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
        *image_manifest_items,
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
        '    <meta property="dcterms:modified">2026-11-25T20:40:00Z</meta>\n'
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
            info = ZipInfo(name, (2026, 11, 25, 20, 40, 0))
            info.compress_type = comp
            zf.writestr(info, val if isinstance(val, bytes) else val.encode("utf-8"))

        add("mimetype", b"application/epub+zip", ZIP_STORED)
        add("META-INF/container.xml", container)
        add("EPUB/package.opf", opf)
        for fname, val in entries.items():
            add(f"EPUB/{fname}", val)

    # Strict validation of archive, prose fidelity, and alt-text presence
    with ZipFile(output) as zf:
        assert zf.testzip() is None
        assert zf.infolist()[0].filename == "mimetype"
        assert zf.infolist()[0].compress_type == ZIP_STORED
        assert zf.read("mimetype") == b"application/epub+zip"
        for name in zf.namelist():
            if name.endswith((".xml", ".xhtml", ".opf")):
                ET.fromstring(zf.read(name))
        img_count = 0
        for fname, title, expected_paras in ch_files:
            tree = ET.fromstring(zf.read(f"EPUB/{fname}"))
            h1 = "".join(tree.find(f".//{{{XHTML_NS}}}h1").itertext())
            assert h1 == title, f"{fname}: title mismatch"
            actual = [norm("".join(p.itertext())) for p in tree.findall(f".//{{{XHTML_NS}}}p")]
            expected_plain = [strip_md_markers(p) for p in expected_paras]
            assert actual == expected_plain, f"{fname}: paragraph prose mismatch"
            for img in tree.findall(f".//{{{XHTML_NS}}}img"):
                assert (img.get("alt") or "").strip(), f"{fname}: missing alt text on {img.get('src')}"
                assert f"EPUB/{img.get('src')}" in zf.namelist(), f"{fname}: broken image {img.get('src')}"
                img_count += 1
        expected_imgs = sum(len(v) for v in illustrations.values())
        assert img_count == expected_imgs, f"Expected {expected_imgs} embedded images, found {img_count}"

    return output.read_bytes()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    meta, chapters = load_chapters()
    illustrations = load_illustrations()
    cover_path = OUT / "cover.jpg"
    cover_bytes = build_cover(cover_path)

    pdf_path = OUT / f"{meta['id']}.pdf"
    pdf_bytes, page_count = build_pdf(meta, chapters, illustrations, cover_path, pdf_path)

    epub_path = OUT / f"{meta['id']}.epub"
    epub_bytes = build_epub(meta, chapters, illustrations, cover_bytes, epub_path)

    summary = {
        "cover": {"path": str(cover_path), "bytes": len(cover_bytes), "sha256": sha256_bytes(cover_bytes)},
        "pdf": {"path": str(pdf_path), "bytes": len(pdf_bytes), "sha256": sha256_bytes(pdf_bytes), "pages": page_count},
        "epub": {
            "path": str(epub_path),
            "bytes": len(epub_bytes),
            "sha256": sha256_bytes(epub_bytes),
            "embedded_illustrations": sum(len(v) for v in illustrations.values()),
        },
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
