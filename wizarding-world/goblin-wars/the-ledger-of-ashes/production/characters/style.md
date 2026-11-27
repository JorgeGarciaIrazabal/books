# Character art: shared style and prompts

These are production prompts for trailer-only character reference art. The appearances below are visual proposals, not manuscript canon.

**The character sheets already contain these blocks inline.** Each character prompt is standalone: it includes the shared style, and the negative prompt follows it. This file is the source of truth if you want to edit the shared style or reuse it for a new character. If you change a block here, do the same find-and-replace across `principal/` and `supporting-cast.md`, because each sheet carries its own copy.

## How to assemble a new prompt

`[CHARACTER PROMPT] + [SHEET_STYLE or CINEMATIC_STYLE] + [NEGATIVE]`

Use `SHEET_STYLE` for turnarounds and expression sheets. Use `CINEMATIC_STYLE` for portraits, prop/detail sheets and trailer stills.

## Sheet style

```text
Neutral warm-grey seamless background, soft even studio light, 1752 historical fantasy, live-action cinematic realism, 35mm film, fine grain, muted umber and slate palette with ember-orange accents, production-design realism, no text.
```

## Cinematic style

```text
Grounded 1752 historical fantasy thriller, live-action cinematic still, 35mm film, anamorphic widescreen, natural lamp and candle light, soot-black shadows, wet stone, brass, iron, parchment and ink textures, muted umber and slate palette with ember-orange highlights, fine grain, shallow depth of field, production-design realism, no glossy CGI.
```

## Negative prompt

```text
text, letters, watermark, logo, modern clothing, wristwatch, electric light, plastic, cartoon, anime, comic, glossy CGI, superhero pose, neon, lens flare, oversaturated, deformed hands, extra fingers, recognizable Harry Potter characters, Hogwarts, wizarding-world logos, antisemitic caricature, hooked nose, greed imagery, grotesque teeth, duplicate faces, mismatched eyes
```

## Goblin design rule

Naturalistic, dignified goblin design. Broad cheekbones, long pointed ears, strong noses, weathered skin, 18th-century working clothes. They should look like a distinct, self-possessed people with an economy and a culture, not a gag or a caricature. Never use hooked noses, exaggerated greed, or grotesque teeth.

Goblin height range is roughly 4 ft 4 to 4 ft 10. Builds vary: compact, lanky, heavy-shouldered, wiry. Skin tones range from olive-brown and warm ochre to deep umber and grey-brown. Eyes are amber, dark brown, hazel or grey. Hair is black, brown, auburn or iron-grey.

## Human design rule

Humans are tall and grounded, 5 ft 6 to 6 ft 2. No superhero physiques. Faces should look lived-in. Ministry wizards are austere, not theatrical: dark travelling cloaks, high collars, dark suits, polished boots, silver wand clips. No Hogwarts robes, no house colours, no modern fashion.

## 1752 clothing rule

Goblins wear working clothes: linen shirts, waistcoats, dark work coats, leather aprons, clogs or sturdy boots, tool belts, neckerchiefs, caps. Bank officials wear dark frock coats, cravats, watch chains and silver spectacles. Ministry wizards wear black travelling cloaks over dark suits. Everything is worn, mended, soot-stained or rain-damp unless the character is meant to look immaculate.

## Reference workflow

1. Generate a four-view turnaround for one character at a time. Do not put the whole cast in one image; the model will blend their faces.
2. Pick the cleanest front view. Use it as the image reference for every later generation of that character.
3. Generate the expression sheet from the same front view, then the cinematic portrait.
4. Keep the same seed and reference image for every prompt in that character's file.
5. Generate a separate prop sheet for signature objects: keys, cups, tools, spectacles, seals.
6. Use the cinematic portrait as the reference for the trailer shot prompts.

## Continuity rules

- The locked visual token is the contract. Do not paraphrase it between shots.
- Keep height, build, skin tone, hair, costume and signature prop identical.
- Change only expression, pose, lighting and camera.
- If a generation drifts, discard it. Do not "fix it in the edit."
- Every character sheet is a proposal, not canon. Do not add scars, tattoos or backstory. Keep jewelry minimal and only where the sheet specifies it.
