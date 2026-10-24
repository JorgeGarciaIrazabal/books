"""Behavior checks for scaffolding, safe assembly, and context/record integrity."""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

SPEC = importlib.util.spec_from_file_location("studio", Path(__file__).resolve().parents[1] / "tools/studio.py")
studio = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(studio)


class StudioTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.book = self.root / "world/sequence/book-01"
        self.quiet = contextlib.redirect_stdout(io.StringIO())

    def new(self, slug="book-01", **kwargs):
        args = argparse.Namespace(universe="world", series="sequence", book=slug,
                                  title=kwargs.get("title", "A Book"), kind="fiction", dry_run=kwargs.get("dry_run", False))
        with contextlib.redirect_stdout(io.StringIO()):
            studio.new_book(self.root, args)

    def manifest(self, **values):
        path = self.book / "book.json"
        data = studio.read_json(path)
        data.update(values)
        path.write_text(studio.json_text(data))

    def test_scaffold_and_shared_records_are_preserved(self):
        self.new(title='A "Quoted" Title\nWith a newline')
        canon = self.root / "world/canon.json"
        canon.write_text('{"schema_version":1,"facts":[{"id":"FACT-0001","text":"Keep me"}]}')
        before = canon.read_bytes()
        self.new("book-02")
        self.assertEqual(canon.read_bytes(), before)
        self.assertEqual(studio.read_json(self.book.parent / "series.json")["books"], ["book-01", "book-02"])
        self.assertEqual(studio.read_json(self.book / "book.json")["title"], 'A "Quoted" Title\nWith a newline')
        errors, _ = studio.check_book(self.root, self.book)
        self.assertEqual(errors, [])

    def test_existing_book_is_never_overwritten(self):
        self.new()
        path = self.book / "brief.md"
        path.write_text("Human work")
        with self.assertRaises(ValueError):
            self.new()
        self.assertEqual(path.read_text(), "Human work")

    def test_dry_run_does_not_write(self):
        self.new(dry_run=True)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_invalid_or_reserved_paths_are_rejected(self):
        for relative in ("../x/y", "world/book", "templates/sequence/book", "World/sequence/book", "world/sequence/../../escape"):
            with self.subTest(relative=relative), self.assertRaises(ValueError):
                studio.book_path(self.root, relative)

    def test_build_uses_manifest_order_and_omits_unlisted_files(self):
        self.new()
        manuscript = self.book / "manuscript"
        for name, text in (("002-second.md", "SECOND"), ("001-first.md", "FIRST"), ("unused.md", "SECRET")):
            (manuscript / name).write_text(text)
        self.manifest(chapters=["manuscript/002-second.md", "manuscript/001-first.md"])
        args = argparse.Namespace(book="world/sequence/book-01", name="draft-01", replace=False)
        with contextlib.redirect_stdout(io.StringIO()):
            studio.build(self.root, args)
        self.assertEqual((self.book / "exports/draft-01.md").read_text(), "SECOND\n\nFIRST\n")
        self.assertEqual((manuscript / "unused.md").read_text(), "SECRET")
        export = studio.read_json(self.book / "exports/draft-01.manifest.json")
        self.assertEqual(export["editorial_status"], "unverified")
        for source in export["sources"]:
            self.assertEqual(source["sha256"], hashlib.sha256((self.book / source["path"]).read_bytes()).hexdigest())
        self.assertEqual(export["output_sha256"], hashlib.sha256((self.book / export["output"]).read_bytes()).hexdigest())
        with self.assertRaises(ValueError):
            studio.build(self.root, args)

    def test_chapters_cannot_escape_or_repeat(self):
        self.new()
        (self.book / "manuscript/a.md").write_text("Text")
        for chapters in (["../other.md"], ["brief.md"], ["manuscript/a.md", "manuscript/a.md"], ["manuscript/missing.md"]):
            with self.subTest(chapters=chapters), self.assertRaises(ValueError):
                studio.chapter_paths(self.book, {"chapters": chapters})

    def test_symlink_escape_is_rejected(self):
        self.new()
        outside = self.root / "outside.md"
        outside.write_text("Do not include")
        (self.book / "manuscript/escape.md").symlink_to(outside)
        with self.assertRaises(ValueError):
            studio.chapter_paths(self.book, {"chapters": ["manuscript/escape.md"]})

    def test_oversize_packet_omits_whole_files_and_reports_them(self):
        self.new()
        (self.book / "outline.md").write_text("SPOILER" * 2000)
        args = argparse.Namespace(book="world/sequence/book-01", task="Test", mode="draft", include=[], max_chars=6000)
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            studio.packet(self.root, args)
        text = output.getvalue()
        self.assertLessEqual(len(text), args.max_chars)
        self.assertNotIn("SPOILER", text)
        self.assertIn("## Omitted for size\nworld/sequence/book-01/outline.md", text)
        self.assertIn("SHA-256:", text)

    def test_review_packet_excludes_drafter_rationale_by_default(self):
        self.new()
        (self.book / "handoff.md").write_text("DRAFTER DEFENSE")
        (self.book / "outline.md").write_text("EARLIER VERDICT")
        args = argparse.Namespace(book="world/sequence/book-01", task="Independent read", mode="review", include=[], max_chars=10000)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            studio.packet(self.root, args)
        self.assertNotIn("DRAFTER DEFENSE", output.getvalue())
        self.assertNotIn("EARLIER VERDICT", output.getvalue())

    def test_checker_catches_bad_claim_reference_and_duplicate_ids(self):
        self.new()
        (self.book / "research/claims.json").write_text(studio.json_text({"schema_version": 1, "claims": [
            {"id": "CLM-0001", "status": "verified", "evidence": [{"source_id": "MISSING"}]}]}))
        (self.book / "scenes.json").write_text(studio.json_text({"schema_version": 1, "scenes": [{"id": "SC-1"}, {"id": "SC-1"}]}))
        errors, _ = studio.check_book(self.root, self.book)
        self.assertTrue(any("unknown source" in error for error in errors))
        self.assertTrue(any("locators" in error for error in errors))
        self.assertTrue(any("Duplicate record" in error for error in errors))

    def test_malformed_records_report_errors_instead_of_crashing(self):
        self.new()
        (self.book / "research/sources.json").write_text('{"schema_version":1,"sources":null}')
        (self.book / "tasks.json").write_text('{"schema_version":1,"tasks":[null]}')
        errors, _ = studio.check_book(self.root, self.book)
        self.assertGreaterEqual(len(errors), 2)

    def ready_export(self):
        self.new()
        (self.book / "manuscript/draft.md").write_text("FIRST\n")
        (self.book / "manuscript/other.md").write_text("SECOND\n")
        self.manifest(chapters=["manuscript/draft.md", "manuscript/other.md"])
        return argparse.Namespace(book="world/sequence/book-01", name="draft", replace=True)

    def test_export_directory_cannot_alias_manuscript(self):
        args = self.ready_export()
        exports = self.book / "exports"
        (exports / ".gitkeep").unlink()
        exports.rmdir()
        exports.symlink_to(self.book / "manuscript", target_is_directory=True)
        with self.assertRaises(ValueError):
            studio.build(self.root, args)
        self.assertEqual((self.book / "manuscript/draft.md").read_text(), "FIRST\n")

    def test_default_packet_inputs_cannot_escape_book(self):
        self.new()
        outside = self.root / "private.md"
        outside.write_text("PRIVATE TEXT")
        brief = self.book / "brief.md"
        brief.unlink()
        brief.symlink_to(outside)
        args = argparse.Namespace(book="world/sequence/book-01", task="Review", mode="review", include=[], max_chars=10000)
        output = io.StringIO()
        with contextlib.redirect_stdout(output), self.assertRaises(ValueError):
            studio.packet(self.root, args)
        self.assertNotIn("PRIVATE TEXT", output.getvalue())

    def test_failed_export_restores_existing_pair(self):
        args = self.ready_export()
        with contextlib.redirect_stdout(io.StringIO()):
            studio.build(self.root, args)
        output = self.book / "exports/draft.md"
        manifest = self.book / "exports/draft.manifest.json"
        before = {p: p.read_bytes() for p in (output, manifest)}
        (self.book / "manuscript/draft.md").write_text("REVISED\n")
        original_write = studio.atomic_write
        failed = False

        def fail_manifest_once(path, content):
            nonlocal failed
            if path == manifest and not failed:
                failed = True
                raise OSError("Injected manifest-write failure")
            return original_write(path, content)

        with mock.patch.object(studio, "atomic_write", side_effect=fail_manifest_once), self.assertRaises(OSError):
            studio.build(self.root, args)
        for path, expected in before.items():
            self.assertEqual(path.read_bytes(), expected)

    def test_failed_new_export_leaves_no_partial_pair(self):
        args = self.ready_export()
        output = self.book / "exports/draft.md"
        manifest = self.book / "exports/draft.manifest.json"
        original_write = studio.atomic_write

        def fail_manifest(path, content):
            if path == manifest:
                raise OSError("Injected manifest-write failure")
            return original_write(path, content)

        with mock.patch.object(studio, "atomic_write", side_effect=fail_manifest), self.assertRaises(OSError):
            studio.build(self.root, args)
        self.assertFalse(output.exists())
        self.assertFalse(manifest.exists())

    def test_export_preflights_both_targets(self):
        args = self.ready_export()
        (self.book / "exports/draft.manifest.json").mkdir()
        with self.assertRaises((OSError, ValueError)):
            studio.build(self.root, args)
        self.assertFalse((self.book / "exports/draft.md").exists())

    def test_scaffold_rollback_preserves_unrelated_concurrent_directory(self):
        self.new()
        series = self.book.parent / "series.json"
        before = series.read_bytes()
        unrelated = self.book / "research/new-notes"
        original_write = studio.atomic_write
        calls = 0

        def fail_during_scaffold(path, content):
            nonlocal calls
            calls += 1
            if calls == 5:
                unrelated.mkdir()
                raise OSError("Injected scaffold-write failure")
            return original_write(path, content)

        with mock.patch.object(studio, "atomic_write", side_effect=fail_during_scaffold), self.assertRaises(OSError):
            self.new("book-02")
        self.assertTrue(unrelated.is_dir())
        self.assertFalse((self.book.parent / "book-02").exists())
        self.assertEqual(series.read_bytes(), before)

    def test_wrong_type_manifests_return_cli_errors(self):
        self.new()
        (self.book / "book.json").write_text("[]")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(studio.main(["--root", str(self.root), "build", "world/sequence/book-01"]), 1)
        (self.root / "world/universe.json").write_text("[]")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(studio.main(["--root", str(self.root), "new", "world", "sequence", "book-02"]), 1)

    def test_packet_hash_matches_source_bytes_with_crlf(self):
        self.new()
        raw = b"first\r\nsecond\r\n"
        (self.book / "brief.md").write_bytes(raw)
        args = argparse.Namespace(book="world/sequence/book-01", task="Review", mode="review", include=[], max_chars=10000)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            studio.packet(self.root, args)
        self.assertIn("SHA-256: " + hashlib.sha256(raw).hexdigest(), output.getvalue())



if __name__ == "__main__":
    unittest.main()
