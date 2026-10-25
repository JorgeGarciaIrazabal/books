# Book Studio

A professional writing workspace for original books, series, and shared universes.
Eighteen native specialist definitions share one set of Markdown contracts across
**Codex** and **OpenCode 2.x**. Those tools run and coordinate the agents; there is
no custom orchestration framework. The author sets the direction; agents plan, write, challenge,
revise, and prepare reviewable manuscripts.

Read [AGENTS.md](AGENTS.md) for the folder structure and operating rules,
[the workflow](.studio/workflow.md) for production, and
[craft standards](.studio/craft.md) for writing and editing.

## Start a book

Start Codex or OpenCode here and ask `studio_director` to create your
`{universe}/{series}/{book}` workspace from `templates/`. Native agents can copy
the needed templates, replace placeholders, and register book order directly.

For optional file-helper commands, use Python 3.11 or newer; no third-party
dependencies are needed:

```bash
python3 tools/studio.py new glass-sea tidebound book-01 --title "The Glass Harbor"
python3 tools/studio.py check glass-sea/tidebound/book-01
```

This creates `glass-sea/tidebound/book-01/`, including shared universe and series
records. The example is a command, not an invented book already in your library.
Existing shared records are preserved. Use `--dry-run` to inspect planned files.
Use `--kind nonfiction` for factual books and `standalone` as the series slug for
a standalone. Slugs are lowercase kebab-case; titles can use ordinary typography.

Start either tool **from this repository root** so the project agents are available:

```bash
codex
opencode
```

Then give it a concrete instruction, for example:

> Act as studio_director for glass-sea/tidebound/book-01. Develop a literary nautical
> mystery for adult readers, with a grieving cartographer as the viewpoint character.
> Fill the brief using labeled assumptions, plan one opening scene, draft it, and
> use reader_advocate for an independent response. Leave a handoff.

Normal work uses a director, a creator, and a reviewer. Other specialists activate
for actual questions. You do not need sixteen concurrent agents or a filled lore
encyclopedia before writing. The scene or section is the practical unit of work.

## Models and runtime setup

- Codex: **GPT-6.1 Sol high** for direction, planning, drafting, line/copy editing,
  and continuity; **GPT-6.1 Sol medium** for developmental editing and blurbs.
  Premise development uses the acquisitions role's high-effort task override.
- Independent reader: **GPT-6 Sol high** in Codex.
- Research, nonfiction review, production, and art retain their existing Astra
  assignments because these specialties were not benchmarked.
- OpenCode currently uses **Ollama Kimi K3 high** and **Mistral Large 4 high**
  fallbacks. Its connected OpenRouter key has reached its spending cap, so the
  preferred Sol routes recorded in the roster are not active. The Mistral drafter
  receives a fresh Kimi reader response.

These are author-approved provisional choices from incomplete tests. The original
cloud effort comparisons were withdrawn after discovering an ineffective control;
corrected trials remain partial. See [model routing and evidence](docs/model-routing.md)
for the exact assignments and instruction changes. Both Ollama routes use cloud
inference through the local service. Account access and trust remain your settings.

```bash
ollama pull kimi-k3:cloud
ollama pull mistral-large-4:cloud
ollama list
opencode debug agents
```

The installed OpenCode v2 discovers Ollama at its default local address; existing
provider credentials stay outside the repository. No keys or machine-wide settings
are stored here. See [tooling notes](docs/tooling.md) for trust, compatibility,
model checks, and native invocation details.

## Everyday commands

```bash
# Inspect the workflow shortcuts inside OpenCode:
# /studio-start, /studio-plan, /studio-draft, /studio-review,
# /studio-canon, /studio-resume, /studio-debate, /studio-release

# Build a bounded packet. Extra paths are relative to the repository root.
python3 tools/studio.py packet glass-sea/tidebound/book-01 \
  --task "Plan the opening scene" \
  --include glass-sea/canon.json

# After writing, add chapter paths to book.json.chapters in the intended order.
# e.g. ["manuscript/001-opening.md", "manuscript/002-arrival.md"]
python3 tools/studio.py build glass-sea/tidebound/book-01 --name draft-01

# Structural checks and utility regression tests:
python3 tools/studio.py check
python3 -m unittest discover -s tests -v
```

Builds use only the explicit chapter order and produce Markdown plus a source-hash
manifest under the book's `exports/`. They do not certify literary quality or
produce a validated print/PDF/EPUB edition. Exports are ignored by Git; source
chapters and review records are the durable work. Add conversion tooling when an
actual format is needed.

See [record examples](docs/records.md) when populating canon, knowledge, evidence,
and editorial ledgers. Keep prose in Markdown and compact tracking records in JSON.
Use Git if desired (`git init`); the setup does not create commits or publish work.

The optional Python helper only scaffolds, checks, packages context, and assembles
book files. It does not run agents, choose models, or manage either runtime.

The [independent audit and resolutions](.studio/reviews/post-setup/README.md)
record the subsequent review, corrections, verification, and remaining limits.

## Illustrated stories

For a new illustrated story or pictures added to an existing book, use the [illustrated-story skill](.studio/skills/illustrated-story/SKILL.md) or OpenCode `/studio-illustrate`. Art direction, an illustrator, book design through production, and an independent illustration reviewer cover distinct parts of the work. The [illustrated-story guide](docs/illustrated-stories.md) explains the plan, references, actual-export proof and source-art records. Picture counts and page targets follow the individual brief. The skill's repository copy is the maintained source; a discoverable local installation can be copied into the current Codex skills directory when requested.
