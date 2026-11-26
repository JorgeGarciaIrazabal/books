# Decision history — Corporate Castle

## DEC-CC-0001: Adopt Tab 4 master canon as the authoritative baseline (superseding Cold Alchemy)
- **Date**: 2026-11-25
- **Question**: Source Google Doc `1HW7Fu6Ug32OM7qx7lF1E63ePWXa_6iTr3MPqXo0T3MY` contains four tabs spanning earlier drafts and a revised master canon (`Vocabulary`, `Latest Version`, `First Draft Version`, and `Tab 4`). Which canon rules govern `corporate-castle`?
- **Accepted choice**: Treat **Tab 4** (`t.k04gx9f8116z`) as the authoritative baseline: Lock the updated Prologue, remove **Cold Alchemy**, establish the **Two-Magic System** (Deep Magic split into Spirit vs. Institutional Insulation, plus Illusion Magic and Marissa's signature **Mirror Shield**), adopt the revised Marissa–Doctor Lois partnership-to-fracture engine, and preserve all non-conflicting lexicon from **Tab 1** (`Vocabulary`, `t.371ksllamqpd`). Treat Tabs 2 and 3 chapters as unfinalized reference drafts rather than accepted manuscript canon until harmonized.
- **Rationale**: User instructed creating the world and book based on the last version of the document while noting old and new drafts remain unfinalized. Tab 4 explicitly states it locks the updated master canon with Cold Alchemy removed and revised Chapters 1–2 beats.
- **Authority**: Author instruction (`2026-11-25`) synthesized by `studio_director`.
- **Affected paths**: `corporate-castle/bible.md`, `corporate-castle/glossary.md`, `corporate-castle/canon.json`, `corporate-castle/timeline.json`, `corporate-castle/characters/*.md`, `corporate-castle/standalone/the-hot-potato-of-corporate-castle/`.

## DEC-CC-0002: Standalone series path and working title (reversible)
- **Date**: 2026-11-25
- **Question**: Should Book 1 live under `corporate-castle/standalone/the-hot-potato-of-corporate-castle/` with working title *The Hot Potato of Corporate Castle*?
- **Accepted choice**: Use `corporate-castle/standalone/the-hot-potato-of-corporate-castle/` and working title *The Hot Potato of Corporate Castle* per repository convention for standalone books and the Google Doc's title. Marked explicitly reversible if the author chooses a different book title or multi-book series slug.
- **Authority**: Delegated coordinator assumption under `.studio/agents/studio_director.md`.
- **Affected paths**: `corporate-castle/standalone/series.json`, `corporate-castle/standalone/the-hot-potato-of-corporate-castle/book.json`, `brief.md`.

## DEC-CC-0003: Preserve Locked Prologue text faithfully; flag house-style punctuation and bolding for author decision
- **Date**: 2026-11-25
- **Question**: `.studio/craft.md` defaults to zero em dashes across the library unless the author grants an exception, whereas the author's Locked Prologue in Tab 4 uses em dashes (and Tab 2 also bolds in-world lexicon terms in body prose). How should we import the Locked Prologue?
- **Accepted choice**: Import Tab 4's Locked Prologue faithfully into `manuscript/000-prologue-the-hot-potato-of-corporate-castle.md` (which already drops the inline bolding used in Tab 2, while preserving the author's em dashes untouched), and explicitly ask the author whether new drafting/revision should follow `.studio/craft.md` (no em dashes) or grant a book-level exception.
- **Rationale**: `AGENTS.md` requires preserving user edits and never silently overriding author taste without checking.
- **Authority**: `studio_director` reversible assumption; pending author ruling.
- **Affected paths**: `corporate-castle/standalone/the-hot-potato-of-corporate-castle/style.md`, `manuscript/000-prologue-the-hot-potato-of-corporate-castle.md`.

## DEC-CC-0004: Fictionalization and privacy guardrail
- **Date**: 2026-11-25
- **Question**: The satire draws closely on realistic tech-company HR/ER/Legal dynamics. What privacy boundaries apply?
- **Accepted choice**: Keep all company names, executives, and matters strictly fictionalized inside Corporate Castle; do not introduce real-world employer names, identifiable real individuals, or confidential legal details. Keep all files local and uncommitted unless the author authorizes publishing or committing.
- **Authority**: Studio safety and publication guidelines (`AGENTS.md`).
- **Affected paths**: All files under `corporate-castle/`.

## DEC-CC-0005: Drop the King-throne mystery for High Lady Lexi and keep her departure grounded in disgust with upper court politics
- **Date**: 2026-11-25
- **Question**: Should the Prologue mention the King and plant a mystery secret beside the throne for High Lady Lexi's departure?
- **Accepted choice**: Remove explicit mention of the King from the Prologue and drop the secret-beside-the-throne mystery subplot. Show simply that standing so close to the upper court proved intolerable to anyone with a spark of Deep Magic, and disgusted at last, Lexi chose to walk away after securing Lois's Offline Oath. Bump `universe.json.canon_revision` from `1` to `2`.
- **Authority**: Explicit author instruction (`2026-11-25`).
- **Affected paths**: `corporate-castle/universe.json`, `bible.md`, `canon.json`, `timeline.json`, `glossary.md`, `characters/CHAR-0004-high-lady-lexi.md`, `characters/CHAR-0001-marissa.md`, `characters/CHAR-0003-sarai.md`, and Book 1 planning/manuscript files.

## DEC-CC-0006: Confirm zero em dashes across Corporate Castle (supersedes open query in DEC-CC-0003)
- **Date**: 2026-11-25
- **Question**: Keep em dashes from the Google Doc drafts or enforce `.studio/craft.md` (zero em dashes)?
- **Accepted choice**: Enforce **zero em dashes** (`—`), zero en dashes (`–`), and zero `--` stand-ins across all Corporate Castle manuscript prose, including a clean copy edit of the imported Prologue. Keep unbolded lexicon prose (following Tab 4).
- **Authority**: Explicit author instruction (`2026-11-25`: "i don't like em dashes").
- **Supersedes**: Open query in `DEC-CC-0003`.
- **Affected paths**: `corporate-castle/standalone/the-hot-potato-of-corporate-castle/style.md`, `manuscript/000-prologue-the-hot-potato-of-corporate-castle.md`.

## DEC-CC-0007: Liability's branch of Deep Magic is equally valid; Doctor Lois's failure is personal (contrasted with Sir Leo)
- **Date**: 2026-11-26
- **Question**: Should ER be framed as the only righteous way to practice Deep Magic, or is Liability Tower's discipline an equally valid calling?
- **Accepted choice**: Keep the Prologue line untouched (it speaks strictly to the ER Watch choosing to keep faith with Deep Magic against the theater of Vibes), and make clear across the rest of the book and canon that **nothing is wrong with the discipline of Liability as a branch of Deep Magic**. ER is Marissa's personal calling, not the sole legitimate path. Doctor Lois's fold upward is strictly a **personal failure of courage**, contrasted with **Sir Leo** (who practices Liability's craft with candor, while carrying his own personal foibles to be explored later). Bump `universe.json.canon_revision` from `2` to `3`.
- **Authority**: Explicit author instruction (`2026-11-26`).
- **Affected paths**: `corporate-castle/universe.json`, `bible.md`, `canon.json`, `glossary.md`, `characters/CHAR-0002-doctor-lois.md`, `characters/CHAR-0007-sir-leo.md`, `standalone/the-hot-potato-of-corporate-castle/manuscript/001-the-reluctant-steward.md`.


