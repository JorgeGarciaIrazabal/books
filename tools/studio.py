#!/usr/bin/env python3
"""Small, dependency-free book-studio utilities. Python 3.11+."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile

REPO = Path(__file__).resolve().parents[1]
RESERVED = {"templates", "tools", "docs", "node_modules", "__pycache__"}
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
KINDS = {"fiction", "nonfiction"}
STAGES = {"brief", "structure", "sample", "draft", "development", "line-copy",
          "continuity-evidence", "production", "released"}
COLLECTIONS = {
    "scenes.json": "scenes", "knowledge.json": "disclosures",
    "threads.json": "threads", "tasks.json": "tasks",
    "research/sources.json": "sources", "research/claims.json": "claims",
    "canon/proposals.json": "proposals", "reviews/issues.json": "issues",
    "reviews/gates.json": "gates",
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def json_text(data) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def writable_file(path: Path):
    # Replacing a symlink is surprising even when its target stays in the project.
    if path.is_symlink():
        raise ValueError(f"Refusing to replace symlink: {path}")
    if path.exists() and not path.is_file():
        raise ValueError(f"Expected a regular file target: {path}")


def atomic_write(path: Path, text: str | bytes):
    writable_file(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".studio-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(text.encode("utf-8") if isinstance(text, str) else text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def confined(base: Path, relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"Expected a relative path without '..': {relative}")
    candidate = base / rel
    if not candidate.resolve().is_relative_to(base.resolve()):
        raise ValueError(f"Path escapes its scope: {relative}")
    return candidate


def book_path(root: Path, relative: str) -> Path:
    parts = Path(relative).parts
    if len(parts) != 3 or not all(SLUG.fullmatch(x) for x in parts):
        raise ValueError("Book path must be universe/series/book using kebab-case slugs")
    if parts[0] in RESERVED:
        raise ValueError(f"Reserved universe slug: {parts[0]}")
    return confined(root, relative)


def chapter_paths(book: Path, manifest: dict, *, check_contents: bool = True) -> list[Path]:
    if not isinstance(manifest, dict):
        raise ValueError("book.json must be an object")
    chapters = manifest.get("chapters")
    if not isinstance(chapters, list) or any(not isinstance(x, str) for x in chapters):
        raise ValueError("book.json.chapters must be an ordered array of relative paths")
    if len(set(chapters)) != len(chapters):
        raise ValueError("Duplicate chapter paths in book.json")
    paths = []
    for relative in chapters:
        path = confined(book, relative)
        if (not Path(relative).parts or Path(relative).parts[0] != "manuscript"
                or path.suffix != ".md" or not path.resolve().is_relative_to((book / "manuscript").resolve())):
            raise ValueError(f"Chapter must be a Markdown file inside manuscript/: {relative}")
        if not path.is_file() or (check_contents and not path.read_text(encoding="utf-8").strip()):
            raise ValueError(f"Missing or empty chapter: {relative}")
        paths.append(path)
    if len({p.resolve() for p in paths}) != len(paths):
        raise ValueError("Multiple chapter paths resolve to the same file")
    return paths


def mkdir_tracked(directory: Path, created: list[Path]):
    missing = []
    current = directory
    while not current.exists():
        missing.append(current)
        current = current.parent
    for path in reversed(missing):
        try:
            path.mkdir()
        except FileExistsError:
            if not path.is_dir():
                raise
        else:
            created.append(path)


def new_book(root: Path, args):
    relative = "/".join((args.universe, args.series, args.book))
    book = book_path(root, relative)
    if book.exists():
        raise ValueError(f"Book already exists; no files changed: {relative}")
    universe, series = book.parents[1], book.parent
    values = {"universe": args.universe, "series": args.series, "book": args.book,
              "title": args.title or args.book.replace("-", " ").title(),
              "universe_title": args.universe.replace("-", " ").title(),
              "series_title": args.series.replace("-", " ").title(), "kind": args.kind}

    def replace(value):
        if isinstance(value, str):
            for key, replacement in values.items():
                value = value.replace("{{" + key + "}}", replacement)
            return value
        if isinstance(value, dict):
            return {key: replace(item) for key, item in value.items()}
        if isinstance(value, list):
            return [replace(item) for item in value]
        return value

    planned = {}
    for level, dest, marker in (("universe", universe, "universe.json"),
                                ("series", series, "series.json"), ("book", book, "book.json")):
        if dest.exists():
            if not (dest / marker).is_file():
                raise ValueError(f"Existing container has no {marker}: {dest}")
            data = read_json(dest / marker)
            if not isinstance(data, dict):
                raise ValueError(f"{marker} must be an object: {dest}")
            if data.get("id") != values[level]:
                raise ValueError(f"Container ID differs from its path: {dest}")
            if level == "series" and data.get("universe") != args.universe:
                raise ValueError("Existing series belongs to a different universe")
            continue
        for source in sorted((REPO / "templates" / level).rglob("*")):
            if not source.is_file():
                continue
            target = confined(dest, str(source.relative_to(REPO / "templates" / level)))
            planned[target] = (json_text(replace(read_json(source))) if source.suffix == ".json"
                               else replace(source.read_text(encoding="utf-8")))

    series_manifest = series / "series.json"
    data = json.loads(planned[series_manifest]) if series_manifest in planned else read_json(series_manifest)
    if not isinstance(data, dict) or not isinstance(data.get("books"), list) or any(not isinstance(x, str) for x in data["books"]):
        raise ValueError("series.json.books must be an ordered array of book slugs")
    if args.book in data["books"]:
        raise ValueError("Book already registered in series.json; reconcile the existing entry first")
    data["books"].append(args.book)
    existing_series_text = series_manifest.read_text(encoding="utf-8") if series_manifest.exists() else None
    # Register the book only after its files have been created successfully.
    planned.pop(series_manifest, None)
    planned[series_manifest] = json_text(data)
    for target in planned:
        confined(root, str(target.relative_to(root)))
        if target.exists() and target != series_manifest:
            raise ValueError(f"Refusing to overwrite: {target}")
    if args.dry_run:
        print("Would create " + relative + " and register it in series.json")
        print("\n".join(str(x.relative_to(root)) for x in planned))
        return
    created = []
    created_directories = []
    series_written = False
    try:
        for path, content in planned.items():
            mkdir_tracked(path.parent, created_directories)
            atomic_write(path, content)
            if path == series_manifest:
                series_written = True
            if path != series_manifest or existing_series_text is None:
                created.append(path)
    except Exception:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        if series_written and existing_series_text is not None:
            atomic_write(series_manifest, existing_series_text)
        # Never scan for or remove directories created by unrelated tasks.
        for directory in reversed(created_directories):
            try:
                directory.rmdir()
            except OSError:
                pass
        raise
    print(f"Created {relative}; next: fill brief.md, then draft one representative unit")


def validate_collection(path: Path, key: str, errors: list[str]):
    try:
        data = read_json(path)
        if not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get(key), list):
            raise ValueError(f"Expected schema_version=1 and array '{key}'")
        ids = set()
        for item in data[key]:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"].strip():
                raise ValueError(f"Every {key} record needs a nonempty string id")
            if item["id"] in ids:
                raise ValueError(f"Duplicate record ID: {item['id']}")
            ids.add(item["id"])
        return data[key]
    except (OSError, ValueError, TypeError) as exc:
        errors.append(f"{path}: {exc}")
        return []


def check_book(root: Path, book: Path) -> tuple[list[str], list[str]]:
    errors, notes = [], []
    try:
        relative = str(book.relative_to(root))
        book_path(root, relative)
        data = read_json(book / "book.json")
        if not isinstance(data, dict):
            raise ValueError("book.json must be an object")
        for key, value in zip(("universe", "series", "id"), book.relative_to(root).parts):
            if data.get(key) != value:
                raise ValueError(f"book.json.{key} must match path '{value}'")
        if data.get("schema_version") != 1 or data.get("kind") not in KINDS or data.get("stage") not in STAGES:
            raise ValueError("Invalid schema_version, kind, or stage in book.json")
        if not isinstance(data.get("title"), str) or not data["title"].strip():
            raise ValueError("Book title must be a nonempty string")
        chapters = chapter_paths(book, data)
        if not chapters:
            notes.append(f"{relative}: no chapters yet (scaffold only)")
        unlisted = set((book / "manuscript").rglob("*.md")) - set(chapters)
        if unlisted:
            notes.append(f"{relative}: {len(unlisted)} manuscript file(s) excluded from chapter order")
        for container, marker, identifier in ((book.parents[1], "universe.json", data["universe"]),
                                               (book.parent, "series.json", data["series"])):
            parent = read_json(container / marker)
            if not isinstance(parent, dict) or parent.get("id") != identifier or parent.get("schema_version") != 1:
                raise ValueError(f"Invalid {marker} identity/schema")
            if marker == "universe.json":
                revision = parent.get("canon_revision")
                if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
                    raise ValueError("canon_revision must be a nonnegative integer")
            else:
                if parent.get("universe") != data["universe"] or not isinstance(parent.get("books"), list):
                    raise ValueError("Invalid series universe/books")
                ordered = parent["books"]
                if any(not isinstance(x, str) or not SLUG.fullmatch(x) for x in ordered) or len(set(ordered)) != len(ordered):
                    raise ValueError("series.json.books needs unique kebab-case book slugs")
                if ordered.count(data["id"]) != 1:
                    raise ValueError("Book must appear exactly once in series.json.books")
                for slug in ordered:
                    if not (container / slug / "book.json").is_file():
                        raise ValueError(f"Series references missing book: {slug}")
        for name in ("AGENTS.md", "brief.md", "outline.md", "style.md", "handoff.md", "state.md", "decisions.md", "production/brief.md"):
            if not confined(book, name).is_file():
                errors.append(f"{relative}: missing {name}")
        for path in book.rglob("*"):
            if path.is_symlink() and not path.resolve().is_relative_to(book.resolve()):
                errors.append(f"{relative}: symlink escapes book scope: {path}")
        records = {}
        for filename, key in COLLECTIONS.items():
            records[filename] = validate_collection(book / filename, key, errors)
        validate_collection(book.parents[1] / "canon.json", "facts", errors)
        validate_collection(book.parents[1] / "timeline.json", "events", errors)
        validate_collection(book.parent / "promises.json", "promises", errors)
        sources = records["research/sources.json"]
        source_ids = {item["id"] for item in sources if isinstance(item, dict) and "id" in item}
        claims = records["research/claims.json"]
        for claim in claims:
            if not isinstance(claim, dict):
                continue
            evidence = claim.get("evidence", [])
            if not isinstance(evidence, list):
                errors.append(f"{relative}: claim {claim.get('id')} evidence must be an array")
                continue
            for entry in evidence:
                if not isinstance(entry, dict) or entry.get("source_id") not in source_ids:
                    errors.append(f"{relative}: claim {claim.get('id')} has an unknown source reference")
            if claim.get("status") == "verified" and (not evidence or any(not isinstance(e, dict) or not e.get("locator") for e in evidence)):
                errors.append(f"{relative}: verified claim {claim.get('id')} needs source evidence and locators")
    except (OSError, ValueError, TypeError, KeyError) as exc:
        errors.append(f"{book}: {exc}")
    return errors, notes


def check(root: Path, args) -> int:
    if args.book:
        books = [book_path(root, args.book)]
    else:
        books = sorted({p.parent for p in root.rglob("book.json")
                        if not any(part.startswith(".") or part in RESERVED
                                   for part in p.relative_to(root).parts[:-1])})
    errors, notes = [], []
    for book in books:
        found, comments = check_book(root, book)
        errors.extend(found)
        notes.extend(comments)
    for item in notes:
        print("NOTE " + item)
    for item in errors:
        print("ERROR " + item, file=sys.stderr)
    print(f"Checked {len(books)} book(s): {len(errors)} structural error(s). Literary/factual quality requires review.")
    return int(bool(errors))


def packet(root: Path, args):
    book = book_path(root, args.book)
    if args.max_chars < 1000:
        raise ValueError("max-chars must be at least 1000")
    names = (("AGENTS.md", "brief.md", "style.md") if args.mode == "review" else
             ("AGENTS.md", "brief.md", "style.md", "handoff.md", "outline.md"))
    paths = [confined(book, name) for name in names]
    paths.extend(confined(root, name) for name in args.include)
    paths = list(dict.fromkeys(paths))
    chunks = [f"# Context packet: {args.book}\n\nTask: {args.task}\n\n"
              "Snapshot only. Check freshness and POV permissions. Canon/knowledge are not automatically filtered.\n"]
    omissions = []
    used = len(chunks[0])
    for path in paths:
        raw = path.read_bytes()
        content = raw.decode("utf-8")
        digest = hashlib.sha256(raw).hexdigest()
        chunk = f"\n## {path.relative_to(root)}\nSHA-256: {digest}\n\n{content}\n"
        # Reserve room for an omissions list; never silently cut a source passage.
        if used + len(chunk) > args.max_chars - 600:
            omissions.append(str(path.relative_to(root)))
        else:
            chunks.append(chunk)
            used += len(chunk)
    footer = "\n## Omitted for size\n" + ("\n".join(omissions) if omissions else "None") + "\n"
    if used + len(footer) > args.max_chars:
        raise ValueError("Omission inventory exceeds packet budget; use fewer inputs or a larger budget")
    print("".join(chunks) + footer, end="")
    if omissions:
        print("Packet omitted whole files; review its omission list before use.", file=sys.stderr)


def build(root: Path, args):
    book = book_path(root, args.book)
    manifest_path = confined(book, "book.json")
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    chapters = chapter_paths(book, manifest, check_contents=False)
    if not chapters:
        raise ValueError("Cannot build an empty manuscript")
    if not SLUG.fullmatch(args.name):
        raise ValueError("Export name must be a kebab-case slug")
    if (book / "exports").is_symlink():
        raise ValueError("exports/ must be a real directory, not a symlink")
    output = confined(book, f"exports/{args.name}.md")
    record = confined(book, f"exports/{args.name}.manifest.json")
    for target in (output, record):
        writable_file(target)
        for source in (manifest_path, *chapters):
            if target.resolve() == source.resolve() or (target.exists() and target.samefile(source)):
                raise ValueError(f"Export target aliases a source file: {target}")
    if (output.exists() or record.exists()) and not args.replace:
        raise ValueError("Export already exists; choose a new --name or explicitly use --replace")
    # Hash the same bytes used for assembly, even if a source changes afterward.
    snapshots = [(manifest_path, manifest_bytes), *[(p, p.read_bytes()) for p in chapters]]
    sections = []
    for path, raw in snapshots[1:]:
        section = raw.decode("utf-8")
        if not section.strip():
            raise ValueError(f"Empty chapter: {path.relative_to(book)}")
        sections.append(section.rstrip())
    text = "\n\n".join(sections) + "\n"
    sources = [{"path": str(p.relative_to(book)), "sha256": hashlib.sha256(raw).hexdigest()}
               for p, raw in snapshots]
    record_data = {"schema_version": 1, "book": args.book, "sources": sources,
                   "output": str(output.relative_to(book)), "output_sha256": hashlib.sha256(text.encode()).hexdigest(),
                   "format": "markdown", "editorial_status": "unverified",
                   "note": "Assembly only. Review coverage, front/back matter, rights and proof require separate verification."}
    previous = {p: p.read_bytes() if p.exists() else None for p in (output, record)}
    written = []
    try:
        for path, content in ((output, text), (record, json_text(record_data))):
            atomic_write(path, content)
            written.append(path)
    except Exception:
        for path in reversed(written):
            if previous[path] is None:
                path.unlink(missing_ok=True)
            else:
                atomic_write(path, previous[path])
        raise
    print(f"Built {output.relative_to(root)} and source manifest; no editorial approval implied")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--root", type=Path, default=REPO, help="Library root (templates stay with this script)")
    sub = result.add_subparsers(dest="command", required=True)
    new = sub.add_parser("new", help="Create universe/series/book without overwriting existing content")
    for name in ("universe", "series", "book"):
        new.add_argument(name)
    new.add_argument("--title")
    new.add_argument("--kind", choices=sorted(KINDS), default="fiction")
    new.add_argument("--dry-run", action="store_true")
    lint = sub.add_parser("check", help="Check structure, manifests, record IDs and source references")
    lint.add_argument("book", nargs="?")
    context = sub.add_parser("packet", help="Print a bounded context packet with source hashes")
    context.add_argument("book")
    context.add_argument("--task", default="Read the brief and complete the next scoped task")
    context.add_argument("--mode", choices=("draft", "review"), default="draft",
                         help="Review mode excludes outline and handoff; explicitly include the text to assess")
    context.add_argument("--include", action="append", default=[], help="Extra file path relative to library root; repeatable")
    context.add_argument("--max-chars", type=int, default=32000)
    export = sub.add_parser("build", help="Assemble declared chapters into Markdown plus a hash manifest")
    export.add_argument("book")
    export.add_argument("--name", default="manuscript")
    export.add_argument("--replace", action="store_true")
    return result


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    root = args.root.resolve()
    handlers = {"new": new_book, "check": check, "packet": packet, "build": build}
    try:
        return handlers[args.command](root, args) or 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
