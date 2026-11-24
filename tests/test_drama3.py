"""Regression tests for tools/drama3.py."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("drama3", ROOT / "tools" / "drama3.py")
drama3 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(drama3)


class Drama3PrepTests(unittest.TestCase):
    def test_prepare_chapters_is_word_exact_and_respects_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            book = Path(tmp) / "book"
            ms = book / "manuscript"
            ms.mkdir(parents=True)
            ch1 = "# Chapter 1: First\n\n*POP!* One two three. Four five six seven eight.\n\nNine ten eleven twelve.\n"
            ch2 = "# Chapter 2: Second\n\nAlpha beta gamma. Delta epsilon zeta eta theta.\n"
            (ms / "001.md").write_text(ch1, encoding="utf-8")
            (ms / "002.md").write_text(ch2, encoding="utf-8")
            (book / "book.json").write_text(
                json.dumps({"id": "sample", "title": "Sample", "chapters": ["manuscript/001.md", "manuscript/002.md"]}),
                encoding="utf-8",
            )
            out = Path(tmp) / "segments.json"
            script = Path(tmp) / "script.md"
            rc = drama3.main(["prepare-chapters", "--book", str(book), "--out", str(out), "--script", str(script), "--max-words", "10"])
            self.assertEqual(rc, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(len(data["chapters"]), 2)
            ch1_segs = [p["text"] for p in data["pages"] if p["chapter"] == 1]
            ch2_segs = [p["text"] for p in data["pages"] if p["chapter"] == 2]
            self.assertIn("\n\n", ch1_segs[0])
            self.assertEqual(
                drama3.normalize_ws(" ".join(ch1_segs)),
                "Chapter 1: First POP! One two three. Four five six seven eight. Nine ten eleven twelve.",
            )
            self.assertEqual(
                drama3.normalize_ws(" ".join(ch2_segs)),
                "Chapter 2: Second Alpha beta gamma. Delta epsilon zeta eta theta.",
            )
            self.assertNotIn("*", " ".join(ch1_segs))
            self.assertIn("<|speaker:0|>", script.read_text(encoding="utf-8"))

    def test_split_into_parts_preserves_exact_words(self) -> None:
        text = "One two three four five. Six seven eight nine ten. Eleven twelve thirteen fourteen fifteen."
        parts = drama3.split_into_parts(text, part_limit=6)
        self.assertGreaterEqual(len(parts), 2)
        self.assertEqual(" ".join(parts), text)

    def test_prepare_pages_rejects_word_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            export = p / "book.md"
            script = p / "script.md"
            out = p / "pages.json"
            export.write_text("## Page 1\n\nHello world.\n", encoding="utf-8")
            script.write_text("## Page 1\n\n```text\n<|speaker:0|> [warm] Hello brave world.\n```\n", encoding="utf-8")
            rc = drama3.main(["prepare-pages", str(script), str(export), str(out)])
            self.assertEqual(rc, 1)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
