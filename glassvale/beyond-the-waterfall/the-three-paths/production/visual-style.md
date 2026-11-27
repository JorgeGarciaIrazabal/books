# The Three Paths — Production & Visual Style Guide

## Edition and Narrative Purpose
- **Audience:** Read together by parent and seven-year-old Clara; bright, atmospheric, spooky-cozy fantasy adventure.
- **Format:** 7 × 9 in illustrated storybook PDF (blended-text spreads where story prose sits directly inside soft painted open zones of the illustrations) plus reflowable EPUB 3 and composed 720 × 1080 JPEG cover.
- **Art Frequency:** 12 interior illustrations (3 sheets generated as 2×2 grids, cleanly cropped) + 1 dedicated portrait cover + 3 approved reference sheets in `assets/references/`.

## Cast, Setting and Prop Reference
- `assets/references/ref-leaders-2x2.png` (Jorge, Marissa + Pip, Peter + sand-timer, Headmistress Monica)
- `assets/references/ref-students-2x2.png` (Clara, Maya + Pebble, Sam, Victor)
- `assets/references/ref-world-2x2.png` (Glassvale Academy exterior, Brass Spire workshop, Living Dome, Starlight Tower + Deep Gate)

## Medium, Composition and Blended-Text Rules
- **Medium:** Rich painterly watercolor, gouache, and expressive crisp ink linework on warm subtly textured storybook paper.
- **Zero Text Inside Raw Art:** Never allow letters, labels, or captions inside generated illustrations.
- **Open Text-Safe Zone (Crucial):** Every interior panel must leave a calm, uncluttered softly painted wash (~35–40% of the panel in the specified upper-left or upper-right zone) so `build_edition.py` can blend story prose right over that quiet painted sky/wall/mist with high contrast and zero collision with faces or action.
