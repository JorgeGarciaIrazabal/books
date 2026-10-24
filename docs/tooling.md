# Runtime integration

Setup inspected **Codex CLI 0.163.0**, **OpenCode v2.1.4**, Python 3.13.7, and the
local Ollama service on 2026-10-23. Native config and role loading were checked as
recorded in the setup review. Recheck versions and model inventory when upgrading.

## Shared contracts, native definitions

`.studio/agents/*.md` contains the portable role instructions.
`.studio/roster.json` records IDs, descriptions, role kinds, and model assignments.
The runtime definitions reference those Markdown contracts directly:

- `.codex/agents/*.toml`: standalone custom agents with `name`, `description`,
  `developer_instructions`, and Astra model/reasoning settings.
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

Launch `codex` at repository root. Project `.codex/config.toml` uses Astra and a
maximum of three concurrent child sessions. Ask the coordinator to use a specialist
by its ID, for example `story_architect` or `canon_keeper`. Project config applies
only when the project is trusted; keep trust and provider settings in your normal
Codex account configuration. This repository does not change global settings.

For a one-off main session, `codex -m gpt-6-astra` makes the model explicit.
Inspect the local catalog rather than guessing availability. `codex debug models`
can be very verbose; it includes model metadata, not just names.

Codex custom agents inherit parent permissions and providers. The contracts make
independent reviewers read-only by instruction; that is **not a filesystem sandbox**.
Use a read-only session/worktree arrangement when enforced isolation is required.
No role file claims to override Codex's inherited sandbox or authentication.

The tested `codex exec` session exposed native subagents without a custom-role
selector. Defining TOML files does not by itself prove that selector is available.
In that interface, the coordinator uses native delegation and explicitly assigns
the role: “Your role is nonfiction_editor; read `.studio/agents/nonfiction_editor.md`
and review these inputs using Astra.” This is a role assignment through native
task instructions, not a custom process or a claim that a TOML role was selected.
Use the native custom role directly when the client exposes that capability.

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
`opencode debug agents` after changing routing. For another Ollama host, use v2
`providers.ollama.settings.baseURL`, as documented there.

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
