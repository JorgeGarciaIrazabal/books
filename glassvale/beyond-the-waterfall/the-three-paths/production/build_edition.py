#!/usr/bin/env python3
"""Build the composed cover, blended-text 7x9 illustrated PDF, and reflowable EPUB 3
for Beyond the Waterfall, Book 1: The Three Paths.

Reads strictly from book.json, manuscript/*.md, and production/illustration-plan.json
without modifying a single word of story text.

Run:
    uv run --with reportlab --with pillow python glassvale/beyond-the-waterfall/the-three-paths/production/build_edition.py
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
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

BOOK = Path(__file__).resolve().parents[1]
OUT = BOOK / "exports"
BLENDED_CACHE = BOOK / "assets" / "blended-cache"
PLAN_PATH = BOOK / "production" / "illustration-plan.json"
COVER_ART = BOOK / "assets" / "illustrations" / "cover-art.png"

PAGE_W = 504.0  # 7.0 in
PAGE_H = 648.0  # 9.0 in
MARGIN_X = 54.0
MARGIN_TOP = 54.0
MARGIN_BOT = 52.0
COL_W = PAGE_W - 2 * MARGIN_X

PAPER_HEX = "#FBF6EC"
INK_DARK = "#231F20"
INK_LIGHT = "#FBF6EC"
ACCENT_GOLD = "#A67C2E"
ACCENT_SLATE = "#36486B"

FONT_CANDIDATES = {
    "regular": [
        Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"),
    ],
    "bold": [
        Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"),
    ],
    "italic": [
        Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"),
    ],
    "bold_italic": [
        Path("/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf"),
    ],
    "sans": [
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ],
    "sans_bold": [
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ],
}


def pick_font(role: str) -> Path:
    for p in FONT_CANDIDATES[role]:
        if p.exists():
            return p
    raise FileNotFoundError(f"Missing font for {role}")


def register_fonts() -> None:
    pdfmetrics.registerFont(TTFont("StorySerif", str(pick_font("regular"))))
    pdfmetrics.registerFont(TTFont("StorySerif-Bold", str(pick_font("bold"))))
    pdfmetrics.registerFont(TTFont("StorySerif-Italic", str(pick_font("italic"))))
    pdfmetrics.registerFont(TTFont("StorySerif-BoldItalic", str(pick_font("bold_italic"))))
    pdfmetrics.registerFont(TTFont("StorySans", str(pick_font("sans"))))
    pdfmetrics.registerFont(TTFont("StorySans-Bold", str(pick_font("sans_bold"))))
    pdfmetrics.registerFontFamily(
        "StorySerif",
        normal="StorySerif",
        bold="StorySerif-Bold",
        italic="StorySerif-Italic",
        boldItalic="StorySerif-BoldItalic",
    )


def md_to_rl_xml(text: str) -> str:
    escaped = html.escape(text, quote=False)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"\*(.+?)\*", r"<i>\1</i>", escaped)
    return escaped


def md_to_xhtml(text: str) -> str:
    escaped = html.escape(text, quote=False)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*(.+?)\*", r"<em>\1</em>", escaped)
    return escaped


def draw_tracked_centered(
    draw: ImageDraw.ImageDraw,
    text: str,
    cy: int,
    w: int,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int, int],
    tracking: int = 2,
    shadow: tuple[int, int, int, int] | None = None,
) -> None:
    widths = [draw.textbbox((0, 0), ch, font=font)[2] for ch in text]
    total_w = sum(widths) + tracking * max(0, len(text) - 1)
    x = (w - total_w) // 2
    for ch, cw in zip(text, widths):
        if shadow:
            draw.text((x + 1, cy + 2), ch, font=font, fill=shadow)
        draw.text((x, cy), ch, font=font, fill=fill)
        x += cw + tracking


def build_cover(out_path: Path) -> None:
    im = Image.open(COVER_ART).convert("RGB")
    im = im.resize((720, 1080), Image.LANCZOS)
    rgba = im.convert("RGBA")

    # Subtle top sky darkening scrim solely behind title band (top 26%) for crisp legibility
    scrim = Image.new("RGBA", (720, 1080), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(scrim)
    for y in range(300):
        alpha = int(105 * (1.0 - y / 300.0) ** 1.4)
        s_draw.line([(0, y), (720, y)], fill=(18, 24, 48, alpha))
    rgba = Image.alpha_composite(rgba, scrim)

    draw = ImageDraw.Draw(rgba)
    f_eyebrow = ImageFont.truetype(str(pick_font("sans_bold")), 16)
    f_title = ImageFont.truetype(str(pick_font("bold")), 62)
    f_sub = ImageFont.truetype(str(pick_font("italic")), 22)

    draw_tracked_centered(
        draw,
        "BEYOND THE WATERFALL  ·  BOOK ONE",
        62,
        720,
        f_eyebrow,
        (249, 232, 184, 245),
        tracking=3,
        shadow=(14, 18, 36, 170),
    )

    title = "THE THREE PATHS"
    tb = draw.textbbox((0, 0), title, font=f_title)
    tw = tb[2] - tb[0]
    tx = (720 - tw) // 2
    ty = 98
    # Soft glow/shadow behind main title
    for dx, dy in [(0, 3), (2, 2), (-1, 2)]:
        draw.text((tx + dx, ty + dy), title, font=f_title, fill=(14, 18, 38, 190))
    draw.text((tx, ty), title, font=f_title, fill=(254, 249, 234, 255))

    # Thin gold ornament rule
    draw.line([(210, 186), (510, 186)], fill=(238, 206, 126, 220), width=2)
    draw_tracked_centered(
        draw,
        "Glassvale Academy",
        198,
        720,
        f_sub,
        (246, 236, 208, 235),
        tracking=1,
        shadow=(14, 18, 36, 160),
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    rgba.convert("RGB").save(out_path, format="JPEG", quality=93, optimize=True)


def build_blended_page_image(ill: dict) -> Path:
    """Create a seamless 1400x1800 (7x9 @ 200dpi) full-bleed blended canvas for one illustration."""
    BLENDED_CACHE.mkdir(parents=True, exist_ok=True)
    out_p = BLENDED_CACHE / f"{ill['id']}_blended.jpg"

    src = Image.open(BOOK / ill["asset"]).convert("RGB")
    target_w, target_h = 1400, 1800  # 200 px per inch for 7x9 in
    scale_h = round(src.height * target_w / src.width)
    # If taller than page, fit height; otherwise fit width and anchor bottom
    if scale_h > target_h:
        resized = src.resize((target_w, target_h), Image.LANCZOS)
        y_top = 0
    else:
        resized = src.resize((target_w, scale_h), Image.LANCZOS)
        y_top = target_h - scale_h

    # Build ambient upper sky/wall extension from top strip of illustration
    top_strip = resized.crop((0, 0, target_w, min(48, resized.height)))
    # Stretch top strip smoothly upward and blur heavily so sky/wall tone continues naturally
    ambient_h = max(1, y_top + 96)
    ambient = top_strip.resize((target_w, ambient_h), Image.BILINEAR)
    ambient = ambient.filter(ImageFilter.GaussianBlur(radius=38))

    canvas_im = Image.new("RGB", (target_w, target_h))
    canvas_im.paste(ambient, (0, 0))

    # Feather top edge of resized illustration seamlessly into ambient extension
    feather_px = min(130, resized.height // 4)
    mask = Image.new("L", resized.size, 255)
    m_draw = ImageDraw.Draw(mask)
    if y_top > 0:
        for y in range(feather_px):
            val = int(255 * (y / float(feather_px)) ** 1.35)
            m_draw.line([(0, y), (target_w, y)], fill=val)
    canvas_im.paste(resized, (0, y_top), mask)

    # Apply soft feathered readability veil ONLY around the mapped text box
    bx, by, bw, bh = ill["box_pt"]
    px_scale = target_w / PAGE_W  # 200/72
    x0 = int((bx - 22) * px_scale)
    y0 = int((by - 20) * px_scale)
    x1 = int((bx + bw + 22) * px_scale)
    y1 = int((by + bh + 18) * px_scale)

    theme = ill["text_theme"]
    if theme == "dark_on_light":
        veil_rgb = (250, 244, 231)
        core_alpha = 188
    else:
        veil_rgb = (20, 25, 48)
        core_alpha = 185

    veil = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    v_mask = Image.new("L", (target_w, target_h), 0)
    vm_draw = ImageDraw.Draw(v_mask)
    vm_draw.rounded_rectangle([x0, y0, x1, y1], radius=46, fill=core_alpha)
    v_mask = v_mask.filter(ImageFilter.GaussianBlur(radius=36))
    veil_color = Image.new("RGBA", (target_w, target_h), veil_rgb + (255,))
    veil_color.putalpha(v_mask)

    final_im = Image.alpha_composite(canvas_im.convert("RGBA"), veil_color).convert("RGB")
    final_im.save(out_p, format="JPEG", quality=92, optimize=True)
    return out_p


def load_chapters(book_meta: dict) -> list[dict]:
    chapters = []
    for idx, rel in enumerate(book_meta["chapters"], 1):
        raw = (BOOK / rel).read_text(encoding="utf-8").strip()
        blocks = [b.strip() for b in raw.split("\n\n") if b.strip()]
        title_line = blocks[0].lstrip("#").strip()
        paras = blocks[1:]
        chapters.append({"num": idx, "rel": rel, "title": title_line, "paras": paras})
    return chapters


def build_pdf(book_meta: dict, plan: dict, cover_jpg: Path, out_pdf: Path) -> tuple[int, dict[str, int]]:
    register_fonts()
    chapters = load_chapters(book_meta)

    # Map chapter -> list of illustrations sorted by first blended paragraph
    by_chap: dict[str, list[dict]] = {}
    for ill in plan["illustrations"]:
        by_chap.setdefault(ill["chapter"], []).append(ill)
    for k in by_chap:
        by_chap[k].sort(key=lambda x: x["blended_paragraphs"][0])

    # Pre-render blended page canvases
    blended_images = {ill["id"]: build_blended_page_image(ill) for ill in plan["illustrations"]}

    # Styles
    s_body = ParagraphStyle(
        "Body",
        fontName="StorySerif",
        fontSize=11.6,
        leading=17.4,
        textColor=HexColor(INK_DARK),
        spaceAfter=9.5,
        alignment=TA_LEFT,
    )
    s_first = ParagraphStyle("BodyFirst", parent=s_body, firstLineIndent=0)
    s_ind = ParagraphStyle("BodyIndent", parent=s_body, firstLineIndent=14)
    s_blend_dark = ParagraphStyle(
        "BlendDark",
        fontName="StorySerif",
        fontSize=11.2,
        leading=16.0,
        textColor=HexColor("#1D1A18"),
        spaceAfter=7.5,
        alignment=TA_LEFT,
    )
    s_blend_light = ParagraphStyle(
        "BlendLight",
        fontName="StorySerif",
        fontSize=11.2,
        leading=16.0,
        textColor=HexColor("#FBF6EA"),
        spaceAfter=7.5,
        alignment=TA_LEFT,
    )
    s_ch_num = ParagraphStyle(
        "ChNum",
        fontName="StorySans-Bold",
        fontSize=9.2,
        leading=12,
        textColor=HexColor(ACCENT_GOLD),
        alignment=TA_CENTER,
    )
    s_ch_title = ParagraphStyle(
        "ChTitle",
        fontName="StorySerif-Bold",
        fontSize=20.0,
        leading=25.0,
        textColor=HexColor(ACCENT_SLATE),
        alignment=TA_CENTER,
    )

    def render_book_pass(toc_pages: dict[int, int] | None) -> tuple[bytes, dict[int, int]]:
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=(PAGE_W, PAGE_H))
        c.setTitle("Beyond the Waterfall: The Three Paths")
        c.setAuthor("Glassvale Book Studio")

        page_num = 0
        found_chap_pages: dict[int, int] = {}

        def start_ivory_page() -> None:
            nonlocal page_num
            page_num += 1
            c.setFillColor(HexColor(PAPER_HEX))
            c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

        def draw_footer(num: int, light: bool = False) -> None:
            c.saveState()
            c.setFont("StorySans", 8.8)
            c.setFillColor(HexColor("#E8DFC9" if light else "#7A7062"))
            c.drawCentredString(PAGE_W / 2, 26, str(num))
            c.restoreState()

        # Page 1: Full-bleed cover
        c.drawImage(ImageReader(str(cover_jpg)), 0, 0, width=PAGE_W, height=PAGE_H)
        c.showPage()
        page_num = 1

        # Page 2: Title page
        start_ivory_page()
        c.setFillColor(HexColor(ACCENT_GOLD))
        c.setFont("StorySans-Bold", 10)
        c.drawCentredString(PAGE_W / 2, PAGE_H - 185, "BEYOND THE WATERFALL  ·  BOOK ONE")
        c.setFillColor(HexColor(ACCENT_SLATE))
        c.setFont("StorySerif-Bold", 28)
        c.drawCentredString(PAGE_W / 2, PAGE_H - 228, "The Three Paths")
        c.setStrokeColor(HexColor(ACCENT_GOLD))
        c.setLineWidth(1.0)
        c.line(PAGE_W / 2 - 70, PAGE_H - 248, PAGE_W / 2 + 70, PAGE_H - 248)
        c.setFillColor(HexColor("#5B5248"))
        c.setFont("StorySerif-Italic", 12.5)
        c.drawCentredString(PAGE_W / 2, PAGE_H - 278, "A Glassvale Academy Story for Clara")
        c.setFont("StorySans", 9)
        c.setFillColor(HexColor("#7A7062"))
        c.drawCentredString(PAGE_W / 2, 86, "Glassvale Book Studio  ·  Illustrated First Edition")
        c.showPage()

        # Page 3: Table of Contents
        start_ivory_page()
        c.setFillColor(HexColor(ACCENT_SLATE))
        c.setFont("StorySerif-Bold", 20)
        c.drawCentredString(PAGE_W / 2, PAGE_H - 86, "Chapters")
        c.setStrokeColor(HexColor(ACCENT_GOLD))
        c.setLineWidth(0.8)
        c.line(PAGE_W / 2 - 44, PAGE_H - 98, PAGE_W / 2 + 44, PAGE_H - 98)

        y_toc = PAGE_H - 144
        for ch in chapters:
            label = ch["title"]
            pg_str = str(toc_pages.get(ch["num"], "")) if toc_pages else ""
            c.setFont("StorySerif", 12)
            c.setFillColor(HexColor(INK_DARK))
            c.drawString(MARGIN_X + 12, y_toc, label)
            if pg_str:
                c.setFont("StorySans", 10.5)
                c.setFillColor(HexColor(ACCENT_GOLD))
                c.drawRightString(PAGE_W - MARGIN_X - 12, y_toc, pg_str)
            c.setStrokeColor(HexColor("#E6DEC8"))
            c.setLineWidth(0.4)
            c.line(MARGIN_X + 12, y_toc - 10, PAGE_W - MARGIN_X - 12, y_toc - 10)
            y_toc -= 36
        c.showPage()

        # Chapters
        for ch in chapters:
            start_ivory_page()
            found_chap_pages[ch["num"]] = page_num
            y_cursor = PAGE_H - MARGIN_TOP

            # Chapter header
            parts = ch["title"].split(":", 1)
            ch_label = parts[0].strip().upper()
            ch_name = parts[1].strip() if len(parts) > 1 else ch["title"]

            p_num = Paragraph(html.escape(ch_label), s_ch_num)
            _, h_num = p_num.wrapOn(c, COL_W, 40)
            p_num.drawOn(c, MARGIN_X, y_cursor - h_num)
            y_cursor -= h_num + 6

            p_tit = Paragraph(html.escape(ch_name), s_ch_title)
            _, h_tit = p_tit.wrapOn(c, COL_W, 80)
            p_tit.drawOn(c, MARGIN_X, y_cursor - h_tit)
            y_cursor -= h_tit + 10

            c.setStrokeColor(HexColor(ACCENT_GOLD))
            c.setLineWidth(0.9)
            c.line(PAGE_W / 2 - 42, y_cursor, PAGE_W / 2 + 42, y_cursor)
            y_cursor -= 22

            chap_ills = by_chap.get(ch["rel"], [])
            # Map start paragraph -> ill dict
            ill_by_start = {ill["blended_paragraphs"][0]: ill for ill in chap_ills}
            skip_set = set()
            for ill in chap_ills:
                for p_idx in ill["blended_paragraphs"]:
                    skip_set.add(p_idx)

            para_is_first = True
            has_drawn_on_current_page = True
            i = 1
            while i <= len(ch["paras"]):
                if i in ill_by_start:
                    ill = ill_by_start[i]
                    # Close current text page if anything was drawn, then emit full-bleed blended page
                    if has_drawn_on_current_page:
                        draw_footer(page_num, light=False)
                        c.showPage()
                        page_num += 1
                    else:
                        # Shouldn't happen, but safety
                        pass

                    # Draw full-bleed blended canvas
                    c.drawImage(
                        ImageReader(str(blended_images[ill["id"]])),
                        0,
                        0,
                        width=PAGE_W,
                        height=PAGE_H,
                    )
                    bx, by_top, bw, bmax_h = ill["box_pt"]
                    style = s_blend_dark if ill["text_theme"] == "dark_on_light" else s_blend_light
                    cur_y = PAGE_H - by_top
                    for p_idx in ill["blended_paragraphs"]:
                        p_obj = Paragraph(md_to_rl_xml(ch["paras"][p_idx - 1]), style)
                        _, ph = p_obj.wrapOn(c, bw, bmax_h)
                        if (PAGE_H - by_top) - (cur_y - ph) > bmax_h + 10:
                            raise RuntimeError(
                                f"Blended text overflow on {ill['id']} (need {(PAGE_H - by_top) - (cur_y - ph):.1f}pt > {bmax_h}pt)"
                            )
                        p_obj.drawOn(c, bx, cur_y - ph)
                        cur_y -= ph + style.spaceAfter

                    draw_footer(page_num, light=(ill["text_theme"] == "light_on_dark"))
                    c.showPage()
                    # Advance past blended paragraphs
                    i = ill["blended_paragraphs"][-1] + 1
                    para_is_first = True
                    if i <= len(ch["paras"]):
                        start_ivory_page()
                        y_cursor = PAGE_H - MARGIN_TOP
                        has_drawn_on_current_page = False
                    else:
                        has_drawn_on_current_page = False
                    continue

                if i in skip_set:
                    i += 1
                    continue

                st = s_first if para_is_first else s_ind
                p_obj = Paragraph(md_to_rl_xml(ch["paras"][i - 1]), st)
                _, ph = p_obj.wrapOn(c, COL_W, PAGE_H)
                if y_cursor - ph < MARGIN_BOT + 12:
                    draw_footer(page_num, light=False)
                    c.showPage()
                    start_ivory_page()
                    y_cursor = PAGE_H - MARGIN_TOP
                    has_drawn_on_current_page = False
                p_obj.drawOn(c, MARGIN_X, y_cursor - ph)
                y_cursor -= ph + st.spaceAfter
                has_drawn_on_current_page = True
                para_is_first = False
                i += 1

            if has_drawn_on_current_page:
                draw_footer(page_num, light=False)
                c.showPage()

        c.save()
        return buf.getvalue(), found_chap_pages

    _, chap_pages = render_book_pass(None)
    pdf_bytes, chap_pages = render_book_pass(chap_pages)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    out_pdf.write_bytes(pdf_bytes)
    return len(chap_pages), chap_pages


def build_epub(book_meta: dict, plan: dict, cover_jpg: Path, out_epub: Path) -> None:
    chapters = load_chapters(book_meta)
    by_chap: dict[str, list[dict]] = {}
    for ill in plan["illustrations"]:
        by_chap.setdefault(ill["chapter"], []).append(ill)

    book_uid = str(uuid.uuid5(uuid.NAMESPACE_URL, "glassvale/beyond-the-waterfall/the-three-paths"))

    css = """
