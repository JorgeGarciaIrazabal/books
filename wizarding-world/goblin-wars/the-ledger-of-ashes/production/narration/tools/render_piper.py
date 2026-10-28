#!/usr/bin/env python3
"""Render chapter narration segments with Piper.

The script reads the word-exact segment map, loads one Piper voice, and writes
one WAV per segment. It never edits the manuscript or the segment map.

This is a synthetic draft narrator, not an auditioned cast. The output must be
checked with check_segments.py and heard by a person before it is presented as
a finished performance.

Example:
    uv run --with piper-tts python production/narration/tools/render_piper.py \
        production/narration/segments.json \
        --out-dir exports/narration-piper \
        --model /tmp/opencode/piper-voices/en_GB-jenny_dioco-medium.onnx \
        --length-scale 2.0
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import wave
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("segments", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--length-scale", type=float, default=2.0)
    parser.add_argument("--noise-scale", type=float, default=None)
    parser.add_argument("--noise-w-scale", type=float, default=None)
    parser.add_argument("--limit", type=int, default=0, help="render only the first N segments")
    args = parser.parse_args()

    from piper import PiperVoice
    from piper.config import SynthesisConfig

    data = json.loads(args.segments.read_text(encoding="utf-8"))
    rows = data["pages"]
    if args.limit:
        rows = rows[: args.limit]
    args.out_dir.mkdir(parents=True, exist_ok=True)

    voice = PiperVoice.load(args.model, config_path=args.config)
    config = SynthesisConfig(
        length_scale=args.length_scale,
        noise_scale=args.noise_scale,
        noise_w_scale=args.noise_w_scale,
    )
    started = time.time()
    total_seconds = 0.0
    files = []
    for row in rows:
        target = args.out_dir / f"page-{row['page']:02d}.wav"
        with wave.open(str(target), "wb") as wav_file:
            voice.synthesize_wav(row["text"], wav_file, config)
        with wave.open(str(target), "rb") as wav_file:
            seconds = wav_file.getnframes() / wav_file.getframerate()
            rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
        total_seconds += seconds
        files.append(
            {
                "page": row["page"],
                "chapter": row["chapter"],
                "segment": row["segment"],
                "wav": target.name,
                "seconds": round(seconds, 3),
                "bytes": target.stat().st_size,
                "sha256": sha256(target),
            }
        )
        print(f"{row['page']}/{rows[-1]['page']}: {seconds:.1f}s", flush=True)

    record = {
        "schema_version": 1,
        "status": "synthetic draft narration; machine checks required; human listening pending",
        "engine": "Piper",
        "voice": args.model.stem,
        "model": str(args.model),
        "model_sha256": sha256(args.model),
        "config": str(args.config) if args.config else None,
        "length_scale": args.length_scale,
        "sample_rate": rate,
        "channels": channels,
        "segment_count": len(files),
        "audio_seconds": round(total_seconds, 3),
        "wall_seconds": round(time.time() - started, 3),
        "source": str(args.segments),
        "source_sha256": sha256(args.segments),
        "files": files,
    }
    (args.out_dir / "render-piper.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"rendered {len(files)} segments, {total_seconds/3600:.2f} h audio, "
        f"{record['wall_seconds']:.0f}s wall -> {args.out_dir}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
