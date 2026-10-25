# Illustration plan record

In Book Studio, use production/visual-style.md and production/illustration-plan.json. Art masters and selected scene images belong under assets/illustrations/ or a similarly explicit book-local directory; build outputs stay under exports/. Art references may be separate assets with reference-only status.

Top-level fields:
- schema_version: 1.
- chapter_paths: ordered manuscript paths matching book.json.chapters, so all chapters participate in the coverage check.
- art_per_chapter: null when no count is specified, or {"min": 1, "max": 2} for this particular author instruction. Count distinct story illustration records, not decorative ornaments or reference sheets. A reused file counts once per chapter.
- illustrations: records with nonempty id and chapter path; page is a positive physical/story page number or null before pagination; asset is a confined book-local file path or null while planned; alt_text is a useful content description.

Optional record fields include chapter_id, scene_ref, narrative_purpose, description, subjects_state, disclosure, placement, provenance, prompt_path, reference_hashes, asset_sha256, revision, and status. Add actual production fields when known; do not fabricate completed metadata to fill a schema. Status commonly progresses planned → generated → accepted after visual review. A versioned rejected asset can remain in its audit record while the selected record points to the current file.

A disclosure object can include not_before_page, an integer lower bound checked by the helper. It can also describe permitted revelations and explicitly prohibited early details. The helper cannot judge whether an image actually reveals those details.

Placement should tie the commission to the actual page/spread dummy: text area, subject scale/direction, negative space, edge/background treatment and fit/crop intent. Link representative composed-page renders so art direction and production can assess the design before repeating it across the book. Record focal safe area and, after layout, width_inches/height_inches. Rectangular panels are a design option; layout counts do not establish rhythm or integration. Record source pixel dimensions and effective PPI = pixels / placed inches per axis. Use the printer's requested threshold only for an actual print edition. A printer-ready claim also needs color, bleed, binding and export checks.

Provenance should identify the actual generator or artist, source/reference files and rights status, prompt record, generation/edit revision, and selected asset hash. "Generated" is a method, not a blanket rights clearance. Generated faces/looks are original design assumptions unless the author supplied character references.

Validate a populated plan from the repository root:

    python3 .studio/skills/illustrated-story/scripts/validate_plan.py U/S/B
    python3 .studio/skills/illustrated-story/scripts/validate_plan.py U/S/B --check-assets

Use --plan to select another book-relative plan path. The helper checks declared chapter coverage, IDs, page membership when source has numbered Page headings, count constraints, path confinement, basic descriptions, optional disclosure bounds and asset hashes. --check-assets also requires every selected asset to exist and be nonempty. It does not inspect pixels, run image generation, certify provenance, or replace an independent visual proof. For an unpopulated scaffold, fill chapter_paths before validating against a manuscript.
