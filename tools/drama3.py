#!/usr/bin/env python3
"""Shared local Fish Audio Drama 3 TTS workflow tool (audio.cpp Vulkan).

This tool provides the studio-wide Drama 3 narration pipeline for both:
  - fixed-layout page-by-page read-aloud scripts (``production/narration/script.md``),
  - reflowable chapter-based audiobooks (ordered ``book.json.chapters``).

Narration stays strictly in its own layer (``production/narration/``, ``exports/``,
``narration/``, or ``site/audio/<book-id>/``). This script never modifies source
manuscripts, EPUBs, or PDFs.

Subcommands:
  doctor             verify local audiocpp_cli, Drama 3 GGUF, ffmpeg, and ASR setup
  prepare-chapters   split ordered chapter Markdown into word-exact segments JSON
  prepare-pages      validate a tagged script.md against exported pages into JSON
  render             render segments/pages with local audio.cpp + Fish Audio Drama 3
  split-retake       re-render capped/long segments split at sentence boundaries
  check              run duration, WPM, silence, and faster-whisper ASR checks
  assemble-chapters  encode verified segment WAVs into mono chapter MP3s + manifests

Environment overrides (auto-discovered by default on this computer):
  DRAMA3_CLI         path to audiocpp_cli (default: ~/.local/bin/audiocpp_cli)
  DRAMA3_MODEL       path to Drama 3 GGUF (default: ~/.cache/drama3/Drama-3-GGUF/...)
  DRAMA3_BACKEND     audio.cpp backend (default: vulkan)
  DRAMA3_WHISPER_PY  Python interpreter with faster_whisper (default: uv run --with faster-whisper)
"""
from __future__ import annotations

import argparse
import array
import difflib
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import wave
from datetime import date
from pathlib import Path

DEFAULT_CLI_CANDIDATES = [
    Path.home() / ".local/bin/audiocpp_cli",
    Path.home() / ".local/opt/audio.cpp/build-vk/bin/audiocpp_cli",
    Path.home() / "tools/audio.cpp/build-vk/bin/audiocpp_cli",
]

DEFAULT_MODEL_CANDIDATES = [
    Path.home() / ".cache/drama3/Drama-3-GGUF/drama-3-backbone-8bit-experts-Q4_K_S.gguf",
    Path.home() / ".cache/drama3/Drama3-small-GGUF/drama3-small-IQ3_XXS.gguf",
]

DEFAULT_DIRECTION = "[warm, unhurried storyteller voice]"
DEFAULT_CHUNK = 4000
DEFAULT_MAX_TOKENS = 1400
DEFAULT_CONTEXT = 4096
DEFAULT_SEED = 7
DEFAULT_THREADS = 8
DEFAULT_BACKEND = "vulkan"
DEFAULT_SENTENCE_GAP_MS = 500
DEFAULT_PARAGRAPH_GAP_MS = 750
EDGE_SILENCE_THRESHOLD_DB = -40.0
EDGE_FADE_MS = 5
MODEL_LICENSE = "Fish Audio Community License v1.0"

TAG_PATTERNS = [
    re.compile(r"<\|speaker:\d+\|>"),
    re.compile(r"\[[^\]]*\]"),
    re.compile(r"</?(?:whisper|emphasis|soft|fast|slow|stress|forceful)>"),
]
PAGE_RE = re.compile(r"^## Page (\d+)\s*$")
FENCE_RE = re.compile(r"^```(?:text)?\s*$")


class Drama3Error(Exception):
    pass


def fail(msg: str) -> None:
    raise Drama3Error(msg)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def strip_markdown_emphasis(text: str) -> str:
    """Remove inline Markdown styling without adding, dropping, or reordering words."""
    out = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    out = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"\1", out)
    out = re.sub(r"`([^`]+?)`", r"\1", out)
    return out


def strip_narration_tags(text: str) -> str:
    out = text
    for pattern in TAG_PATTERNS:
        out = pattern.sub("", out)
    return normalize_ws(out)


def find_cli(explicit: str | None = None) -> Path | None:
    if explicit:
        p = Path(explicit).expanduser()
        return p if p.is_file() else None
    env = os.environ.get("DRAMA3_CLI")
    if env:
        p = Path(env).expanduser()
        if p.is_file():
            return p
    which = shutil.which("audiocpp_cli")
    if which:
        return Path(which)
    for cand in DEFAULT_CLI_CANDIDATES:
        if cand.is_file():
            return cand
    return None


def find_model(explicit: str | None = None) -> Path | None:
    if explicit:
        p = Path(explicit).expanduser()
        return p if p.is_file() else None
    env = os.environ.get("DRAMA3_MODEL")
    if env:
        p = Path(env).expanduser()
        if p.is_file():
            return p
    for cand in DEFAULT_MODEL_CANDIDATES:
        if cand.is_file():
            return cand
    return None


def detect_engine_commit(cli: Path | None) -> str:
    if not cli:
        return "unknown"
    resolved = cli.resolve()
    for parent in resolved.parents:
        if (parent / ".git").exists():
            res = subprocess.run(
                ["git", "-C", str(parent), "rev-parse", "HEAD"],
                capture_output=True, text=True, check=False,
            )
            if res.returncode == 0:
                return res.stdout.strip()
            break
    return "unknown"


def probe_duration(path: Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        text=True,
    ).strip()
    return round(float(out), 3)


def detect_silences(path: Path, threshold: float) -> list[tuple[float, float]]:
    out = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-i", str(path),
            "-af", f"silencedetect=noise=-40dB:d={threshold}",
            "-f", "null", "-",
        ],
        capture_output=True, text=True, check=False,
    )
    starts = [
        float(line.split("silence_start: ")[1].split()[0])
        for line in out.stderr.splitlines() if "silence_start:" in line
    ]
    lengths = [
        float(line.split("silence_duration: ")[1].split()[0])
        for line in out.stderr.splitlines() if "silence_duration:" in line
    ]
    return list(zip(starts, lengths))


def measure_wav_edge_silence(
    path: Path,
    threshold_db: float = EDGE_SILENCE_THRESHOLD_DB,
    window_ms: int = 10,
) -> tuple[int, int]:
    """Measure leading and trailing near-silence (ms) in a 16-bit PCM WAV."""
    with wave.open(str(path), "rb") as wf:
        nchannels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        nframes = wf.getnframes()
        if sampwidth != 2:
            fail(f"{path}: expected 16-bit PCM WAV, got sampwidth={sampwidth}")
        raw = wf.readframes(nframes)
    if nframes == 0 or framerate <= 0:
        return (0, 0)
    samples = array.array("h")
    samples.frombytes(raw)
    if sys.byteorder != "little":
        samples.byteswap()
    win_frames = max(1, int(round(framerate * window_ms / 1000.0)))
    step = win_frames * nchannels
    threshold = 32768.0 * (10.0 ** (threshold_db / 20.0))
    rms_windows = []
    for i in range(0, len(samples), step):
        chunk = samples[i:i + step]
        if not chunk:
            continue
        rms_windows.append(math.sqrt(sum(s * s for s in chunk) / len(chunk)))
    if not rms_windows:
        return (0, 0)
    total_ms = int(round((nframes / framerate) * 1000.0))
    first_active = next((idx for idx, val in enumerate(rms_windows) if val > threshold), None)
    if first_active is None:
        return (total_ms, total_ms)
    last_active = next(
        len(rms_windows) - 1 - idx
        for idx, val in enumerate(reversed(rms_windows))
        if val > threshold
    )
    lead_ms = first_active * window_ms
    trail_ms = (len(rms_windows) - 1 - last_active) * window_ms
    return (lead_ms, trail_ms)


