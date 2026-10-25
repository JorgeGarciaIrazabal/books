#!/usr/bin/env python3
"""Check illustration-plan structure and chapter coverage; never judge pixels."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

IMAGE_SUFFIXES = {'.png', '.jpg', '.jpeg', '.webp', '.tif', '.tiff', '.avif', '.svg'}


def confined(book: Path, relative: object) -> Path:
    if not isinstance(relative, str) or not relative.strip():
        raise ValueError('expected a nonempty book-relative path')
    path = Path(relative)
    if path.is_absolute() or '..' in path.parts:
        raise ValueError(f'path must be relative and confined: {relative}')
    result = (book / path).resolve()
    if not result.is_relative_to(book):
        raise ValueError(f'path escapes book through a symlink: {relative}')
    return result


def validate(book: Path, plan_name: str, check_assets: bool) -> list[str]:
    errors: list[str] = []
    try:
        manifest = json.loads((book / 'book.json').read_text(encoding='utf-8'))
        plan = json.loads(confined(book, plan_name).read_text(encoding='utf-8'))
        if not isinstance(manifest, dict) or not isinstance(plan, dict):
            raise ValueError('book.json and illustration plan must be objects')
        chapters = manifest.get('chapters')
        if not isinstance(chapters, list) or any(not isinstance(c, str) for c in chapters):
            raise ValueError('book.json.chapters must be an ordered string array')
        if len(set(chapters)) != len(chapters):
            raise ValueError('book.json repeats a chapter path')
        if plan.get('schema_version') != 1:
            raise ValueError('illustration plan requires schema_version 1')
        if plan.get('chapter_paths') != chapters:
            errors.append('chapter_paths must exactly match book.json.chapters, including order')
        entries = plan.get('illustrations')
        if not isinstance(entries, list):
            raise ValueError('illustrations must be an array')
        quota = plan.get('art_per_chapter')
        if quota is not None:
            if (not isinstance(quota, dict)
                    or any(type(quota.get(key)) is not int for key in ('min', 'max'))
                    or not 0 <= quota['min'] <= quota['max']):
                raise ValueError('art_per_chapter must be null or integer min/max with 0 <= min <= max')
        chapter_pages: dict[str, set[int]] = {}
        for chapter in chapters:
            text = confined(book, chapter).read_text(encoding='utf-8')
            chapter_pages[chapter] = {int(p) for p in re.findall(r'^## Page (\d+)\s*$', text, re.MULTILINE)}
        ids: set[str] = set()
        coverage: dict[str, set[str]] = {chapter: set() for chapter in chapters}
        for index, entry in enumerate(entries, 1):
            label = f'illustrations[{index}]'
            if not isinstance(entry, dict):
                errors.append(f'{label}: expected an object')
                continue
            identifier = entry.get('id')
            if not isinstance(identifier, str) or not identifier.strip():
                errors.append(f'{label}: nonempty id is required')
            elif identifier in ids:
                errors.append(f'{label}: duplicate id {identifier}')
            else:
                ids.add(identifier)
                label = identifier
            chapter = entry.get('chapter')
            if not isinstance(chapter, str) or chapter not in coverage:
                errors.append(f'{label}: chapter must be a declared manuscript path')
                continue
            page = entry.get('page')
            if page is not None and (type(page) is not int or page < 1):
                errors.append(f'{label}: page must be null or a positive integer')
            elif page is not None and chapter_pages[chapter] and page not in chapter_pages[chapter]:
                errors.append(f'{label}: page {page} is not in chapter {chapter}')
            description = entry.get('alt_text')
            if not isinstance(description, str) or not description.strip():
                errors.append(f'{label}: useful nonempty alt_text is required')
            disclosure = entry.get('disclosure', {})
            if not isinstance(disclosure, dict):
                errors.append(f'{label}: disclosure must be an object when supplied')
            elif 'not_before_page' in disclosure:
                lower = disclosure['not_before_page']
                if type(lower) is not int or lower < 1:
                    errors.append(f'{label}: disclosure.not_before_page must be a positive integer')
                elif type(page) is int and page < lower:
                    errors.append(f'{label}: page {page} precedes disclosure bound {lower}')
            asset = entry.get('asset')
            if asset is None:
                coverage[chapter].add(f'planned:{identifier}')
                if check_assets:
                    errors.append(f'{label}: --check-assets requires a selected local asset')
                continue
            try:
                image = confined(book, asset)
                if image.suffix.lower() not in IMAGE_SUFFIXES:
                    raise ValueError('asset must have a supported image-file suffix')
                coverage[chapter].add(str(image))
                if check_assets and (not image.is_file() or image.stat().st_size == 0):
                    raise ValueError(f'selected asset is missing or empty: {asset}')
                digest = entry.get('asset_sha256')
                if digest is not None:
                    if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-fA-F]{64}', digest):
                        raise ValueError('asset_sha256 must contain 64 hexadecimal characters')
                    if image.is_file() and hashlib.sha256(image.read_bytes()).hexdigest() != digest.lower():
                        raise ValueError(f'asset hash does not match selected file: {asset}')
            except (OSError, ValueError) as exc:
                errors.append(f'{label}: {exc}')
        if quota is not None:
            for chapter, assets in coverage.items():
                if not quota['min'] <= len(assets) <= quota['max']:
                    errors.append(f'{chapter}: {len(assets)} distinct story pictures; expected {quota["min"]}–{quota["max"]}')
    except (OSError, ValueError, TypeError, KeyError) as exc:
        errors.append(str(exc))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('book', type=Path)
    parser.add_argument('--plan', default='production/illustration-plan.json')
    parser.add_argument('--check-assets', action='store_true')
    args = parser.parse_args()
    errors = validate(args.book.resolve(), args.plan, args.check_assets)
    for error in errors:
        print('ERROR ' + error, file=sys.stderr)
    if errors:
        print(f'Illustration plan: {len(errors)} error(s).', file=sys.stderr)
        return 1
    print('Illustration plan checks passed. Image/story/layout quality still requires visual review.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
