# Visual style and book design — The Quest of the Golden Garbanzo

## Edition and narrative purpose
- **Book**: *The Quest of the Golden Garbanzo* (`garbanzo-family/standalone/the-quest-of-the-golden-garbanzo`), 10 chapters, 8,255 words, plain American English (~Grade 5–6) with three Spanish phrases.
- **Format**: Illustrated retrofit of the reflowable EPUB 3 and 6 × 9 in reading PDF, plus a new illustrated 720 × 1080 JPEG cover. Source prose in `manuscript/*.md` is untouched.
- **Art frequency (author-approved quota-saving strategy)**: 8 interior story illustrations anchored at the book's most pivotal emotional and comic beats (Chapters 1, 3, 4, 5, 6, 7, 9, 10), generated as two 2 × 2 grids (4 scenes per image call) and cleanly cropped into individual local assets, plus 1 dedicated full-resolution portrait cover illustration and 1 cast/prop reference sheet (4 image-generation calls total).
- **Narrative purpose**: Pictures carry comedy, warmth, and spatial truth — Garbanzo's confetti chaos, the muffled coffee-mug timeout, Poki's tender silver twilight visit, the absurd crooked Spanish lot, the diving glass-wall padel bounce, midnight debugging, twelve tumbling plush dragons, and calm sunny Tuesday in Valladolid — without altering a word of prose.

## Cast, setting and prop reference
- **Reference asset**: `assets/illustrations/ref-cast.png` (reference-only, not counted as a story illustration).
- **Jorge (`CHAR-0001`)**: 37-year-old practical, warm Spanish-American dad. Short dark wavy hair, light friendly stubble, expressive eyes, medium build. Wears rolled-sleeve navy or slate henley/button-down, comfortable jeans/chinos, sneakers (or court shorts/polo for padel; casual shorts/sandals in Valladolid). Carries yellow tape measure, tablet, padel racket, or small toolbox. **Never shown cooking or tending a stove (`FACT-0009`).**
- **Marissa (`CHAR-0002`)**: 38-year-old warm, sharp-eyed mom. Shoulder-length chestnut brown hair, expressive eyebrows, warm smile. Wears cozy cream/oatmeal fleece sweater or terracotta cardigan, dark jeans. Carries pancake plate, coffee mug, or yellow legal pad.
- **Clara (`CHAR-0003`)**: 6-year-old energetic, bright-eyed girl. Wavy dark brown hair (often half-up or messy pigtails with a tiny unicorn clip), rosy cheeks. Signature wardrobe by scene: purple unicorn socks (Ch 1, Ch 7), bright yellow raincoat over sneakers (Ch 4), red flannel pajamas (Ch 7), casual tee/sneakers in Spain (Ch 6, Ch 10).
- **Garbanzo (`CHAR-0004`)**: Palm-sized (plum-sized) golden-tan chickpea-shaped desk-bot on **four stubby green metal feet**, with two small waving stubby arms and glowing expressive amber/green LED eyes and tiny front status screen. **Disclosure rule**: plain golden-tan shell in Ch 1 & Ch 3; wears a bright, slightly crooked unicorn sticker on his side from Ch 4 onward; emits **zero confetti** in Ch 10.
- **Poki (`CHAR-0005`, `FACT-0010`)**: Sleek, dignified cat with **glossy ink-dark black fur, steady warm amber eyes, and neat white-tipped paws**, surrounded by a gentle pale silver starlight glow. **HARD RULE: strictly costume-free — never wears any dragon costume, hat, cape, or collar.**
- **The Golden Garbanzo Pot (`FACT-0001`, `FACT-0002`)**: Small gleaming copper pot with lid resting beside the toaster, holding one walnut-sized golden chickpea. Chilly/dark in Ch 1; glowing warm honey-gold in Ch 3 & Ch 7. **Disclosure rule**: never show the split-open golden sun charm before Chapter 8 (keep cover showing the whole glowing chickpea in the copper pot).

## Medium, composition and pacing
- **Medium**: Warm modern children's storybook watercolor, gouache, and soft colored-pencil ink linework on subtly textured cream paper. Expressive faces, clear silhouettes, lively body language.
- **Palette & light progression**:
  - New Jersey winter/rush scenes (Ch 1, Ch 7): cozy indoor amber lamp/kitchen light contrasted with cool blue-gray window light or winter rain.
  - Twilight magic (Ch 4): deep November indigo sky, first stars, soft pale silver glow around Poki, warm yellow raincoat focal accent.
  - Spain scouting & Valladolid (Ch 5, Ch 6, Ch 10): sunlit Castilian ochre, terracotta brick, bright blue padel glass, crisp white walls, dark blue roof solar panels, golden dusk warmth.
- **Typography separation**: No rendered speech bubbles, captions, or story prose inside illustrations. Cover title typography is composited cleanly in Python (`build_edition.py`) over a reserved calm upper sky/parchment band on the cover illustration.

## Layout and reproduction
- **PDF trim**: 6 × 9 in (`432 × 648 pt`), `48 pt` horizontal margins (`4.67 in` text column width). Interior illustrations placed centered inside the text column at `4.3–4.5 in` wide (`~2.8–3.2 in` tall, preserving native aspect ratio, never stretched), with thin warm-gold hairline border (`0.5 pt`) and generous vertical breathing room (`10–12 pt` top/bottom) so body typography (`10.3 pt` serif, `14.6 pt` leading) stays untouched.
- **EPUB 3 (reflowable)**: Embedded JPEG assets under `EPUB/images/`, semantic `<figure class="story-art"><img src="images/..." alt="..."/><figcaption>...</figcaption></figure>` with `max-width: 100%; height: auto;` and clean `break-inside: avoid;`, so illustrations scale gracefully on phones, tablets, and desktop readers.
- **Cover**: `720 × 1080` JPEG (2:3 portrait), high-contrast title overlaid cleanly over the calm upper zone of `cover-art.png`, keeping the family, Garbanzo, copper pot, and sunlit Spanish archway cleanly below the title band.

## Provenance, accessibility and review
- Tool: Antigravity built-in `image-generator` subagent. All generated sheets, cropped masters, hashes, prompts, and alt texts are recorded in `production/illustration-plan.json`.
- Independent inspection: every cropped interior panel and the composed cover are inspected visually at full size against canon (`FACT-0001`..`FACT-0019`), followed by rendering and visually proofing the picture-bearing PDF pages via `pdftoppm` and validating EPUB XML, alt-text preservation, and catalog checks.