def _fade_edges_pcm16(
    raw: bytes,
    nchannels: int,
    sample_rate: int,
    fade_in: bool,
    fade_out: bool,
    fade_ms: int = EDGE_FADE_MS,
) -> bytes:
    """Apply short linear ramps to prevent clicks when padding tight WAV cuts."""
    if not (fade_in or fade_out) or not raw:
        return raw
    samples = array.array("h")
    samples.frombytes(raw)
    if sys.byteorder != "little":
        samples.byteswap()
    total_frames = len(samples) // nchannels
    fade_frames = min(int(round(sample_rate * fade_ms / 1000.0)), total_frames // 2)
    if fade_frames <= 0:
        return raw
    if fade_in:
        for f in range(fade_frames):
            scale = f / fade_frames
            base = f * nchannels
            for c in range(nchannels):
                samples[base + c] = int(round(samples[base + c] * scale))
    if fade_out:
        start = total_frames - fade_frames
        for offset in range(fade_frames):
            scale = (fade_frames - 1 - offset) / fade_frames
            base = (start + offset) * nchannels
            for c in range(nchannels):
                samples[base + c] = int(round(samples[base + c] * scale))
    if sys.byteorder != "little":
        samples.byteswap()
    return samples.tobytes()


def concat_wavs_with_gaps(
    wavs: list[Path],
    target_gaps_ms: list[int],
    out_wav: Path,
    threshold_db: float = EDGE_SILENCE_THRESHOLD_DB,
) -> dict:
    """Concatenate 16-bit PCM WAVs while ensuring minimum silence at joins."""
    if not wavs:
        fail("concat_wavs_with_gaps requires at least one WAV")
    if len(target_gaps_ms) != len(wavs) - 1:
        fail(
            f"target_gaps_ms length ({len(target_gaps_ms)}) must equal len(wavs) - 1 ({len(wavs) - 1})"
        )
    params: tuple[int, int, int, str] | None = None
    edges: list[tuple[int, int]] = []
    for w in wavs:
        with wave.open(str(w), "rb") as wf:
            cur = (wf.getnchannels(), wf.getsampwidth(), wf.getframerate(), wf.getcomptype())
        if cur[1] != 2 or cur[3] != "NONE":
            fail(f"{w}: expected uncompressed 16-bit PCM WAV, got width={cur[1]} comp={cur[3]}")
        if params is None:
            params = cur
        elif cur != params:
            fail(f"{w}: WAV format {cur} differs from {params}")
        edges.append(measure_wav_edge_silence(w, threshold_db=threshold_db))

    assert params is not None
    nchannels, sampwidth, framerate, _ = params
    frame_bytes = nchannels * sampwidth

    pad_plan: list[int] = []
    raw_gaps: list[int] = []
    final_gaps: list[int] = []
    for idx, target in enumerate(target_gaps_ms):
        raw_gap = edges[idx][1] + edges[idx + 1][0]
        target_ms = max(0, int(target))
        pad_ms = max(0, target_ms - raw_gap)
        pad_plan.append(pad_ms)
        raw_gaps.append(raw_gap)
        final_gaps.append(raw_gap + pad_ms)

    out_wav.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_wav), "wb") as out_wf:
        out_wf.setnchannels(nchannels)
        out_wf.setsampwidth(sampwidth)
        out_wf.setframerate(framerate)
        for idx, w in enumerate(wavs):
            with wave.open(str(w), "rb") as in_wf:
                raw = in_wf.readframes(in_wf.getnframes())
            need_fade_in = idx > 0 and pad_plan[idx - 1] > 0 and edges[idx][0] < 15
            need_fade_out = idx < len(wavs) - 1 and pad_plan[idx] > 0 and edges[idx][1] < 15
            if need_fade_in or need_fade_out:
                raw = _fade_edges_pcm16(raw, nchannels, framerate, need_fade_in, need_fade_out)
            out_wf.writeframes(raw)
            if idx < len(wavs) - 1 and pad_plan[idx] > 0:
                silence_frames = int(round(pad_plan[idx] * framerate / 1000.0))
                if silence_frames > 0:
                    out_wf.writeframes(b"\x00" * (silence_frames * frame_bytes))

    return {
        "joins": len(target_gaps_ms),
        "padded_joins": sum(1 for p in pad_plan if p > 0),
        "min_raw_gap_ms": min(raw_gaps) if raw_gaps else None,
        "min_final_gap_ms": min(final_gaps) if final_gaps else None,
        "total_added_ms": sum(pad_plan),
    }


def page_wav_name(page: int) -> str:
    return f"page-{page:02d}.wav"


def clock_fmt(seconds: float) -> str:
    total = int(round(seconds))
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours} h {minutes:02d} min"
    return f"{minutes}:{secs:02d}"


# ---------------------------------------------------------------------------
# doctor
# ---------------------------------------------------------------------------

def cmd_doctor(args: argparse.Namespace) -> int:
    cli = find_cli(args.cli)
    model = find_model(args.model)
    commit = detect_engine_commit(cli)
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    uv = shutil.which("uv")
    default_ref = Path.home() / ".cache/drama3/cast/narrator.wav"

    print(f"audiocpp_cli : {cli if cli else 'MISSING'}")
    if cli:
        print(f"audio.cpp git: {commit[:12] if commit != 'unknown' else 'unknown'}")
    print(f"drama3 model : {model if model else 'MISSING'}")
    if model:
        gb = model.stat().st_size / (1024 ** 3)
        print(f"model size   : {gb:.2f} GiB")
    print(f"ffmpeg       : {ffmpeg or 'MISSING'}")
    print(f"ffprobe      : {ffprobe or 'MISSING'}")
    print(f"uv           : {uv or 'not installed'}")
    print(f"default ref  : {default_ref if default_ref.is_file() else 'not cached'}")

    ok = bool(cli and model and ffmpeg and ffprobe)
    if not ok:
        print(
            "\nMissing required local Drama 3 dependency. "
            "See docs/narration.md for building audio.cpp with Vulkan into ~/.local/opt/audio.cpp.",
            file=sys.stderr,
        )
        return 1
    print("\nDrama 3 local TTS toolchain is ready.")
    return 0


