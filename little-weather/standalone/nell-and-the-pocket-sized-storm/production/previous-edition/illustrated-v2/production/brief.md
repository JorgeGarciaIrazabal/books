# Illustrated private reading edition

Nell and the Pocket-Sized Storm, illustrated-v2. English read-aloud for a seven-year-old. Exactly 30 story/PDF pages at 7.5 × 9.5 inches, with title on page 1 and no extra cover or front matter. Six five-page chapters, with two distinct narrative pictures each: twelve total. The 2,047-word story-page prose is unchanged from archived text-only v1; chapter headings and visual layout were added.

## Art and page design
Original AI-generated gouache-style narrative pictures, made with built-in image_gen.imagegen from an inspected cast reference. Broad media traits were used without requesting a named artist's imitation. Twelve original PNG masters at 1536 × 1024 pixels are in assets/illustrations/. Cast reference is separate and does not count toward twelve. Exact scene, prompt, reference and revision records are in production/illustration-plan.json and image-generation-run.json. Full prompts are in production/prompts/. No human illustrator commission, endorsement or legal rights clearance is claimed.

Type remains 16.8 pt, with 1.28 leading and 0.075-inch paragraph spacing. Chapter cues, dark blue text and warm cream paper support reading. Pictures follow their own page prose and preserve the complete 3:2 composition at 3.75 × 2.5 inches, rather than stretching into the wider available box. This yields native 409.6 PPI per axis at placement. Original PNGs are retained; high-quality JPEG 92, 4:4:4 derivatives at unchanged dimensions reduce the self-contained HTML/PDF size. All derivatives are recorded in the export manifest. No fixed universal printer-resolution rule is implied.

## Rebuild
Run from the repository root:

    python3 .studio/skills/illustrated-story/scripts/validate_plan.py little-weather/standalone/nell-and-the-pocket-sized-storm --check-assets
    python3 tools/studio.py build little-weather/standalone/nell-and-the-pocket-sized-storm --name nell-and-the-pocket-sized-storm --replace
    python3 little-weather/standalone/nell-and-the-pocket-sized-storm/production/build.py
    python3 little-weather/standalone/nell-and-the-pocket-sized-storm/production/verify_illustrated.py

Requires Python, Pillow, local Chrome or Chromium, pdfinfo, pdftotext and pdfimages. No image API key or network call is needed to rebuild from saved art. Source chapter order is solely book.json. Build checks all 30 page frames after embedded images load and records native/placed dimensions, hashes, effective PPI, actual tool command and output count. Successful conversion is not independent art acceptance.

## Editions, proof and limits
Current reading files are exports/nell-and-the-pocket-sized-storm.pdf, .html and .md. The earlier text-only edition and source/metadata are preserved in production/previous-edition/text-only-v1/. Current snapshots, findings and coverage are in reviews/illustrated/. Source HTML carries meaningful alt descriptions; PDF alt-tag preservation and full accessibility are not certified. This is a private digital reading edition; printer-specific bleed, binding, paper, color and physical proof were not commissioned. No publication or upload is authorized. Model/process records stay outside story pages.
