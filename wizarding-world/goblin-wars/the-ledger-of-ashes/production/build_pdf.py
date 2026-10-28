#!/usr/bin/env python3
"""Build the public reading PDF for The Ledger of Ashes.

Chapter order and prose come only from book.json and the manuscript. The story
text is not rewritten. This is a reading edition with a title page, public
fan-fiction notice, linked contents and running page numbers.

Run with reportlab available, for example:
    uv run --with reportlab python production/build_pdf.py
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import inch
from reportlab.lib.styles import ParagraphStyle
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
PAGE = (6 * inch, 9 * inch)
MARGIN_X = 54
MARGIN_TOP = 58
MARGIN_BOTTOM = 60
INK = HexColor("#2f2a24")
MUTED = HexColor("#6d6357")
RULE = HexColor("#9b8a6d")
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
for name, file in [
    ("Story", "DejaVuSerif.ttf"),
    ("StoryBold", "DejaVuSerif-Bold.ttf"),
    ("StoryItalic", "DejaVuSerif-Italic.ttf"),
    ("Label", "DejaVuSans.ttf"),
]:
    pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / file)))
pdfmetrics.registerFontFamily(
    "Story", normal="Story", bold="StoryBold", italic="StoryItalic", boldItalic="StoryBold"
)

BODY = ParagraphStyle(
    "Body", fontName="Story", fontSize=11.2, leading=16.4, textColor=INK,
    spaceAfter=5.5, alignment=0, firstLineIndent=0,
)
CHAPTER = ParagraphStyle(
    "ChapterTitle", fontName="StoryBold", fontSize=17, leading=21, textColor=INK,
    spaceBefore=0, spaceAfter=18, keepWithNext=1,
)
TITLE = ParagraphStyle(
    "Title", fontName="Story", fontSize=30, leading=34, textColor=INK,
    alignment=TA_CENTER, spaceAfter=0,
)
SERIES = ParagraphStyle(
    "Series", fontName="Label", fontSize=9, leading=14, textColor=MUTED,
    alignment=TA_CENTER, spaceAfter=30, charSpace=2.2,
)
EDITION = ParagraphStyle(
    "Edition", fontName="StoryItalic", fontSize=13, leading=18, textColor=MUTED,
    alignment=TA_CENTER, spaceBefore=18, spaceAfter=0,
)
NOTICE = ParagraphStyle(
    "Notice", fontName="Label", fontSize=8.5, leading=13, textColor=MUTED,
    alignment=TA_CENTER, spaceBefore=28,
)
ABOUT = ParagraphStyle(
    "About", fontName="Story", fontSize=10.6, leading=16, textColor=INK, spaceAfter=8,
)
ABOUT_HEAD = ParagraphStyle(
    "AboutHead", fontName="StoryBold", fontSize=17, leading=21, textColor=INK,
    spaceBefore=0, spaceAfter=16,
)
TOC_HEAD = ParagraphStyle(
    "TocHead", fontName="StoryBold", fontSize=17, leading=21, textColor=INK,
    spaceBefore=0, spaceAfter=18,
)


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def load_chapters() -> list[dict]:
    meta = json.loads((BOOK / "book.json").read_text(encoding="utf-8"))
    paths = meta["chapters"]
    if len(paths) != 22 or len(set(paths)) != len(paths):
        raise ValueError("Expected the 22 distinct declared chapters")
    chapters = []
    for index, relative in enumerate(paths, 1):
        raw = (BOOK / relative).read_text(encoding="utf-8").strip()
        heading, body = raw.split("\n", 1)
        if not heading.startswith("# "):
            raise ValueError(f"No chapter heading: {relative}")
        title = heading[2:].strip()
        paragraphs = [normalise(p) for p in re.split(r"\n\s*\n", body.strip()) if p.strip()]
        if any(re.search(r"^[#*]|<!--", p) for p in paragraphs):
            raise ValueError(f"Unsupported manuscript markup in {relative}")
        chapters.append(
            {
                "number": index,
                "source": relative,
                "title": title,
                "paragraphs": paragraphs,
                "sha256": hashlib.sha256((BOOK / relative).read_bytes()).hexdigest(),
            }
        )
    return chapters


class BookDoc(BaseDocTemplate):
    def __init__(self, filename: str, **kwargs):
        super().__init__(filename, **kwargs)
        self.book_title = "The Ledger of Ashes"
        self._chapter_keys: dict[str, str] = {}

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == "ChapterTitle":
            text = flowable.getPlainText()
            key = f"chapter-{len(self._chapter_keys) + 1:02d}"
            self._chapter_keys[key] = text
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=0, closed=False)
            self.notify("TOCEntry", (0, text, self.page))


def draw_body_page(canv: canvas.Canvas, doc: BookDoc):
    canv.saveState()
    width, height = PAGE
    canv.setFillColor(INK)
    canv.setFont("Label", 8)
    canv.drawString(MARGIN_X, height - 34, "THE LEDGER OF ASHES")
    canv.setFillColor(MUTED)
    canv.drawRightString(width - MARGIN_X, height - 34, "UNOFFICIAL FAN FICTION")
    canv.setStrokeColor(RULE)
    canv.setLineWidth(0.4)
    canv.line(MARGIN_X, height - 42, width - MARGIN_X, height - 42)
    canv.setFont("Story", 9)
    canv.setFillColor(MUTED)
    canv.drawCentredString(width / 2, 32, str(doc.page))
    canv.restoreState()


def draw_plain_page(canv: canvas.Canvas, doc: BookDoc):
    pass


def build() -> dict:
    chapters = load_chapters()
    OUT.mkdir(exist_ok=True)
    output = OUT / "the-ledger-of-ashes.pdf"
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
        title="The Ledger of Ashes",
        subject="Unofficial Wizarding World fan fiction",
        author="",
        creator="Book Studio",
        keywords="fan fiction, historical fantasy, goblins, 1752",
    )
    doc.addPageTemplates(
        [
            PageTemplate(id="Plain", frames=[frame], onPage=draw_plain_page),
            PageTemplate(id="Body", frames=[frame], onPage=draw_body_page),
        ]
    )

    story = []
    story.append(Spacer(1, 84))
    story.append(Paragraph("THE GOBLIN WARS", SERIES))
    story.append(Paragraph("The Ledger<br/>of Ashes", TITLE))
    story.append(Spacer(1, 18))
    story.append(Paragraph("BOOK ONE", EDITION))
    story.append(Paragraph("UNOFFICIAL FAN FICTION", NOTICE))
    story.append(PageBreak())

    story.append(Paragraph("About this edition", ABOUT_HEAD))
    story.append(
        Paragraph(
            "This is unofficial fan fiction set in the Harry Potter and Wizarding World setting. "
            "It is not an official or endorsed publication. Harry Potter and the Wizarding World "
            "are properties of their respective rights holders. This free fan work is not authorised, "
            "endorsed or sponsored by them, and no official status is claimed.",
            ABOUT,
        )
    )
    story.append(
        Paragraph(
            "The story follows original characters in an imagined account of the goblin rebellions. "
            "The edition contains twenty-two chapters. Narration, where published, is a separate "
            "performance and is not embedded in this book.",
            ABOUT,
        )
    )
    story.append(
        Paragraph(
            "Published by the author as a free fan work. No endorsement, licence or affiliation is implied.",
            ABOUT,
        )
    )
    story.append(PageBreak())

    story.append(NextPageTemplate("Body"))
    story.append(Paragraph("Contents", TOC_HEAD))
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(
            "TOCEntry", fontName="Story", fontSize=9.2, leading=12.6, textColor=INK,
            leftIndent=0, firstLineIndent=0, spaceBefore=0,
        )
    ]
    toc.dotsMinLevel = -1
    story.append(toc)
    story.append(PageBreak())

    for index, chapter in enumerate(chapters):
        if index:
            story.append(PageBreak())
        story.append(Paragraph(escape(chapter["title"]), CHAPTER))
        for paragraph in chapter["paragraphs"]:
            story.append(Paragraph(escape(paragraph), BODY))

    doc.multiBuild(story)

    raw = output.read_bytes()
    return {
        "pdf": str(output),
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "pages": doc.page,
        "chapter_count": len(chapters),
        "story_words": sum(len(" ".join(c["paragraphs"]).split()) for c in chapters),
        "chapter_titles": [c["title"] for c in chapters],
        "source_sha256": {c["source"]: c["sha256"] for c in chapters},
        "checks": [
            "all 22 declared chapters in book.json order",
            "title, about, contents and chapter text rendered",
            "PDF header and EOF written by reportlab",
            "no performance tags in source",
            "running page numbers and bookmarks",
        ],
        "limitations": [
            "No human page-by-page proof of the PDF layout",
            "Fonts are embedded DejaVu; no print-profile colour management",
            "Franchise rights remain with their holders; this is a free fan work",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2))