# ---------------------------------------------------------------------------
# prepare-chapters
# ---------------------------------------------------------------------------

SENTENCE_SPLIT_RE = re.compile(
    r'(?:(?<=[.!?])|(?<=[.!?]["”\']))\s+(?=[A-Z0-9"“\'¿¡])'
)


def _flush_segment(items: list[tuple[int, str, bool]]) -> dict:
    groups: list[list[str]] = []
    prev_para: int | None = None
    for para_idx, text, _ in items:
        if prev_para is None or para_idx != prev_para:
            groups.append([text])
            prev_para = para_idx
        else:
            groups[-1].append(text)
    seg_text = "\n\n".join(" ".join(group) for group in groups)
    return {"text": seg_text, "ends_paragraph": items[-1][2]}


def split_chapter_markdown(path: Path, max_words: int, keep_markdown: bool = False) -> tuple[str, str, str, list[dict]]:
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    if not lines or not lines[0].startswith("# "):
        fail(f"{path}: expected '# ' chapter heading on line 1")
    title = lines[0][2:].strip()
    body_raw = "\n".join(lines[1:]).strip()
    body = body_raw if keep_markdown else strip_markdown_emphasis(body_raw)

    # Keep paragraph structure; split paragraphs into sentences without losing words.
    paragraphs = [normalize_ws(p) for p in re.split(r"\n\s*\n", body) if p.strip()]
    units: list[tuple[int, str, bool]] = [(0, title, True)]
    para_word_counts: dict[int, int] = {0: len(title.split())}
    for p_idx, para in enumerate(paragraphs, 1):
        para_word_counts[p_idx] = len(para.split())
        sentences = [s.strip() for s in SENTENCE_SPLIT_RE.split(para) if s.strip()]
        for s_idx, sent in enumerate(sentences):
            units.append((p_idx, sent, s_idx == len(sentences) - 1))

    spoken_full = normalize_ws(title + " " + " ".join(paragraphs))

    segments: list[dict] = []
    current: list[tuple[int, str, bool]] = []
    for idx, (para_idx, unit_text, is_para_end) in enumerate(units):
        w = unit_text.split()
        # Keep the chapter heading attached to the opening sentence(s) with a
        # paragraph break so Drama 3 pauses naturally after the chapter title.
        if idx == 0:
            current.append((para_idx, unit_text, is_para_end))
            continue
        cur_words = sum(len(part[1].split()) for part in current)
        if (
            current
            and para_idx != current[-1][0]
            and current[-1][0] != 0
            and cur_words >= int(max_words * 0.65)
            and cur_words + para_word_counts[para_idx] > max_words
        ):
            segments.append(_flush_segment(current))
            current = []
            cur_words = 0
        if current and cur_words + len(w) > max_words:
            segments.append(_flush_segment(current))
            current = []
        while len(w) > max_words:
            segments.append({"text": " ".join(w[:max_words]), "ends_paragraph": False})
            w = w[max_words:]
        if w:
            current.append((para_idx, " ".join(w), is_para_end))
    if current:
        segments.append(_flush_segment(current))

    if normalize_ws(" ".join(seg["text"] for seg in segments)) != spoken_full:
        fail(f"{path}: segment reassembly mismatch against chapter text")
    return raw, title, spoken_full, segments


def cmd_prepare_chapters(args: argparse.Namespace) -> int:
    book_dir = Path(args.book).resolve()
    book_json = book_dir / "book.json"
    if not book_json.is_file():
        fail(f"missing {book_json}")
    meta = json.loads(book_json.read_text(encoding="utf-8"))
    chapters = meta.get("chapters") or []
    if not chapters or len(chapters) != len(set(chapters)):
        fail(f"{book_json}: chapters list is empty or contains duplicates")

    chapter_meta = []
    rows = []
    for ch_num, rel in enumerate(chapters, 1):
        ch_path = book_dir / rel
        if not ch_path.is_file():
            fail(f"missing chapter {ch_path}")
        raw, title, spoken, segments = split_chapter_markdown(
            ch_path, args.max_words, keep_markdown=args.keep_markdown
        )
        chapter_meta.append({
            "chapter": ch_num,
            "path": rel,
            "title": title,
            "source_sha256": sha256_text(raw),
            "spoken_sha256": sha256_text(spoken),
            "words": len(spoken.split()),
            "segments": len(segments),
        })
        for seg_idx, seg in enumerate(segments, 1):
            seg_text = seg["text"]
            rows.append({
                "page": len(rows) + 1,
                "chapter": ch_num,
                "segment": seg_idx,
                "text": seg_text,
                "ends_paragraph": seg["ends_paragraph"],
                "words": len(seg_text.split()),
                "text_sha256": sha256_text(seg_text),
            })

    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "kind": "chapter_segments",
        "book_id": meta.get("id", book_dir.name),
        "title": meta.get("title", book_dir.name),
        "max_words": args.max_words,
        "chapters": chapter_meta,
        "pages": rows,
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.script:
        script_path = Path(args.script).resolve()
        script_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            f"# Narration script — {payload['title']}",
            "",
            "Separate read-aloud layer. Never feeds the manuscript, EPUB, or PDF.",
        ]
        direction = f" {args.direction}" if args.direction else ""
        for row in rows:
            lines.extend([
                "",
                f"## Chapter {row['chapter']} · Segment {row['segment']} (Unit {row['page']:02d})",
                "",
                "```text",
                f"<|speaker:0|>{direction} {row['text']}",
                "```",
            ])
        script_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Wrote script: {script_path}")

    print(
        f"{len(chapter_meta)} chapters, {len(rows)} segments "
        f"({sum(r['words'] for r in rows)} words), exact reassembly verified -> {out_path}"
    )
    return 0


# ---------------------------------------------------------------------------
# prepare-pages (fixed-layout script.md -> pages.json)
# ---------------------------------------------------------------------------

def parse_export_pages(markdown: str) -> dict[int, str]:
    pages: dict[int, str] = {}
    current: int | None = None
    body: list[str] = []
    for line in markdown.splitlines():
        m = PAGE_RE.match(line)
        if m:
            if current is not None:
                pages[current] = "\n\n".join(p for p in body if p).strip()
            current = int(m.group(1))
            body = []
        elif line.startswith("#"):
            if current is not None:
                pages[current] = "\n\n".join(p for p in body if p).strip()
            current = None
            body = []
        elif current is not None:
            body.append(line.strip())
    if current is not None:
        pages[current] = "\n\n".join(p for p in body if p).strip()
    return pages


def parse_script_pages(markdown: str) -> dict[int, str]:
    pages: dict[int, str] = {}
    lines = markdown.splitlines()
    i = 0
    while i < len(lines):
        m = PAGE_RE.match(lines[i])
        i += 1
        if not m:
            continue
        while i < len(lines) and not FENCE_RE.match(lines[i]):
            i += 1
        i += 1
        body: list[str] = []
        while i < len(lines) and not FENCE_RE.match(lines[i]):
            body.append(lines[i])
            i += 1
        pages[int(m.group(1))] = "\n".join(body).strip()
    return pages


