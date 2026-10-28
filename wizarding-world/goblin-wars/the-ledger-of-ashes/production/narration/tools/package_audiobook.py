#!/usr/bin/env python3
"""Assemble verified segment WAVs into chapter MP3s for the public site.

This script does not listen to audio and does not claim a listening review. It
verifies coverage and hashes, concatenates each chapter in source order, and
records the machine checks. A human must still hear the result before it is
described as a finished performance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=nw=1:nk=1", str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("segments", type=Path)
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--render", type=Path, required=True)
    parser.add_argument("--checks", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--book-id", default="the-ledger-of-ashes")
    parser.add_argument("--bitrate", default="96k")
    parser.add_argument("--sample-rate", default="24000")
    parser.add_argument("--credit", default="Synthetic narration generated locally; not a human performance.")
    parser.add_argument("--voice", default=None)
    parser.add_argument("--review-status", default="Coverage checked; human listening pending.")
    args = parser.parse_args()

    source = json.loads(args.segments.read_text(encoding="utf-8"))
    render = json.loads(args.render.read_text(encoding="utf-8"))
    rows = source["pages"]
    files = {row["page"]: row for row in render["files"]}
    if set(files) != {row["page"] for row in rows}:
        raise SystemExit("Render record does not cover every segment exactly once")
    expected = {f"page-{row['page']:02d}.wav" for row in rows}
    actual = {path.name for path in args.audio.glob("page-*.wav")}
    if expected != actual:
        raise SystemExit(f"missing={sorted(expected - actual)} extra={sorted(actual - expected)}")
    for row in rows:
        path = args.audio / f"page-{row['page']:02d}.wav"
        if sha256(path) != files[row["page"]]["sha256"]:
            raise SystemExit(f"hash mismatch: {path}")

    checks = None
    if args.checks and args.checks.is_file():
        checks = json.loads(args.checks.read_text(encoding="utf-8"))
        checked = {row["page"] for row in checks.get("segments", [])}
        if checked != {row["page"] for row in rows}:
            raise SystemExit("ASR check record does not cover every segment exactly once")

    args.out.mkdir(parents=True, exist_ok=True)
    list_path = args.out / "concat-list.txt"
    chapters_out = []
    for chapter in source["chapters"]:
        chapter_rows = [row for row in rows if row["chapter"] == chapter["chapter"]]
        if not chapter_rows:
            raise SystemExit(f"no segments for chapter {chapter['chapter']}")
        with list_path.open("w", encoding="utf-8") as handle:
            for row in chapter_rows:
                path = (args.audio / f"page-{row['page']:02d}.wav").resolve()
                handle.write(f"file '{path.as_posix()}'\n")
        target = args.out / f"chapter-{chapter['chapter']:02d}.mp3"
        subprocess.run(
            [
                "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "concat", "-safe", "0", "-i", str(list_path),
                "-ac", "1", "-ar", args.sample_rate, "-codec:a", "libmp3lame",
                "-b:a", args.bitrate, str(target),
            ],
            check=True,
        )
        seconds = duration(target)
        chapters_out.append(
            {
                "number": chapter["chapter"],
                "title": chapter["title"],
                "file": target.name,
                "seconds": round(seconds, 3),
                "bytes": target.stat().st_size,
                "sha256": sha256(target),
                "segments": [row["page"] for row in chapter_rows],
            }
        )
        print(f"chapter-{chapter['chapter']:02d}: {seconds/60:.1f} min", flush=True)
    list_path.unlink(missing_ok=True)

    flagged = 0
    if checks:
        flagged = sum(1 for row in checks["segments"] if row.get("needs_listen"))
    manifest = {
        "schema_version": 1,
        "book_id": args.book_id,
        "title": "The Ledger of Ashes",
        "credit": args.credit,
        "engine": render.get("engine"),
        "voice": args.voice or render.get("voice"),
        "review_status": args.review_status,
        "asr_flagged_segments": flagged if checks else None,
        "total_segments": len(rows),
        "total_seconds": round(sum(c["seconds"] for c in chapters_out), 3),
        "chapters": chapters_out,
    }
    (args.out / "chapters.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"{len(chapters_out)} chapters, {manifest['total_seconds']/3600:.2f} h, "
        f"{manifest['total_seconds']/len(chapters_out)/60:.1f} min mean",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
