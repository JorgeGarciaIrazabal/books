# Decision history — Garbanzo Family

## DEC-GF-0001: Standardize wife's name spelling as Marisa (reversible)
- **Date**: 2026-11-22
- **Question**: Source family profile records both `Marisa` and `Marissa` across historical notes without a settled spelling. Which spelling should Book Studio standardize on for `garbanzo-family`?
- **Accepted choice**: Use **Marisa** consistently across universe canon, character profiles, and Book 1 manuscript, while marking this spelling explicitly as a reversible author-confirmable assumption.
- **Rationale**: Consistent spelling prevents jarring mid-chapter shifts for readers; `Marisa` is the primary form used in the latest profile sections.
- **Alternatives**: Use `Marissa` globally, or prompt the author before drafting (rejected to preserve studio momentum on a straightforward, globally replaceable name choice).
- **Authority**: Delegated coordinator assumption under `.studio/agents/studio_director.md`.
- **Affected paths**: `garbanzo-family/bible.md`, `garbanzo-family/characters/CHAR-0002-marisa.md`, `garbanzo-family/standalone/the-quest-of-the-golden-garbanzo/`.

## DEC-GF-0002: Privacy boundary for real-world personal profile material
- **Date**: 2026-11-22
- **Question**: How should sensitive biographical material in the user's comprehensive archive be handled in this creative fantasy universe?
- **Accepted choice**: Celebrate family warmth, personalities, favorite hobbies (padel, DIY trades, local AI tinkering, unicorns, wizards, *cocido madrileño*), and cities/regions (New Jersey, Manhattan, Sierra de Guadarrama, Valladolid) while strictly excluding private medical episodes, legal/deposition details, exact street addresses, and real financial account identifiers/balances.
- **Rationale**: Protects family privacy in a keepsake story meant to be dramatic, joyful, and shared with a six-year-old.
- **Authority**: Studio privacy guardrail and creative brief.
- **Affected paths**: All files under `garbanzo-family/`.

## DEC-GF-0003: Poki's canonical appearance
- **Date**: 2026-11-22
- **Question**: How should late family cat Poki appear in magical family stories?
- **Accepted choice**: Poki appears tenderly as a sleek, dignified starlight companion with zero costumes of any kind (explicitly never a dragon costume).
- **Rationale**: Honors the author's explicit correction in the family profile.
- **Authority**: Author profile correction preserved in `FACT-0010`.
- **Affected paths**: `garbanzo-family/canon.json`, `garbanzo-family/characters/CHAR-0005-poki.md`.

## DEC-GF-0004: Private family keepsake publication status
- **Date**: 2026-11-22
- **Question**: Should *The Quest of the Golden Garbanzo* be published to the public `publications/` catalog or committed to Git automatically?
- **Accepted choice**: Keep the book private inside `garbanzo-family/` (do not modify `publications/` or commit/push to Git).
- **Rationale**: Respects repository publication boundaries and private family nature unless the author later chooses to publish or commit.
- **Authority**: Studio safety rules in `AGENTS.md`.

## DEC-GF-0005: Accept Book 1 story canon (`FACT-0015`..`FACT-0019`)
- **Date**: 2026-11-22
- **Question**: Should post-revision story outcomes from *The Quest of the Golden Garbanzo* (`PROP-0001`..`PROP-0005`) be promoted to `garbanzo-family/canon.json`?
- **Accepted choice**: Accept `FACT-0015` through `FACT-0019` into `garbanzo-family/canon.json` and increment `universe.json.canon_revision` from `1` to `2` after reconciling the windowsill gray stone vs. white backyard pebble in Chapters 4, 9, and 10.
- **Authority**: Director canon integration following blind continuity review (`reviews/whole-book-canon-audit.md`) and manuscript repair.
- **Affected paths**: `garbanzo-family/universe.json`, `garbanzo-family/canon.json`, `garbanzo-family/standalone/the-quest-of-the-golden-garbanzo/canon/proposals.json`.

## DEC-GF-0006: Confirm wife's canonical name as Marissa (supersedes DEC-GF-0001)
- **Date**: 2026-11-22
- **Question**: Author explicitly confirmed `"wife name is Marissa"`. Update universe and Book 1 accordingly?
- **Accepted choice**: Adopt **Marissa** canonically across all active `garbanzo-family` universe records, character profiles (`CHAR-0002-marissa.md`, replacing `CHAR-0002-marisa.md`), and Book 1 planning/manuscript/export files; bump `universe.json.canon_revision` from `2` to `3`. Preserve historical `DEC-GF-0001` and blind review archives untouched.
- **Authority**: Explicit author instruction (`2026-11-22`).
- **Supersedes**: `DEC-GF-0001`.
- **Affected paths**: `garbanzo-family/universe.json`, `garbanzo-family/bible.md`, `garbanzo-family/glossary.md`, `garbanzo-family/canon.json`, `garbanzo-family/timeline.json`, `garbanzo-family/characters/*.md`, `garbanzo-family/standalone/bible.md`, `garbanzo-family/standalone/the-quest-of-the-golden-garbanzo/`.

## DEC-GF-0007: Authorize public release and audiobook on GitHub Pages (supersedes DEC-GF-0004 for Book 1)
- **Date**: 2026-11-23
- **Question**: Author asked `"can you push is and release it? with the audio too?"`. Should Book 1 be published to `publications/`, `site/`, and pushed to `origin/main`?
- **Accepted choice**: Publish *The Quest of the Golden Garbanzo* (reflowable EPUB 3, 32-page reading PDF, 720×1080 cover JPEG, and 10-chapter synthetic MP3 audiobook) to the GitHub Pages catalog and push cleanly to `origin/main`.
- **Authority**: Explicit author release instruction (`2026-11-23`).
- **Supersedes**: `DEC-GF-0004` (for Book 1 release scope).
- **Affected paths**: `publications/`, `site/index.html`, `site/audiobook-the-quest-of-the-golden-garbanzo.html`, `site/audio/the-quest-of-the-golden-garbanzo/`, `garbanzo-family/standalone/the-quest-of-the-golden-garbanzo/`.

## DEC-GF-0008: Ground Garbanzo Family in ordinary human life with light magic and easy prose
- **Date**: 2026-11-23
- **Question**: Author requested making the book less magical so the family remain ordinary humans, lowering the reading level so it is easy to read and follow (less dense), while keeping it fun and dramatic (`Do a full rewrite of the whole book`).
- **Accepted choice**: Rewrite *The Quest of the Golden Garbanzo* and update active `garbanzo-family` canon to revision 4 around real human life in New Jersey, Manhattan, and Spain, keeping magic warm, simple, and strictly limited to three elements: (1) the lucky Golden Garbanzo chickpea in the kitchen copper pot, (2) Garbanzo the chickpea-shaped desk-bot, and (3) sleek, costume-free Poki's quiet starlight visits. Remove all heavy allegorical fantasy apparatus (Citadel, Tax Hydra, Mirage Brokers, Loom, Brass Scale, Living Compass, Cadastral Spectacles, Sky-Portal, Padelsword).
- **Rationale**: Keeps characters clearly human, eliminates dense capitalized terminology, and lowers the prose to crisp, vivid Grade 5–6 read-aloud English without losing the humor, emotion, or stakes.
- **Authority**: Explicit author instruction (`2026-11-23`).
- **Affected paths**: `garbanzo-family/universe.json`, `bible.md`, `glossary.md`, `canon.json`, `timeline.json`, `characters/*.md`, `standalone/{bible,roadmap}.md`, and `standalone/the-quest-of-the-golden-garbanzo/`.
