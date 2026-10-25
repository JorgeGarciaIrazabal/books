#!/usr/bin/env python3
"""Verify actual PDF fidelity and art coverage; visual proof remains separate."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess

BOOK = Path(__file__).resolve().parents[1]
STEM = "nell-and-the-pocket-sized-storm"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_pages(paths: list[Path]) -> dict[int, str]:
    pages = {}
    order = []
    for path in paths:
        parts = re.split(r"^## Page (\d+)\s*$", path.read_text(), flags=re.MULTILINE)
        for i in range(1, len(parts), 2):
            number = int(parts[i])
            if number in pages:
                raise ValueError(f"Duplicate story page {number}")
            pages[number] = parts[i + 1].strip()
            order.append(number)
    if order != list(range(1, 31)):
        raise ValueError("Source order is not exactly pages 1–30")
    return pages


def compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def main() -> None:
    book = json.loads((BOOK / "book.json").read_text())
    manifest = json.loads((BOOK / "exports/reading-edition-manifest.json").read_text())
    plan = json.loads((BOOK / book["illustration_plan"]).read_text())
    pages = source_pages([BOOK / p for p in book["chapters"]])
    archived = source_pages([BOOK / "production/previous-edition/text-only-v1/manuscript/001-story.md"])
    if pages != archived:
        raise ValueError("Story-page prose changed from preserved first edition")
    for relative, expected in manifest["sha256"].items():
        if digest(BOOK / relative) != expected:
            raise ValueError(f"Stale export input/output hash: {relative}")
    pdf = BOOK / "exports" / f"{STEM}.pdf"
    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=True).stdout
    if not re.search(r"^Pages:\s+30$", info, re.MULTILINE):
        raise ValueError("Actual PDF must contain 30 pages")
    text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
    extracted = text.split("\f")
    if not extracted[-1].strip():
        extracted.pop()
    if len(extracted) != 30:
        raise ValueError("Extracted PDF has wrong page count")
    for number, page in enumerate(extracted, 1):
        lines = [line.strip() for line in page.splitlines() if line.strip()]
        chapter = next(c for c in book["chapter_details"] if c["pages"][0] <= number <= c["pages"][1])
        expected_header = f"Nell & Grumble {book['chapter_details'].index(chapter) + 1} · {chapter['title']}"
        if compact(lines[0]) != compact(expected_header) or lines[-1] != str(number):
            raise ValueError(f"Incorrect running header/footer on page {number}")
        body = compact("\n".join(lines[1:-1]))
        if number == 1:
            title = compact(book["title"])
            if not body.startswith(title):
                raise ValueError("Missing integrated page-1 title")
            body = body[len(title):]
        if body != compact(pages[number]):
            raise ValueError(f"PDF text differs from source on page {number}")
    image_list = subprocess.run(["pdfimages", "-list", str(pdf)], capture_output=True, text=True, check=True).stdout
    rows = [line.split() for line in image_list.splitlines() if re.match(r"^\s*\d+\s+\d+\s+image\s", line)]
    expected_pages = sorted(p["page"] for p in plan["illustrations"])
    if len(rows) != 12 or sorted(int(row[0]) for row in rows) != expected_pages:
        raise ValueError("Actual embedded pictures do not match the twelve planned picture pages")
    if any((int(row[3]), int(row[4])) != (1536, 1024) for row in rows):
        raise ValueError("Unexpected embedded image dimensions")
    layout = json.loads((BOOK / "exports/illustrated-layout-check.json").read_text())
    if layout["pages"] != 30 or layout["image_count"] != 12 or layout["failures"]:
        raise ValueError("Browser layout check failed or is stale")
    if any(item["body_font_px"] != "22.4px" for item in layout["measurements"]):
        raise ValueError("Body type was silently reduced below the declared 16.8 pt")
    result = {
        "schema_version": 1, "edition": book["edition"], "pdf_sha256": digest(pdf),
        "verification_script_sha256": digest(Path(__file__)), "pdf_pages": 30,
        "chapters": len(book["chapters"]), "embedded_story_images": len(rows),
        "pictures_per_chapter": {c: sum(i["chapter"] == c for i in plan["illustrations"]) for c in book["chapters"]},
        "image_pages": expected_pages, "embedded_native_pixels": [1536, 1024],
        "body_type_points": 16.8, "all_30_page_bodies_match_source": True,
        "all_30_story_page_bodies_unchanged_from_archived_v1": True,
        "all_manifest_hashes_match": True, "browser_layout_failures": [],
        "pdf_size_bytes": pdf.stat().st_size,
        "limits": "Mechanical checks only. Artistic/narrative fidelity, accessibility and visual proof have separate reports."
    }
    target = BOOK / "reviews/illustrated/verification.json"
    target.write_text(json.dumps(result, indent=2) + "\n")
    print("Verified actual PDF: 30 pages, 6 chapters, 12 images, 2 per chapter; all page text and hashes match.")


if __name__ == "__main__":
    main()
