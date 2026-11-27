"""Regression tests for tools/drama3.py."""
from __future__ import annotations

import array
import importlib.util
import json
import shutil
import tempfile
import unittest
import wave
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

    def test_prepare_chapters_preserves_paragraph_breaks_and_ends_paragraph(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            book = Path(tmp) / "book"
            ms = book / "manuscript"
            ms.mkdir(parents=True)
            ch1 = (
                "# Chapter 1: Test\n\n"
                "One two three four. Five six seven.\n\n"
                "Eight nine ten eleven twelve.\n\n"
                "Thirteen fourteen fifteen. Sixteen seventeen eighteen nineteen.\n"
            )
            (ms / "001.md").write_text(ch1, encoding="utf-8")
            (book / "book.json").write_text(
                json.dumps({"id": "sample", "title": "Sample", "chapters": ["manuscript/001.md"]}),
                encoding="utf-8",
            )
            out = Path(tmp) / "segments.json"
            rc = drama3.main(["prepare-chapters", "--book", str(book), "--out", str(out), "--max-words", "11"])
            self.assertEqual(rc, 0)
            pages = json.loads(out.read_text(encoding="utf-8"))["pages"]
            self.assertEqual(len(pages), 3)
            self.assertIn("\n\n", pages[0]["text"])
            self.assertTrue(pages[0]["ends_paragraph"])
            self.assertIn("\n\n", pages[1]["text"])
            self.assertFalse(pages[1]["ends_paragraph"])
            self.assertTrue(pages[2]["ends_paragraph"])
            self.assertEqual(
                drama3.normalize_ws(" ".join(p["text"] for p in pages)),
                "Chapter 1: Test One two three four. Five six seven. Eight nine ten eleven twelve. "
                "Thirteen fourteen fifteen. Sixteen seventeen eighteen nineteen.",
            )


def _write_test_wav(path: Path, lead_ms: int, tone_ms: int, trail_ms: int, sr: int = 24000) -> None:
    lead = [0] * int(sr * lead_ms / 1000)
    tone = [8000 if (i // 12) % 2 == 0 else -8000 for i in range(int(sr * tone_ms / 1000))]
    trail = [0] * int(sr * trail_ms / 1000)
    samples = array.array("h", lead + tone + trail)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(samples.tobytes())


class Drama3AudioGapTests(unittest.TestCase):
    def test_measure_wav_edge_silence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            wav = Path(tmp) / "clip.wav"
            _write_test_wav(wav, lead_ms=40, tone_ms=200, trail_ms=130)
            lead_ms, trail_ms = drama3.measure_wav_edge_silence(wav)
            self.assertEqual((lead_ms, trail_ms), (40, 130))

    def test_concat_wavs_with_gaps_pads_only_short_joins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            a = p / "a.wav"
            b = p / "b.wav"
            c = p / "c.wav"
            d = p / "d.wav"
            _write_test_wav(a, lead_ms=30, tone_ms=100, trail_ms=30)
            _write_test_wav(b, lead_ms=30, tone_ms=100, trail_ms=600)
            _write_test_wav(c, lead_ms=250, tone_ms=100, trail_ms=5)
            _write_test_wav(d, lead_ms=5, tone_ms=100, trail_ms=20)

            out = p / "joined.wav"
            stats = drama3.concat_wavs_with_gaps([a, b, c, d], [500, 750, 500], out)
            self.assertEqual(stats["joins"], 3)
            # Join 0 (a->b): raw=60 -> padded by 440ms to 500ms.
            # Join 1 (b->c): raw=850 >= 750 -> padded by 0ms.
            # Join 2 (c->d): raw=10 -> padded by 490ms to 500ms (with 5ms fades).
            self.assertEqual(stats["padded_joins"], 2)
            self.assertEqual(stats["min_raw_gap_ms"], 10)
            self.assertEqual(stats["min_final_gap_ms"], 500)
            self.assertEqual(stats["total_added_ms"], 930)

            out_zero = p / "joined_zero.wav"
            stats_zero = drama3.concat_wavs_with_gaps([a, b], [0], out_zero)
            self.assertEqual(stats_zero["total_added_ms"], 0)
            self.assertEqual(stats_zero["padded_joins"], 0)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg/ffprobe required")
    def test_assemble_chapters_respects_gap_padding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            audio = p / "audio"
            audio.mkdir()
            _write_test_wav(audio / "page-01.wav", lead_ms=30, tone_ms=300, trail_ms=30)
            _write_test_wav(audio / "page-02.wav", lead_ms=30, tone_ms=300, trail_ms=30)
            segments = p / "segments.json"
            segments.write_text(
                json.dumps({
                    "schema_version": 1,
                    "kind": "chapter_segments",
                    "book_id": "test-book",
                    "title": "Test Book",
                    "chapters": [{
                        "chapter": 1,
                        "path": "manuscript/001.md",
                        "title": "Chapter 1",
                        "source_sha256": "0" * 64,
                        "spoken_sha256": "0" * 64,
                        "words": 10,
                        "segments": 2,
                    }],
                    "pages": [
                        {"page": 1, "chapter": 1, "segment": 1, "text": "Hello.", "ends_paragraph": True},
                        {"page": 2, "chapter": 1, "segment": 2, "text": "World.", "ends_paragraph": True},
                    ],
                }),
                encoding="utf-8",
            )
            out_dir = p / "site_audio"
            rc = drama3.main([
                "assemble-chapters", str(segments),
                "--audio", str(audio),
                "--out", str(out_dir),
                "--paragraph-gap-ms", "750",
            ])
            self.assertEqual(rc, 0)
            manifest = json.loads((out_dir / "chapters.json").read_text(encoding="utf-8"))
            self.assertGreaterEqual(manifest["chapters"][0]["seconds"], 1.35)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg/ffprobe required")
    def test_assemble_chapters_builds_full_book_and_respects_max_mb(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            audio = p / "audio"
            audio.mkdir()
            _write_test_wav(audio / "page-01.wav", lead_ms=30, tone_ms=300, trail_ms=30)
            _write_test_wav(audio / "page-02.wav", lead_ms=30, tone_ms=300, trail_ms=30)
            segments = p / "segments.json"
            segments.write_text(
                json.dumps({
                    "schema_version": 1,
                    "kind": "chapter_segments",
                    "book_id": "test-book",
                    "title": "Test Book",
                    "chapters": [
                        {
                            "chapter": 1, "path": "manuscript/001.md", "title": "Ch 1",
                            "source_sha256": "0" * 64, "spoken_sha256": "0" * 64, "words": 5, "segments": 1,
                        },
                        {
                            "chapter": 2, "path": "manuscript/002.md", "title": "Ch 2",
                            "source_sha256": "0" * 64, "spoken_sha256": "0" * 64, "words": 5, "segments": 1,
                        },
                    ],
                    "pages": [
                        {"page": 1, "chapter": 1, "segment": 1, "text": "Hello.", "ends_paragraph": True},
                        {"page": 2, "chapter": 2, "segment": 1, "text": "World.", "ends_paragraph": True},
                    ],
                }),
                encoding="utf-8",
            )
            out_dir = p / "site_audio"
            rc = drama3.main([
                "assemble-chapters", str(segments),
                "--audio", str(audio), "--out", str(out_dir),
                "--chapter-gap-seconds", "1.0",
            ])
            self.assertEqual(rc, 0)
            manifest = json.loads((out_dir / "chapters.json").read_text(encoding="utf-8"))
            self.assertIn("full_book", manifest)
            self.assertTrue((out_dir / "full-book.mp3").is_file())
            self.assertEqual(manifest["chapters"][0]["start_seconds"], 0.0)
            self.assertGreater(manifest["chapters"][1]["start_seconds"], manifest["chapters"][0]["seconds"])

            out_skip = p / "site_audio_skip"
            rc2 = drama3.main([
                "assemble-chapters", str(segments),
                "--audio", str(audio), "--out", str(out_skip),
                "--full-book-max-mb", "0",
            ])
            self.assertEqual(rc2, 0)
            manifest2 = json.loads((out_skip / "chapters.json").read_text(encoding="utf-8"))
            self.assertNotIn("full_book", manifest2)
            self.assertFalse((out_skip / "full-book.mp3").exists())


if __name__ == "__main__":
    unittest.main()
