# Runtime integration

Setup inspected **Codex CLI 0.163.0**, **OpenCode v2.1.4**, Python 3.13.7, and the
local Ollama service on 2026-10-23. Native config and role loading were checked as
recorded in the setup review. Recheck versions and model inventory when upgrading.

## Shared contracts, native definitions

`.studio/agents/*.md` contains the portable role instructions.
`.studio/roster.json` records IDs, descriptions, role kinds, and model assignments.
The runtime definitions reference those Markdown contracts directly:

- `.codex/agents/*.toml`: standalone custom agents with `name`, `description`,
  `developer_instructions`, and per-role model/reasoning settings.
- `.opencode/agents/*.md`: Markdown agents with v2 `mode`, `model`, `steps`,
  and ordered `permissions`. The director is primary; the others are subagents.

Edit shared role behavior in `.studio/agents/ROLE.md`. If changing a model, ID, or
permissions, update the corresponding native definition and roster entry. Codex
and OpenCode own agent execution and orchestration. There is no Python integration,
model proxy, launcher, workflow engine, or extra background service in this project.

The formats follow [Codex custom-agent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents)
and [OpenCode v2 agents](https://opencode.ai/v2/docs/agents/).
Project configuration follows [Codex configuration](https://learn.chatgpt.com/docs/config-file/config-basic)
and [OpenCode v2 configuration](https://opencode.ai/v2/docs/config/).

## Codex

Launch `codex` at repository root. Project `.codex/config.toml` defaults to GPT-6.1 Sol high and a
maximum of three concurrent child sessions. Ask the coordinator to use a specialist
by its ID, for example `story_architect` or `canon_keeper`. Project config applies
only when the project is trusted; keep trust and provider settings in your normal
Codex account configuration. This repository does not change global settings.

For a one-off main session, `codex -m gpt-6.1-sol` makes the model explicit.
Inspect the local catalog rather than guessing availability. `codex debug models`
can be very verbose; it includes model metadata, not just names.

Codex custom agents inherit parent permissions and providers. The contracts make
independent reviewers read-only by instruction; that is **not a filesystem sandbox**.
Use a read-only session/worktree arrangement when enforced isolation is required.
No role file claims to override Codex's inherited sandbox or authentication.

The current session exposed the named custom roles with their updated model and
effort definitions. Use that selector when available. If another client exposes
only generic native delegation, assign the role contract and explicitly request
the model and effort from `.studio/roster.json`; do not claim that a named native
role was selected. A task-effort override in the roster is coordinator guidance,
not an automatic runtime switch. Premise development needs an explicit high-effort
invocation rather than the acquisitions role's medium default. Report an unavailable
route instead of silently substituting another model.

See [the phase table](model-routing.md) for current choices, retained untested
specialties, and same-model review limitations. Start a fresh main session to pick
up project defaults; existing sessions can retain their selected model.

## OpenCode 2.x

`opencode.json` selects `studio_director` and the local Ollama Kimi cloud route for
new sessions. In an existing session, its stored model may take precedence; use
`/models` to inspect or select it. Ask the primary agent to launch the named
specialists, for example “Use the developmental_editor subagent on this chapter.”

OpenCode v2 uses `permissions` arrays with `shell` and `subagent` actions, rather
than v1 `permission`, `bash`, and `task` configuration. The native reviewer
agents deny edits, shell commands, and further delegation. They can use local
read/search and web tools. Other specialists deny recursive delegation and retain
the runtime's normal editing capabilities within the assignment's write scope.
The coordinator serializes updates to shared ledgers. See
[OpenCode v2 permissions](https://opencode.ai/v2/docs/permissions/).

OpenCode [discovers Ollama models](https://opencode.ai/v2/docs/models/) from the
local service. Exact project IDs are `ollama/kimi-k3:cloud` and
`ollama/mistral-large-4:cloud`; the `ollama-cloud/…` provider is a different route
and is not silently substituted. Check `opencode models` and
`opencode debug agents` after changing routing. If that command reports an empty
registry because the service is scoped to another directory, inspect the project
explicitly without inference:

```bash
opencode api agent.list -H "x-opencode-directory:/absolute/path/to/books"
```

For the author-requested GitHub Pages implementation, OpenCode used the explicit
`ollama/glm-5.3:cloud#low` override. Project configuration exposes the model's
supported low/high/max variants without changing the studio's default routes.
On 2026-10-25, Ollama `/api/show` reported `max` as GLM's default; the initial
default-effort inference was interrupted after a prolonged pause before any
implementation edits. Session evidence and actual checks are recorded under
`.studio/reviews/github-pages-2026-10-25/`.

The adoption check used this API with the actual repository path and verified all
16 studio roles. Preferred OpenRouter Sol routes remain metadata only: a native
probe returned HTTP 403 because the connected key had reached its spending cap.
The active routes are the explicit Ollama `#high` variants in the native files.
For another Ollama host, use v2
`providers.ollama.settings.baseURL`, as documented there.

The OpenAI-compatible Ollama endpoint uses `body.reasoning_effort`. Its native
`think` option was ineffective on this route. Project variants use Kimi low/high/max
and Mistral none/high; there is no verified medium setting for either. The author
accepted Kimi low/high and Mistral's supported equivalents for the experiment.
Direct and native probes establish the corrected control, not a completed quality
comparison. See [the runtime correction](../.studio/experiments/instruction-ablation-v1/runtime-control-correction.md).

Custom [OpenCode commands](https://opencode.ai/v2/docs/commands/) live in
`.opencode/commands/`. They send scoped prompts to the director; they are not a
background scheduler or a second orchestration engine. Pass the book path first,
then the task. E.g. `/studio-draft glass-sea/tidebound/book-01 opening scene`.

## Ollama and model discussion

The requested “Mistral large V4” resolves to the official
[Mistral Large 4 cloud tag](https://ollama.com/library/mistral-large-4).
`kimi-k3:cloud` was already registered; setup registered the Mistral cloud tag too.
No large local weights were downloaded for that cloud tag. The local inventory
alone does not prove inference, credentials, or quota availability. Setup's actual
consultation reports supply inference evidence. Repeat discussions with native
Codex/OpenCode agents; write the question, inputs, and responses to review files.
The consultation text is advice, not canon or trusted tool documentation.

## Practical limits

`check` validates identity/path layout, required records, IDs, chapter references,
and claim-source links. It is deliberately not a full ontology or literary grader.
Manual editorial work must verify knowledge boundaries, plot logic, factual truth,
review coverage, rights, and exported formatting. See `docs/records.md`.

`packet` hashes included files, omits whole files over budget, and lists omissions.
Its character limit is not an exact token counter and its default inputs are not
automatically spoiler-safe. Select task-relevant canon, state, and source excerpts.
For an independent initial manuscript assessment, `packet --mode review` excludes
handoff and planning outline; add manuscript files explicitly with `--include`.
For an explicit structure review, include the outline as the target instead and
leave manuscript execution unassessed. Do not add prior verdicts to either pass.

`build` assembles chapters as-is without deleting headings, front matter, or notes.
The author/production editor decides which source files belong in chapter order.
It records hashes and calls editorial status unverified. Generated exports may be
overwritten only with `--replace`; source chapters are never build targets.
The export directory must be a real directory. Both targets are checked before
writing, and an ordinary write failure restores any previous output/manifest pair.
The manifest is written last; an interrupted process or power loss still requires
checking its output hash before using the export. Assembly hashes the captured
source bytes, rather than rereading files later for their hashes. Keep the assigned
source files stable during a build; this is not a live-edit snapshot across writers.
