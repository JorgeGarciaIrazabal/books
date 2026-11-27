# The Ledger of Ashes — character prompt pack

Production prompts for creating consistent character reference art for the book trailer.

**Start here:**

1. `style.md` — shared style blocks, negative prompt, goblin/human design rules, reference workflow.
2. `cast-list.md` — every character, tier, role and signature visual, with links to their sheet.
3. `principal/` — full sheets for the nine characters who carry the trailer.
4. `supporting-cast.md` — compact sheets for the wider cast.
5. `template.md` — blank sheet for adding a character.

## What “done” looks like

For each principal character:

- A clean four-view turnaround: front, three-quarter, profile, back.
- A chest-up cinematic portrait.
- A six-panel expression sheet.
- A detail sheet for their signature props.
- A saved front-view reference image and seed.

For each supporting character:

- One clean reference sheet.
- One cinematic portrait if they appear in the trailer.

## Using the sheets

Each character sheet is standalone. The positive prompt already includes the shared style, and the negative prompt follows it. Copy one section and send it, one character at a time. You do not need to open `style.md` or assemble anything.

For Midjourney, add `--ar 16:9 --style raw --stylize 150` for portraits, or `--ar 4:5` for reference sheets. For Flux, use 4:5 or 1:1 for sheets and 16:9 for portraits.

If you add a new character, use `template.md` and the formula in `style.md`.

## Consistency rules

- One character per generation. Never generate the whole cast in one image.
- Use the same front-view reference image and seed for every prompt in a character's file.
- The locked visual token is the contract. Do not improvise new scars, jewelry, tattoos or clothing between shots.
- Keep the silhouette readable: Ragna's key pouch and penknife, Tavin's too-big coat and pen, Sella's tight hair and apron, Neri's folded apron and hammer, Merrok's hands behind his back and spectacles, Harrow's silver wrist clip.
- Change expression, pose, lighting and camera. Do not change the person.

## Canon vs design

The manuscript gives few physical descriptions. Everything here is a trailer-only visual proposal. It does not change the book, and it should not be treated as canon. If a detail contradicts the manuscript, the manuscript wins.

## Rights

*The Ledger of Ashes* is unofficial fan fiction. The trailer and character art are not authorised, endorsed or sponsored by the rights holders. Do not use official Harry Potter imagery, logos, costumes, or recognizable film designs.

## File index

- `style.md`
- `cast-list.md`
- `principal/ragna.md`
- `principal/tavin.md`
- `principal/sella.md`
- `principal/neri.md`
- `principal/orren.md`
- `principal/dorrik.md`
- `principal/merrok.md`
- `principal/ilva.md`
- `principal/harrow.md`
- `supporting-cast.md`
- `template.md`