body {
  font-family: Georgia, "Times New Roman", serif;
  line-height: 1.58;
  color: #231F20;
  background-color: #FBF6EC;
  margin: 1.2em;
}
h1, h2 {
  color: #36486B;
  text-align: center;
  margin-top: 1.4em;
  margin-bottom: 0.8em;
}
p { margin: 0 0 0.85em 0; }
figure.story-art {
  margin: 1.2em auto;
  text-align: center;
  break-inside: avoid;
}
figure.story-art img {
  max-width: 100%;
  height: auto;
  border-radius: 6px;
}
figure.story-art figcaption {
  font-style: italic;
  font-size: 0.9em;
  color: #5A5147;
  margin-top: 0.4em;
}
""".strip()

    out_epub.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(out_epub, "w") as z:
        zi = ZipInfo("mimetype")
        zi.compress_type = ZIP_STORED
        z.writestr(zi, b"application/epub+zip")

        z.writestr(
            "META-INF/container.xml",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
            '  <rootfiles>\n'
            '    <rootfile full-path="EPUB/package.opf" media-type="application/oebps-package+xml"/>\n'
            '  </rootfiles>\n'
            '</container>\n',
            compress_type=ZIP_DEFLATED,
        )
        z.writestr("EPUB/styles.css", css, compress_type=ZIP_DEFLATED)
        z.writestr("EPUB/images/cover.jpg", cover_jpg.read_bytes(), compress_type=ZIP_DEFLATED)

        manifest_items = [
            '<item id="css" href="styles.css" media-type="text/css"/>',
            '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
            '<item id="cover-img" href="images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>',
            '<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>',
        ]
        spine_items = ['<itemref idref="cover"/>']

        z.writestr(
            "EPUB/cover.xhtml",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE html>\n'
            '<html xmlns="http://www.w3.org/1999/xhtml" lang="en">\n'
            '<head><title>The Three Paths</title><link rel="stylesheet" type="text/css" href="styles.css"/></head>\n'
            '<body style="margin:0;text-align:center;">\n'
            '  <img src="images/cover.jpg" alt="' + html.escape(plan["cover_illustration"]["alt_text"], quote=True) + '" style="max-width:100%;height:auto;"/>\n'
            '</body>\n'
            '</html>\n',
            compress_type=ZIP_DEFLATED,
        )

        # Embed all 12 interior illustrations as JPEG
        for ill in plan["illustrations"]:
            im = Image.open(BOOK / ill["asset"]).convert("RGB")
            jb = io.BytesIO()
            im.save(jb, format="JPEG", quality=90, optimize=True)
            img_href = f"images/{ill['id']}.jpg"
            z.writestr(f"EPUB/{img_href}", jb.getvalue(), compress_type=ZIP_DEFLATED)
            manifest_items.append(f'<item id="{ill["id"]}" href="{img_href}" media-type="image/jpeg"/>')

        nav_lis = []
        for ch in chapters:
            chap_href = f"ch-{ch['num']:02d}.xhtml"
            chap_id = f"ch-{ch['num']:02d}"
            manifest_items.append(f'<item id="{chap_id}" href="{chap_href}" media-type="application/xhtml+xml"/>')
            spine_items.append(f'<itemref idref="{chap_id}"/>')
            nav_lis.append(f'      <li><a href="{chap_href}">{html.escape(ch["title"])}</a></li>')

            ill_by_end = {ill["blended_paragraphs"][-1]: ill for ill in by_chap.get(ch["rel"], [])}
            body_parts = [f"  <h1>{html.escape(ch['title'])}</h1>"]
            for idx_p, para in enumerate(ch["paras"], 1):
                body_parts.append(f"  <p>{md_to_xhtml(para)}</p>")
                if idx_p in ill_by_end:
                    ill = ill_by_end[idx_p]
                    alt = html.escape(ill["alt_text"], quote=True)
                    cap = html.escape(ill["caption"])
                    body_parts.append(
                        f'  <figure class="story-art">\n'
                        f'    <img src="images/{ill["id"]}.jpg" alt="{alt}"/>\n'
                        f'    <figcaption>{cap}</figcaption>\n'
                        f'  </figure>'
                    )

            xhtml = (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<!DOCTYPE html>\n'
                '<html xmlns="http://www.w3.org/1999/xhtml" lang="en">\n'
                f'<head><title>{html.escape(ch["title"])}</title><link rel="stylesheet" type="text/css" href="styles.css"/></head>\n'
                '<body>\n' + "\n".join(body_parts) + "\n</body>\n</html>\n"
            )
            z.writestr(f"EPUB/{chap_href}", xhtml, compress_type=ZIP_DEFLATED)

        nav_xhtml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE html>\n'
            '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en">\n'
            '<head><title>Contents</title><link rel="stylesheet" type="text/css" href="styles.css"/></head>\n'
            '<body>\n'
            '  <nav epub:type="toc" id="toc">\n'
            '    <h1>The Three Paths</h1>\n'
            '    <ol>\n' + "\n".join(nav_lis) + '\n    </ol>\n'
            '  </nav>\n'
            '</body>\n'
            '</html>\n'
        )
        z.writestr("EPUB/nav.xhtml", nav_xhtml, compress_type=ZIP_DEFLATED)

        opf = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">\n'
            '  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
            f'    <dc:identifier id="bookid">urn:uuid:{book_uid}</dc:identifier>\n'
            '    <dc:title>The Three Paths</dc:title>\n'
            '    <dc:language>en</dc:language>\n'
            '    <dc:creator>Glassvale Book Studio</dc:creator>\n'
            '    <meta property="dcterms:modified">2026-11-27T16:00:00Z</meta>\n'
            '  </metadata>\n'
            '  <manifest>\n    ' + "\n    ".join(manifest_items) + '\n  </manifest>\n'
            '  <spine>\n    ' + "\n    ".join(spine_items) + '\n  </spine>\n'
            '</package>\n'
        )
        z.writestr("EPUB/package.opf", opf, compress_type=ZIP_DEFLATED)


def main() -> None:
    book_meta = json.loads((BOOK / "book.json").read_text(encoding="utf-8"))
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))

    cover_jpg = OUT / "cover.jpg"
    out_pdf = OUT / "the-three-paths.pdf"
    out_epub = OUT / "the-three-paths.epub"

    build_cover(cover_jpg)
    _, chap_pages = build_pdf(book_meta, plan, cover_jpg, out_pdf)
    build_epub(book_meta, plan, cover_jpg, out_epub)

    for label, p in [("cover.jpg", cover_jpg), ("the-three-paths.pdf", out_pdf), ("the-three-paths.epub", out_epub)]:
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        print(f"{label}: {p.stat().st_size} bytes | sha256={h}")
    print("Chapter starting pages:", chap_pages)


if __name__ == "__main__":
    main()