def cmd_prepare_pages(args: argparse.Namespace) -> int:
    script_path = Path(args.script).resolve()
    source_path = Path(args.source).resolve()
    out_path = Path(args.out).resolve()

    tagged = parse_script_pages(script_path.read_text(encoding="utf-8"))
    raw_source = source_path.read_text(encoding="utf-8")
    if source_path.suffix == ".json":
        plain = {p["page"]: p["text"] for p in json.loads(raw_source)["pages"]}
    else:
        plain = parse_export_pages(raw_source)

    if not tagged:
        fail(f"{script_path}: no '## Page N' blocks found")

    problems = []
    for num, text in sorted(tagged.items()):
        if num not in plain:
            problems.append((num, "missing in source", ""))
            continue
        got = strip_narration_tags(text)
        want = normalize_ws(plain[num])
        if got != want:
            problems.append((num, got, want))
    if problems:
        lines = []
        for num, got, want in problems[:5]:
            lines.append(f"page {num} differs after tag removal")
            for left, right in zip(got.split(), want.split()):
                if left != right:
                    lines.append(f"  first diff: {left!r} != {right!r}")
                    break
        fail("\n".join(lines))

    data = {
        "schema_version": 1,
        "kind": "fixed_pages",
        "source": str(script_path),
        "tagged": True,
        "pages": [
            {
                "page": num,
                "text": text,
                "words": len(strip_narration_tags(text).split()),
                "text_sha256": sha256_text(strip_narration_tags(text)),
            }
            for num, text in sorted(tagged.items())
        ],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(tagged)} tagged pages verified identical -> {out_path}")
    return 0


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------

def resolve_cast_options(args: argparse.Namespace) -> tuple[list[str], dict]:
    """Build audiocpp_cli voice reference flags and provenance summary."""
    if args.cast:
        cast_path = Path(args.cast).resolve()
        cast_data = json.loads(cast_path.read_text(encoding="utf-8"))
        voices = cast_data["voices"] if isinstance(cast_data, dict) else cast_data
        if not voices:
            fail(f"{cast_path}: cast has no voices")
        # Single-voice cast without speaker tags uses --voice-ref; multi-voice or tagged uses references JSON.
        if len(voices) == 1 and not args.multi_speaker:
            v = voices[0]
            ref_rel = v.get("audio_path") or v.get("reference")
            ref_text = v.get("text") or v.get("reference_text")
            if not ref_rel or not ref_text:
                fail(f"{cast_path}: voice 0 requires reference path and reference_text")
            ref_path = Path(ref_rel)
            if not ref_path.is_absolute():
                ref_path = (cast_path.parent / ref_path).resolve()
            if not ref_path.is_file():
                fail(f"missing reference audio: {ref_path}")
            return (
                ["--voice-ref", str(ref_path), "--request-option", f"reference_text={ref_text}"],
                {"mode": "single_voice", "cast": str(cast_path), "voice": v.get("voice", "narrator"),
                 "reference": str(ref_path), "reference_sha256": sha256_file(ref_path)},
            )
        descriptors = []
        seen_texts = set()
        for idx, v in enumerate(voices):
            ref_rel = v.get("audio_path") or v.get("reference")
            ref_text = v.get("text") or v.get("reference_text")
            if not ref_rel or not ref_text:
                fail(f"{cast_path}: voice {idx} needs reference path and transcript")
            if ref_text in seen_texts:
                fail(f"{cast_path}: duplicate reference_text at voice {idx}; Drama 3 requires distinct sentences")
            seen_texts.add(ref_text)
            ref_path = Path(ref_rel)
            if not ref_path.is_absolute():
                ref_path = (cast_path.parent / ref_path).resolve()
            if not ref_path.is_file():
                fail(f"missing reference audio: {ref_path}")
            descriptors.append({"text": f"<|speaker:{idx}|> {ref_text}", "audio_path": str(ref_path)})
        return (
            ["--request-option", "references=" + json.dumps(descriptors, ensure_ascii=False)],
            {"mode": "multi_speaker", "cast": str(cast_path), "voices": len(descriptors)},
        )

    if not args.voice_ref or not args.ref_text:
        fail("pass either --cast CAST_JSON or both --voice-ref and --ref-text")
    ref_path = Path(args.voice_ref).expanduser().resolve()
    if not ref_path.is_file():
        fail(f"missing --voice-ref: {ref_path}")
    return (
        ["--voice-ref", str(ref_path), "--request-option", f"reference_text={args.ref_text}"],
        {"mode": "single_voice", "reference": str(ref_path), "reference_sha256": sha256_file(ref_path)},
    )


def run_audiocpp_batch(
    cli: Path,
    model: Path,
    backend: str,
    batch_dir: Path,
    out_dir: Path,
    manifest_path: Path,
    voice_flags: list[str],
    chunk: int,
    max_tokens: int,
    context: int,
    seed: int,
    threads: int,
    extra_sessions: list[str],
) -> tuple[int, float, list[str], str, str]:
    cmd = [
        str(cli),
        "--task", "tts",
        "--family", "fish_drama3",
        "--backend", backend,
        "--mode", "offline",
        "--model", str(model),
        "--request-option", f"text_chunk_size={chunk}",
        "--session-option", f"fish_drama3.context_length={context}",
        "--batch-text-dir", str(batch_dir),
        "--batch-manifest-out", str(manifest_path),
        "--max-tokens", str(max_tokens),
        "--seed", str(seed),
        "--threads", str(threads),
        "--metrics",
    ]
    for opt in extra_sessions:
        cmd.extend(["--session-option", opt])
    cmd.extend(voice_flags)
    cmd.extend(["--out-dir", str(out_dir)])

    started = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - started
    return proc.returncode, elapsed, cmd, proc.stdout, proc.stderr


def load_or_init_summary(out_dir: Path, base: dict) -> dict:
    summary_path = out_dir / "render-summary.json"
    if summary_path.is_file():
        existing = json.loads(summary_path.read_text(encoding="utf-8"))
        existing["engine"] = base["engine"]
        existing["settings"] = base["settings"]
        return existing
    return {**base, "files": {}}


