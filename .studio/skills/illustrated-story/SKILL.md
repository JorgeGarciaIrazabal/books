---
name: illustrated-story
description: Create or revise illustrated storybooks and chapter books, including children's stories where pictures are part of the reading format. Plan consistent characters, narrative art and final-page proof; excludes unrelated standalone images and cover-only work.
---

# Illustrated story

Deliver a readable story in which pictures carry narrative work and remain consistent across the book. Preserve the author's prose, format, art count, creative direction, and publication authority. Work from the repository root when a Book Studio workspace is present; read applicable AGENTS.md and scoped book records. Outside that workspace, use equivalent source, order, style, and output records without imposing its directory scheme.

## Establish the edition

Distinguish a picture book, an illustrated chapter book, and an illustrated retrofit. A source file, a chapter, a scene, a page, and a spread are different units. Read actual content and declared order before counting art. If the text has no chapters, choose transparent chapter boundaries where useful; do not silently reinterpret a request for pictures per chapter as pictures per page. Keep an existing page target unless the author changes it. Record language, intended age/use, page/trim target, reading medium, art frequency, and whether front matter is included. Use labeled reversible choices when preferences are missing.

For a new story, bring art direction into the brief and outline: identify visual actions, page turns, emotional changes, and discoveries that prose can leave to the pictures. For a retrofit, snapshot the existing text and exports, then add art without rewriting successful prose merely to fit it. Any necessary text changes remain explicit editorial revisions.

## Plan before rendering

Make a small page/spread dummy using actual text at the intended trim and reading size. Commission art for that composition: specify subject scale/direction, type area, negative space, crop and edge treatment, such as a bounded panel, vignette, or image fading into the page. Before commissioning the whole book, render representative composed pages and compare them in sequence or as intended spreads; revise an awkward art/text relationship here. Vary scale and distance for narrative purpose. Pictures can reveal expressions, spatial relationships, parallel action, or visual jokes; they need not repeat every sentence. Keep revelations on the permitted page turn, including background details and ornaments. Do not force every chapter into identical picture placement.

Create a concise visual bible and an illustration plan. Use stable image IDs, chapter paths from book.json, placement/anchor, scene and character state, narrative purpose, permitted disclosures, and useful alt text. The [plan reference](references/plan.md) defines the portable record and validation command. Art counts follow this assignment, not a universal quota. A cast/prop reference is reference material, not one of the requested story illustrations.

Set consistent silhouettes, apparent ages, proportions, hair, clothing, palette, key props, setting, medium, light progression, and expressive range. Visual decisions are provisional design choices until reconciled with text/canon; an image cannot silently retcon a character. A written visual bible alone does not prove that rendered identities match.

List the characters and important props included in each scene, plus exclusions that matter at that moment. A shared cast sheet identifies designs; it does not authorize every reference character to appear in every picture. Check background participants as carefully as foreground action. For nonhuman characters, specify how many faces or bodies are present; inspect expressive appendages for accidental duplicates. Track a prop’s function across the neighboring scene, such as a kite remaining tethered before it is wound in.

## Make and inspect the art

Use the available image-generation skill and built-in image tool for requested generated raster illustration. Generate a reusable cast/style reference, inspect it, and attach the relevant selected reference to each scene call. Do not rely only on repeated prose prompts or an earlier conversation image remaining available. Use one explicit scene request per final asset. Preserve existing author references and rights restrictions; describe broad visual traits rather than promising imitation of a named artist.

Separate story text and typography from the image. Keep essential subjects away from planned trim/gutter/crops and provide usable space for the actual layout. Save selected originals and final local assets in the project; retain original dimensions and source metadata. Record tool actually used, full prompt or prompt path, source/reference hashes, asset hash, revision, and rights/provenance status. Do not invent a model name, license, hand-painted origin, or permission clearance. If the built-in image tool is unavailable, report it; do not silently switch to a paid API route or substitute decorative SVG icons for requested scene illustration.

Inspect every selected image against its scene and cast reference at sufficient detail. Check identities, scale, prop custody, handed action, setting, expression, anatomy, unexpected text/objects, crop, and disclosure timing. A contact sheet helps judge cohesion but cannot replace individual inspection. Make a targeted correction when needed; after two unsuccessful focused revisions, change the composition/reference strategy or report the concrete limitation rather than looping.

## Design, proof, and deliver

Production owns type, hierarchy, space, image placement and export. Preserve comfortable type and contrast; use another layout before shrinking text just to retain a picture. Fit art deliberately without stretching or accidental clipping. Assess integration with the text, edge/background transitions, subject scale, negative space and visual rhythm across neighboring pages. Rectangular panels can be intentional; variety should serve the story rather than meet a quota of layout types. Record native pixels and placed physical size so effective PPI is calculable. Digital reading does not impose an automatic print-resolution threshold; printer-specific bleed, color, binding, safety margins and proof requirements come from the actual production brief.

Build from declared chapter order and hash the current text, plan, references, art, layout code and final exports. Independently review selected images with actual prose, then proof the rendered illustrated deliverable, including every picture-bearing page, chapter breaks, image/text collisions, page count and text fidelity. Alt text should describe narrative content without unsupported claims; verify it survives the intended format or disclose the limit. Record exact visual/text coverage and unresolved findings. Give the composed edition an explicit aesthetic assessment, separately from asset correctness and collision checks, with page examples and any taste judgments labeled as such. Neither file existence nor a successful converter certifies visual quality, accessibility, permissions, or print readiness. Author feedback overrides an earlier aesthetic pass; a revised export needs its own review.

In Book Studio, use art_director for visual direction, illustrator for assets, production_editor for book design/export, and illustration_reviewer for an independent image/layout check. The director integrates findings and updates tasks, gates and handoff. Use only needed roles; follow current runtime availability and do not claim a new role definition is already a running worker. If delegation is unavailable, do the scoped work and disclose the missing independence.

Record lessons only after observing outcomes: what failed, evidence, the smallest useful workflow change, and its scope. Do not generalize one book's art count, palette, trim or chapter length to all stories. Return the illustrated artifact, asset/prompt locations, actual checks, and remaining limits. Publication or external delivery remains separately authorized.
