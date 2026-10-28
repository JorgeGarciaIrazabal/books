#!/usr/bin/env python3
"""Re-render long Drama 3 segments as two sentence-boundary parts.

A 1400-token request caps at about 65 seconds. A few long segments hit that
cap. This tool splits only those segments at a sentence boundary, renders the
parts in one Drama 3 session, and concatenates them back to the original
page-NN.wav name. The spoken words are unchanged.

It requires the Nell render adapter and the local audio.cpp/Drama 3 runtime.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def words(text: str) -> list[str]:
    return text.split()


def split_parts(text: str, limit: int = 75) -> list[str]:
    text = " ".join(text.split())
    heading = re.match(r"^(Chapter\s+[A-Za-z0-9-]+:\s*[^.!?]+?)\s+(?=[A-Z“\"])", text)
    if heading:
        head = heading.group(1).strip()
        rest = text[heading.end():].strip()
        parts = [head] + split_parts(rest, limit)
        if " ".join(parts) != text:
            raise ValueError("chapter-heading split did not reassemble exactly")
        return parts
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", text) if s]
    if len(words(text)) <= limit or len(sentences) == 1:
        return [text]
    target = len(words(text)) / 2
    best = min(
        range(1, len(sentences)),
        key=lambda i: abs(len(words(" ".join(sentences[:i]))) - target),
    )
    left = " ".join(sentences[:best])
    right = " ".join(sentences[best:])
    parts = []
    for part in (left, right):
        parts.extend(split_parts(part, limit) if len(words(part)) > limit else [part])
    if " ".join(parts) != text:
        raise ValueError("sentence split did not reassemble exactly")
    return parts


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("segments", type=Path)
    p.add_argument("--pages", required=True, help="comma separated original page numbers")
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--work-dir", type=Path, required=True)
    p.add_argument("--adapter", type=Path, required=True)
    p.add_argument("--cli", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--voice-ref", required=True)
    p.add_argument("--ref-text", required=True)
    p.add_argument("--max-tokens", type=int, default=1400)
    p.add_argument("--part-limit", type=int, default=60, help="maximum words per rendered part")
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--threads", type=int, default=24)
    p.add_argument("--context", type=int, default=4096)
    a = p.parse_args()

    source = json.loads(a.segments.read_text(encoding="utf-8"))
    rows = {row["page"]: row for row in source["pages"]}
    wanted = [int(x) for x in a.pages.split(",") if x.strip()]
    if not wanted:
        raise SystemExit("no pages requested")
    a.out_dir.mkdir(parents=True, exist_ok=True)
    a.work_dir.mkdir(parents=True, exist_ok=True)
    record = []

    for page in wanted:
        row = rows.get(page)
        if row is None:
            raise SystemExit(f"page {page} is not in the segment map")
        parts = split_parts(row["text"], a.part_limit)
        batch = []
        for index, part in enumerate(parts, 1):
            batch.append(
                {
                    "page": page * 1000 + index,
                    "chapter": row["chapter"],
                    "segment": row["segment"],
                    "text": part,
                    "words": len(words(part)),
                }
            )
        batch_path = a.work_dir / f"page-{page:03d}-parts.json"
        batch_path.write_text(
            json.dumps({"pages": batch}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        part_dir = a.work_dir / f"page-{page:03d}"
        command = [
            sys.executable,
            str(a.adapter),
            str(batch_path),
            "--out-dir",
            str(part_dir),
            "--cli",
            a.cli,
            "--model",
            a.model,
            "--voice-ref",
            a.voice_ref,
            "--ref-text",
            a.ref_text,
            "--chunk",
            "4000",
            "--max-tokens",
            str(a.max_tokens),
            "--seed",
            str(a.seed),
            "--threads",
            str(a.threads),
            "--session",
            f"fish_drama3.context_length={a.context}",
            "--pages",
            ",".join(str(item["page"]) for item in batch),
        ]
        subprocess.run(command, check=True)
        wavs = [part_dir / f"page-{item['page']:04d}.wav" for item in batch]
        missing = [str(path) for path in wavs if not path.is_file()]
        if missing:
            raise SystemExit(f"missing part audio: {missing}")
        list_path = part_dir / "concat-list.txt"
        with list_path.open("w", encoding="utf-8") as handle:
            for path in wavs:
                handle.write(f"file '{path.resolve().as_posix()}'\n")
        target = a.out_dir / f"page-{page:02d}.wav"
        subprocess.run(
            [
                "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "concat", "-safe", "0", "-i", str(list_path),
                "-c", "copy", str(target),
            ],
            check=True,
        )
        seconds = float(
            subprocess.run(
                [
                    "ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "default=nw=1:nk=1", str(target),
                ],
                capture_output=True,
                text=True,
                check=True,
            ).stdout
        )
        record.append(
            {
                "page": page,
                "parts": [{"text": item["text"], "words": item["words"]} for item in batch],
                "seconds": round(seconds, 3),
                "wav": str(target),
            }
        )
        print(f"page {page}: {len(parts)} parts, {seconds:.2f}s -> {target}", flush=True)

    (a.out_dir / "split-renders.json").write_text(
        json.dumps({"pages": record}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