def cmd_render(args: argparse.Namespace) -> int:
    cli = find_cli(args.cli)
    if not cli:
        fail("audiocpp_cli not found; run `python3 tools/drama3.py doctor`")
    model = find_model(args.model)
    if not model:
        fail("Drama 3 GGUF model not found; run `python3 tools/drama3.py doctor`")

    data = json.loads(Path(args.pages_json).read_text(encoding="utf-8"))
    all_pages = data["pages"]
    wanted: set[int] | None = None
    if args.pages:
        wanted = {int(p.strip()) for p in args.pages.split(",") if p.strip()}
    selected = [
        p for p in all_pages
        if (wanted is None or p["page"] in wanted)
        and p["page"] >= args.start
        and (args.end == 0 or p["page"] <= args.end)
    ]
    if not selected:
        fail("no pages/segments selected to render")

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    voice_flags, voice_meta = resolve_cast_options(args)

    if args.resume:
        todo = [p for p in selected if not (out_dir / page_wav_name(p["page"])).is_file()]
    else:
        todo = list(selected)

    commit = detect_engine_commit(cli)
    model_sha = args.model_sha256 or sha256_file(model)
    summary = load_or_init_summary(
        out_dir,
        {
            "schema_version": 1,
            "generated": str(date.today()),
            "engine": {
                "name": "audio.cpp",
                "commit": commit,
                "cli": str(cli),
                "backend": args.backend,
                "model": model.name,
                "model_sha256": model_sha,
                "model_license": MODEL_LICENSE,
            },
            "voice": voice_meta,
            "settings": {
                "seed": args.seed,
                "text_chunk_size": args.chunk,
                "max_tokens": args.max_tokens,
                "context_length": args.context,
                "threads": args.threads,
                "direction": None if args.no_direction else args.direction,
            },
        },
    )

    if not todo:
        print(f"All {len(selected)} requested segments already exist in {out_dir}.")
        return 0

    batch_size = max(1, args.batch_size)
    batches = [todo[i:i + batch_size] for i in range(0, len(todo), batch_size)]
    total_wall = 0.0
    capped_pages: list[int] = []

    for b_idx, batch in enumerate(batches, 1):
        b_dir = out_dir / f"batch-{b_idx:02d}"
        req_dir = b_dir / "requests"
        if req_dir.exists():
            shutil.rmtree(req_dir)
        req_dir.mkdir(parents=True, exist_ok=True)

        for item in batch:
            text = item["text"]
            if not args.no_direction and args.direction and not text.lstrip().startswith(("<|speaker:", "[")):
                text = f"{args.direction} {text}"
            (req_dir / f"page-{item['page']:02d}.txt").write_text(text + "\n", encoding="utf-8")

        manifest_path = b_dir / "batch-manifest.json"
        print(
            f"Batch {b_idx}/{len(batches)}: rendering {len(batch)} unit(s) "
            f"(pages {batch[0]['page']}..{batch[-1]['page']}, seed={args.seed})...",
            flush=True,
        )
        rc, elapsed, cmd, stdout, stderr = run_audiocpp_batch(
            cli=cli,
            model=model,
            backend=args.backend,
            batch_dir=req_dir,
            out_dir=out_dir,
            manifest_path=manifest_path,
            voice_flags=voice_flags,
            chunk=args.chunk,
            max_tokens=args.max_tokens,
            context=args.context,
            seed=args.seed,
            threads=args.threads,
            extra_sessions=args.session,
        )
        total_wall += elapsed
        (b_dir / "render.log").write_text(stdout + "\n--- stderr ---\n" + stderr, encoding="utf-8")
        (b_dir / "command.json").write_text(
            json.dumps({"argv": cmd, "returncode": rc, "wall_seconds": round(elapsed, 2)}, indent=2) + "\n",
            encoding="utf-8",
        )
        if rc != 0:
            fail(f"audiocpp_cli failed in batch {b_idx} (rc={rc}):\n{stderr[-2000:]}")

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for req in manifest.get("requests", []):
            num = int(str(req["id"]).split("-")[-1])
            wav = out_dir / page_wav_name(num)
            if not wav.is_file():
                fail(f"expected rendered WAV missing: {wav}")
            sr = req.get("sample_rate") or 44100
            samples = req.get("samples") or 0
            secs = round(samples / sr, 3) if samples else probe_duration(wav)
            custom = (req.get("custom_schema_output") or {}).get("data") or {}
            frames = custom.get("frames")
            wall_s = round(custom.get("wall_ms", 0) / 1000.0, 2) if "wall_ms" in custom else None
            capped = bool(frames is not None and frames >= args.max_tokens - 2)
            if capped:
                capped_pages.append(num)
            summary["files"][str(num)] = {
                "page": num,
                "file": wav.name,
                "seconds": secs,
                "frames": frames,
                "wall_seconds": wall_s,
                "seed": args.seed,
                "capped": capped,
                "sha256": sha256_file(wav),
            }
        (out_dir / "render-summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"  Batch {b_idx} finished in {elapsed:.1f}s.", flush=True)

    print(f"Rendered {len(todo)} unit(s) in {total_wall:.1f}s -> {out_dir}")
    if capped_pages:
        print(
            f"WARNING: {len(capped_pages)} unit(s) hit max_tokens ({args.max_tokens}): {sorted(capped_pages)}. "
            "Re-render with `python3 tools/drama3.py split-retake`.",
            flush=True,
        )
    return 0


# ---------------------------------------------------------------------------
# split-retake (for segments that hit max_tokens)
# ---------------------------------------------------------------------------

def split_into_parts(text: str, part_limit: int) -> list[str]:
    text = normalize_ws(text)
    sentences = [s.strip() for s in SENTENCE_SPLIT_RE.split(text) if s.strip()]
    if len(text.split()) <= part_limit or len(sentences) <= 1:
        return [text]
    target = len(text.split()) / 2
    best = min(
        range(1, len(sentences)),
        key=lambda idx: abs(len(" ".join(sentences[:idx]).split()) - target),
    )
    left = " ".join(sentences[:best])
    right = " ".join(sentences[best:])
    parts: list[str] = []
    for side in (left, right):
        parts.extend(split_into_parts(side, part_limit) if len(side.split()) > part_limit else [side])
    if normalize_ws(" ".join(parts)) != text:
        fail("split_into_parts did not reassemble exact text")
    return parts


def cmd_split_retake(args: argparse.Namespace) -> int:
    cli = find_cli(args.cli)
    model = find_model(args.model)
    if not cli or not model:
        fail("audiocpp_cli or Drama 3 model missing; run `doctor`")

    data = json.loads(Path(args.pages_json).read_text(encoding="utf-8"))
    by_page = {r["page"]: r for r in data["pages"]}
    wanted = [int(x.strip()) for x in args.pages.split(",") if x.strip()]
    if not wanted:
        fail("no pages specified")

    out_dir = Path(args.out_dir).resolve()
    work_dir = out_dir / "split-retakes"
    work_dir.mkdir(parents=True, exist_ok=True)
    voice_flags, _ = resolve_cast_options(args)

    summary_path = out_dir / "render-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.is_file() else {"files": {}}

    # Prepare all split sub-requests in one Drama 3 session so the model loads only once.
    req_dir = work_dir / f"requests-seed-{args.seed}"
    if req_dir.exists():
        shutil.rmtree(req_dir)
    req_dir.mkdir(parents=True, exist_ok=True)

    plan: dict[int, list[tuple[int, str]]] = {}
    for page in wanted:
        row = by_page.get(page)
        if not row:
            fail(f"page {page} not in {args.pages_json}")
        parts = split_into_parts(row["text"], args.part_limit)
        plan[page] = []
        for idx, part in enumerate(parts, 1):
            sub_id = page * 100 + idx
            text = part
            if not args.no_direction and args.direction and not text.lstrip().startswith(("<|speaker:", "[")):
                text = f"{args.direction} {text}"
            (req_dir / f"page-{sub_id:04d}.txt").write_text(text + "\n", encoding="utf-8")
            plan[page].append((sub_id, part))

    sub_out = work_dir / f"wavs-seed-{args.seed}"
    sub_out.mkdir(parents=True, exist_ok=True)
    manifest_path = sub_out / "batch-manifest.json"
    rc, elapsed, _, stdout, stderr = run_audiocpp_batch(
        cli=cli,
        model=model,
        backend=args.backend,
        batch_dir=req_dir,
        out_dir=sub_out,
        manifest_path=manifest_path,
        voice_flags=voice_flags,
        chunk=args.chunk,
        max_tokens=args.max_tokens,
        context=args.context,
        seed=args.seed,
        threads=args.threads,
        extra_sessions=args.session,
    )
    (sub_out / "render.log").write_text(stdout + "\n--- stderr ---\n" + stderr, encoding="utf-8")
    if rc != 0:
        fail(f"split-retake failed (rc={rc}):\n{stderr[-2000:]}")

    for page, sub_items in plan.items():
        wavs = [sub_out / f"page-{sub_id:04d}.wav" for sub_id, _ in sub_items]
        for w in wavs:
            if not w.is_file():
                fail(f"missing split wav {w}")
        target = out_dir / page_wav_name(page)
        join_stats = concat_wavs_with_gaps(
            wavs, [args.sentence_gap_ms] * (len(wavs) - 1), target
        )
        secs = probe_duration(target)
        summary.setdefault("files", {})[str(page)] = {
            "page": page,
            "file": target.name,
            "seconds": secs,
            "seed": args.seed,
            "split_parts": len(sub_items),
            "join_stats": join_stats,
            "capped": False,
            "sha256": sha256_file(target),
        }
        print(f"split-retake page {page:02d}: {len(sub_items)} parts, {secs:.2f}s -> {target}")

    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Completed split-retake for {len(wanted)} unit(s) in {elapsed:.1f}s.")
    return 0


# ---------------------------------------------------------------------------
# check (duration, WPM, silence, faster-whisper ASR diff)
# ---------------------------------------------------------------------------

WHISPER_RUNNER = r"""
import json, subprocess, sys
import numpy as np
from faster_whisper import WhisperModel
model_name = sys.argv[1]
threads = int(sys.argv[2])
beam = int(sys.argv[3])
model = WhisperModel(model_name, device="cpu", compute_type="int8", cpu_threads=threads)
out = {}
for path in sys.argv[4:]:
    raw = subprocess.check_output(
        ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
         "-i", path, "-ar", "16000", "-ac", "1", "-f", "f32le", "-"]
    )
    audio = np.frombuffer(raw, dtype=np.float32)
    segs, _ = model.transcribe(audio, beam_size=beam)
    out[path] = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in segs]
print(json.dumps(out, ensure_ascii=False))
"""


def norm_words(text: str) -> list[str]:
    clean = strip_narration_tags(text)
    return re.findall(r"[a-z0-9]+(?:['’][a-z0-9]+)?", clean.lower().replace("’", "'"))


def run_whisper(wavs: list[Path], model: str, threads: int, beam: int, whisper_py: str | None) -> dict[str, list[dict]]:
    if whisper_py:
        cmd = [whisper_py, "-c", WHISPER_RUNNER, model, str(threads), str(beam), *map(str, wavs)]
    else:
        env_py = os.environ.get("DRAMA3_WHISPER_PY")
        if env_py:
            cmd = [env_py, "-c", WHISPER_RUNNER, model, str(threads), str(beam), *map(str, wavs)]
        else:
            # Prefer current python if faster_whisper is installed; otherwise uv run --with faster-whisper
            try:
                import faster_whisper  # noqa: F401
                cmd = [sys.executable, "-c", WHISPER_RUNNER, model, str(threads), str(beam), *map(str, wavs)]
            except ImportError:
                uv = shutil.which("uv")
                if not uv:
                    fail("faster_whisper not installed and `uv` not found; pass --whisper-python")
                cmd = [uv, "run", "--quiet", "--with", "faster-whisper", "python", "-c",
                       WHISPER_RUNNER, model, str(threads), str(beam), *map(str, wavs)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        fail(f"faster-whisper check failed:\n{proc.stderr[-2000:]}")
    return json.loads(proc.stdout)


def cmd_check(args: argparse.Namespace) -> int:
    data = json.loads(Path(args.pages_json).read_text(encoding="utf-8"))
    wav_dir = Path(args.wav_dir).resolve()
    wanted = {int(x.strip()) for x in args.pages.split(",") if x.strip()} if args.pages else None
    rows_in = [
        r for r in data["pages"]
        if (wanted is None or r["page"] in wanted)
        and r["page"] >= args.start
        and (args.end == 0 or r["page"] <= args.end)
    ]
    if not rows_in:
        fail("no units selected for check")

    wavs = []
    for r in rows_in:
        wav = wav_dir / page_wav_name(r["page"])
        if not wav.is_file():
            fail(f"missing rendered audio {wav}")
        wavs.append(wav)

    transcripts = run_whisper(wavs, args.whisper_model, args.threads, args.beam_size, args.whisper_python)
    low_wpm, high_wpm = (float(v) for v in args.wpm_range.split(","))

    summary_path = wav_dir / "render-summary.json"
    summary_files = {}
    if summary_path.is_file():
        summary_files = json.loads(summary_path.read_text(encoding="utf-8")).get("files", {})

    results = []
    flagged = 0
    for r, wav in zip(rows_in, wavs):
        secs = probe_duration(wav)
        expected_tokens = norm_words(r["text"])
        heard_text = " ".join(seg["text"] for seg in transcripts.get(str(wav), []))
        heard_tokens = norm_words(heard_text)

        matcher = difflib.SequenceMatcher(None, expected_tokens, heard_tokens, autojunk=False)
        ratio = round(matcher.ratio(), 4)
        diffs = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != "equal":
                diffs.append({
                    "kind": tag,
                    "expected": expected_tokens[i1:i2],
                    "transcribed": heard_tokens[j1:j2],
                })

        gaps = detect_silences(wav, args.pause_threshold)
        longest_pause = max((length for _, length in gaps), default=0.0)
        lead_ms, trail_ms = measure_wav_edge_silence(wav)
        wpm = round((len(expected_tokens) / secs) * 60.0, 1) if secs > 0 else 0.0
        capped = bool(summary_files.get(str(r["page"]), {}).get("capped", False))

        reasons = []
        if capped:
            reasons.append("hit_max_tokens")
        if wpm < low_wpm or wpm > high_wpm:
            reasons.append(f"wpm={wpm}")
        if longest_pause > args.pause_limit:
            reasons.append(f"pause={longest_pause:.1f}s")
        if ratio < args.min_similarity:
            reasons.append(f"sim={ratio:.2f}")

        is_flagged = bool(reasons)
        flagged += int(is_flagged)
        results.append({
            "page": r["page"],
            "chapter": r.get("chapter"),
            "segment": r.get("segment"),
            "seconds": secs,
            "words": len(expected_tokens),
            "wpm": wpm,
            "similarity": ratio,
            "lead_ms": lead_ms,
            "trail_ms": trail_ms,
            "longest_pause_s": round(longest_pause, 2),
            "pauses": [[round(s, 2), round(d, 2)] for s, d in gaps],
            "capped": capped,
            "transcript": heard_text,
            "differences": diffs,
            "reasons": reasons,
            "flag": is_flagged,
        })
        marker = f"  <-- {', '.join(reasons)}" if is_flagged else ""
        print(
            f"u{r['page']:02d} {secs:6.1f}s {wpm:5.1f}wpm sim={ratio:.3f} "
            f"pause={longest_pause:4.1f}s diffs={len(diffs):2d}{marker}",
            flush=True,
        )

    out_path = Path(args.out).resolve() if args.out else (wav_dir / "checks.json")
    report = {
        "schema_version": 1,
        "whisper_model": args.whisper_model,
        "units_checked": len(results),
        "flagged": flagged,
        "total_seconds": round(sum(x["seconds"] for x in results), 2),
        "mean_wpm": round(sum(x["wpm"] for x in results) / len(results), 1),
        "segments": results,
    }
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"\n{len(results)} units checked, {report['total_seconds']/60:.1f} min audio, "
        f"mean {report['mean_wpm']} wpm, {flagged} flagged -> {out_path}"
    )
    return 0


# ---------------------------------------------------------------------------
# assemble-chapters (reflowable chapter audiobook MP3s + manifests)
# ---------------------------------------------------------------------------

def cmd_assemble_chapters(args: argparse.Namespace) -> int:
    segments_path = Path(args.segments).resolve()
    audio_dir = Path(args.audio).resolve()
    out_dir = Path(args.out).resolve()

    source = json.loads(segments_path.read_text(encoding="utf-8"))
    if source.get("kind") != "chapter_segments":
        fail(f"{segments_path}: expected kind='chapter_segments'")

    summary_path = audio_dir / "render-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.is_file() else {}
    summary_files = summary.get("files", {})

    rows = source["pages"]
    for row in rows:
        wav = audio_dir / page_wav_name(row["page"])
        if not wav.is_file():
            fail(f"missing rendered segment WAV: {wav}")
        recorded = summary_files.get(str(row["page"]))
        if recorded and recorded.get("sha256") and sha256_file(wav) != recorded["sha256"]:
            fail(f"WAV hash mismatch against render-summary.json: {wav}")

    out_dir.mkdir(parents=True, exist_ok=True)
    chapters_out = []

    with tempfile.TemporaryDirectory(prefix="drama3-asm-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        for ch in source["chapters"]:
            ch_rows = [r for r in rows if r["chapter"] == ch["chapter"]]
            if not ch_rows:
                fail(f"chapter {ch['chapter']} has no segments")
            wavs = [audio_dir / page_wav_name(r["page"]) for r in ch_rows]
            target_gaps = [
                args.paragraph_gap_ms if r.get("ends_paragraph") else args.sentence_gap_ms
                for r in ch_rows[:-1]
            ]
            combined_wav = tmp_path / f"chapter-{ch['chapter']:02d}.wav"
            join_stats = concat_wavs_with_gaps(wavs, target_gaps, combined_wav)
            target = out_dir / f"chapter-{ch['chapter']:02d}.mp3"
            cmd = [
                "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                "-i", str(combined_wav),
                "-ac", "1", "-ar", str(args.sample_rate),
                "-codec:a", "libmp3lame", "-b:a", args.bitrate,
                "-map_metadata", "-1",
                str(target),
            ]
            subprocess.run(cmd, check=True)
            secs = probe_duration(target)
            chapters_out.append({
                "number": ch["chapter"],
                "title": ch["title"],
                "file": target.name,
                "seconds": secs,
                "bytes": target.stat().st_size,
                "sha256": sha256_file(target),
                "source": ch["path"],
                "source_sha256": ch["source_sha256"],
                "segments": [r["page"] for r in ch_rows],
                "join_stats": join_stats,
            })
            gap_note = (
                f", joins {join_stats['min_raw_gap_ms']}->{join_stats['min_final_gap_ms']}ms min "
                f"(+{join_stats['total_added_ms']}ms)"
                if join_stats["joins"]
                else ""
            )
            print(
                f"{target.name}: {clock_fmt(secs)} ({secs}s, {target.stat().st_size} bytes{gap_note})",
                flush=True,
            )

    engine_info = summary.get("engine") or {}
    commit_short = (engine_info.get("commit") or "unknown")[:7]
    engine_label = f"{engine_info.get('name', 'audio.cpp')} {commit_short} ({engine_info.get('backend', 'vulkan')}) / Fish Audio Drama 3"
    total_seconds = round(sum(c["seconds"] for c in chapters_out), 3)

    checks_flagged = None
    if args.checks and Path(args.checks).is_file():
        checks_data = json.loads(Path(args.checks).read_text(encoding="utf-8"))
        checks_flagged = checks_data.get("flagged")

    manifest = {
        "schema_version": 1,
        "book_id": args.book_id or source.get("book_id"),
        "title": args.title or source.get("title"),
        "credit": args.credit,
        "engine": engine_label,
        "model": engine_info.get("model", "drama-3-backbone-8bit-experts-Q4_K_S.gguf"),
        "voice": args.voice,
        "review_status": args.review_status,
        "asr_flagged_segments": checks_flagged,
        "total_segments": len(rows),
        "total_seconds": total_seconds,
        "chapters": [
            {k: c[k] for k in ("number", "title", "file", "seconds", "bytes", "sha256", "segments")}
            for c in chapters_out
        ],
    }
    (out_dir / "chapters.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    if args.render_record:
        rec_path = Path(args.render_record).resolve()
        rec_path.parent.mkdir(parents=True, exist_ok=True)
        rec_settings = dict(summary.get("settings") or {})
        rec_settings["join_padding"] = {
            "sentence_gap_ms": args.sentence_gap_ms,
            "paragraph_gap_ms": args.paragraph_gap_ms,
        }
        record = {
            "schema_version": 1,
            "book": manifest["book_id"],
            "generated": str(date.today()),
            "status": args.review_status,
            "engine": engine_info,
            "settings": rec_settings,
            "voice": args.voice,
            "voice_reference": summary.get("voice") or {},
            "format": f"mono {args.sample_rate} Hz {args.bitrate} CBR MP3",
            "total_segments": len(rows),
            "total_seconds": total_seconds,
            "total_bytes": sum(c["bytes"] for c in chapters_out),
            "asr_flagged_segments": checks_flagged,
            "public_page": args.public_page,
            "audio_dir": args.audio_rel_dir,
            "chapters": chapters_out,
        }
        rec_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Updated render record -> {rec_path}")

    print(
        f"Assembled {len(chapters_out)} chapters, {clock_fmt(total_seconds)} "
        f"({total_seconds}s), {sum(c['bytes'] for c in chapters_out)} bytes -> {out_dir}"
    )
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def add_common_engine_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--cli", default=None, help="path to audiocpp_cli (auto-detected)")
    p.add_argument("--model", default=None, help="path to Drama 3 GGUF (auto-detected)")
    p.add_argument("--backend", default=os.environ.get("DRAMA3_BACKEND", DEFAULT_BACKEND))
    p.add_argument("--cast", default=None, help="path to production/narration/cast.json")
    p.add_argument("--multi-speaker", action="store_true", help="send references JSON even for 1 voice")
    p.add_argument("--voice-ref", default=None, help="single reference WAV path")
    p.add_argument("--ref-text", default=None, help="exact transcript of --voice-ref")
    p.add_argument("--direction", default=DEFAULT_DIRECTION)
    p.add_argument("--no-direction", action="store_true", help="do not prepend --direction")
    p.add_argument("--chunk", type=int, default=DEFAULT_CHUNK)
    p.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    p.add_argument("--context", type=int, default=DEFAULT_CONTEXT)
    p.add_argument("--seed", type=int, default=DEFAULT_SEED)
    p.add_argument("--threads", type=int, default=DEFAULT_THREADS)
    p.add_argument("--session", action="append", default=[], help="extra session-option key=value")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_doc = sub.add_parser("doctor", help="check local Drama 3 runtime, model, ffmpeg, and uv")
    p_doc.add_argument("--cli", default=None)
    p_doc.add_argument("--model", default=None)

    p_pch = sub.add_parser("prepare-chapters", help="prepare word-exact chapter segments JSON")
    p_pch.add_argument("--book", required=True, help="book directory containing book.json")
    p_pch.add_argument("--out", required=True, help="output segments JSON path")
    p_pch.add_argument("--max-words", type=int, default=95)
    p_pch.add_argument("--keep-markdown", action="store_true")
    p_pch.add_argument("--script", default=None, help="optional tagged script.md output")
    p_pch.add_argument("--direction", default="")

    p_ppg = sub.add_parser("prepare-pages", help="verify tagged script.md against export into pages JSON")
    p_ppg.add_argument("script", help="production/narration/script.md")
    p_ppg.add_argument("source", help="exported Markdown or plain pages JSON")
    p_ppg.add_argument("out", help="output pages JSON path")

    p_ren = sub.add_parser("render", help="render pages/segments with local audio.cpp + Drama 3")
    p_ren.add_argument("pages_json")
    p_ren.add_argument("--out-dir", required=True)
    p_ren.add_argument("--pages", default="", help="comma-separated unit numbers")
    p_ren.add_argument("--start", type=int, default=1)
    p_ren.add_argument("--end", type=int, default=0)
    p_ren.add_argument("--batch-size", type=int, default=30)
    p_ren.add_argument("--resume", action="store_true", help="skip units whose WAV already exists")
    p_ren.add_argument("--model-sha256", default=None, help="precomputed model sha256 to skip hashing 23 GB")
    add_common_engine_args(p_ren)

    p_spl = sub.add_parser("split-retake", help="split capped segments at sentence boundaries and re-render")
    p_spl.add_argument("pages_json")
    p_spl.add_argument("--pages", required=True, help="comma-separated unit numbers to split")
    p_spl.add_argument("--out-dir", required=True)
    p_spl.add_argument("--part-limit", type=int, default=55)
    p_spl.add_argument("--sentence-gap-ms", type=int, default=DEFAULT_SENTENCE_GAP_MS)
    add_common_engine_args(p_spl)

    p_chk = sub.add_parser("check", help="check duration, WPM, silence, and faster-whisper ASR")
    p_chk.add_argument("pages_json")
    p_chk.add_argument("wav_dir")
    p_chk.add_argument("--out", default=None, help="output JSON report (default: <wav_dir>/checks.json)")
    p_chk.add_argument("--whisper-python", default=None)
    p_chk.add_argument("--whisper-model", default="small.en")
    p_chk.add_argument("--beam-size", type=int, default=5)
    p_chk.add_argument("--threads", type=int, default=4)
    p_chk.add_argument("--pause-threshold", type=float, default=1.5)
    p_chk.add_argument("--pause-limit", type=float, default=3.0)
    p_chk.add_argument("--wpm-range", default="95,220")
    p_chk.add_argument("--min-similarity", type=float, default=0.90)
    p_chk.add_argument("--pages", default="")
    p_chk.add_argument("--start", type=int, default=1)
    p_chk.add_argument("--end", type=int, default=0)

    p_asm = sub.add_parser("assemble-chapters", help="assemble verified segment WAVs into chapter MP3s")
    p_asm.add_argument("segments")
    p_asm.add_argument("--audio", required=True, help="directory containing page-NN.wav")
    p_asm.add_argument("--out", required=True, help="destination directory for chapter-NN.mp3 + chapters.json")
    p_asm.add_argument("--book-id", default=None)
    p_asm.add_argument("--title", default=None)
    p_asm.add_argument("--bitrate", default="96k")
    p_asm.add_argument("--sample-rate", type=int, default=24000)
    p_asm.add_argument(
        "--credit",
        default="Synthetic narration built with Fish Audio Drama 3 (local audio.cpp); not a human performance.",
    )
    p_asm.add_argument("--voice", default="synthetic narrator reference (Drama 3 rendering)")
    p_asm.add_argument(
        "--review-status",
        default="Coverage, durations, hashes, and faster-whisper ASR checked; human listening review pending.",
    )
    p_asm.add_argument("--checks", default=None, help="optional checks.json path")
    p_asm.add_argument("--render-record", default=None, help="optional production/narration/render.json path")
    p_asm.add_argument("--public-page", default=None)
    p_asm.add_argument("--audio-rel-dir", default=None)
    p_asm.add_argument("--sentence-gap-ms", type=int, default=DEFAULT_SENTENCE_GAP_MS)
    p_asm.add_argument("--paragraph-gap-ms", type=int, default=DEFAULT_PARAGRAPH_GAP_MS)

    args = parser.parse_args(argv)
    try:
        dispatch = {
            "doctor": cmd_doctor,
            "prepare-chapters": cmd_prepare_chapters,
            "prepare-pages": cmd_prepare_pages,
            "render": cmd_render,
            "split-retake": cmd_split_retake,
            "check": cmd_check,
            "assemble-chapters": cmd_assemble_chapters,
        }
        return dispatch[args.command](args)
    except Drama3Error as err:
        print(f"drama3: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
