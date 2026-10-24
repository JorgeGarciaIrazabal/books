# Native integration audit — 2026-10-23

No confirmed actionable findings in the reviewed native integration. Keep the native Codex/OpenCode definitions and shared Markdown contracts as the architecture; this assessment provides no reason to add a Python runtime layer.

This was an independent first assessment. Prior setup consultation and review reports were not read. No paid model calls, child agents, configuration edits, global trust changes, model downloads, or publication actions were performed. The sole intentional workspace write is this report.

## Checks and evidence

- Installed CLIs report `codex-cli 0.163.0` and `opencode v2.1.4`, matching `docs/tooling.md:3`.
- Parsed every `.codex/agents/*.toml` using Python's standard TOML parser. All 16 IDs, descriptions, models, reasoning levels, and referenced shared contract paths match `.studio/roster.json`; every referenced contract exists.
- Ran `opencode debug agents`, then compared its resolved registry against all 16 roster entries. Every expected role resolves with the stated model, description, shared contract reference, mode, and 40-step cap. The director is primary; the other 15 roles are subagents. All specialists deny further subagent delegation; the four reviewer roles also deny `edit` and `shell`.
- `opencode debug config` identifies this repository's `opencode.json` and `.opencode/` among its configuration sources. Global config also participates; this audit printed only source paths, not credential values.
- `opencode models` lists both `ollama/kimi-k3:cloud` and `ollama/mistral-large-4:cloud`. `ollama list` independently lists both cloud tags. This establishes discovery, not successful inference.
- `codex debug models --bundled` includes `gpt-6-astra` and supports both `medium` and `high` reasoning used here. This does not establish account entitlement.
- `codex debug prompt-input` exits successfully and includes the root Book Studio instructions. This output does not establish the effective main model or custom-role selector availability. The explicit limitation in `docs/tooling.md:45` is therefore appropriate; no native role selection was fabricated.
- Inspected all eight OpenCode command definitions: each targets `studio_director`, substitutes `$ARGUMENTS`, and uses the documented Markdown format. They are prompt shortcuts; they contain no custom execution engine or embedded shell blocks.
- Reviewed the shared role contracts for delegation, assignment scope, reviewer independence, and ownership. The four reviewers exclude handoff, outline, rationale, and prior verdicts from initial assessment. The creator/reviewer distinctions match the roster and native definitions. No model/role/path drift was found.

The standalone Codex agent format and inherited permissions match [official OpenAI subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents). The three-child setting excludes the primary thread, consistent with `docs/tooling.md:30` and the [configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).

The OpenCode modes, agent directories, and Markdown fields match [v2 agent documentation](https://opencode.ai/v2/docs/agents/). The deny actions cover built-in writes and shell use as documented in [v2 permissions](https://opencode.ai/v2/docs/permissions/). Command metadata and argument expansion match [v2 commands](https://opencode.ai/v2/docs/commands/); Ollama discovery and provider IDs match [v2 models](https://opencode.ai/v2/docs/models/).

## Limitations and next verification

No end-to-end drafting, specialist delegation, independent review, or handoff cycle was exercised. CLI metadata and configuration compatibility cannot establish editorial quality, account access, quota, or tool-use reliability. Historical consultation claims in README/tooling remain deliberately unassessed because inspecting earlier consultations would violate this fresh-review assignment.

Codex reviewer restrictions are instructions, as the documentation correctly discloses. OpenCode's current reviewer rules deny built-in edit/shell/delegation actions; they are not a universal restriction on arbitrary future MCP/plugin tools, whose actions have separate permission names. No connected-tool mutation bypass was tested or observed. Assignment write scopes and the no-recursion/three-child convention remain partly behavioral policies, not general filesystem confinement.

Shared contract references are instructions to read a path, not automatic content inclusion. They resolve from the documented repository-root startup. The observed registry proves the reference text was loaded, not that a model subsequently obeyed it.

The next useful verification is a small, explicitly authorized native writing cycle with a creator and a fresh reviewer, retaining exact role/model/tool evidence and the resulting handoff. This would test practical behavior without replacing runtime integration. No such model call is needed merely to repair a proven configuration defect, because none was found here.

## Snapshot and coverage

The inventory below covers all native files, command files, shared role contracts, roster, root instructions, workflow, and README/tooling documentation inspected for this audit. Contract review focused on the integration-facing assignment/ownership/independence provisions; it is not a certification of every specialist's editorial craft. Other reports, books, helper internals, production output, and global credential/trust contents were not assessed.

Inventory SHA-256 (SHA-256 of the exact `hash  path\n` entries below): `025185873cb5b97490c9ef890b92b6100850263f2e8954b637d159cf5cca32f1`.

```text
10da39471cd9438f29c6fd3e70153afa0cdd9dbc859b1ed985c1b0b111059a11  .codex/agents/acquisitions_editor.toml
340a0494ffe98a1687ad0acd0ddb0d1679450e7fb34c2c4135b8700e068e3ede  .codex/agents/art_director.toml
4f97a3d7f4516962647400fa8ecbf36cd5de69532e1d6699ebd1fa927511e734  .codex/agents/canon_keeper.toml
7b3b7375cfd7eb37c09c8fd0f6cd4fd67350868ce3079544cbffb5f5cf66e2a2  .codex/agents/character_director.toml
de1ea4e719bcecd28a7f9dd7643050633f5c432786ac19f4dd31d65eb56d8f73  .codex/agents/copy_editor.toml
53e5e2ab5d074f5bda6b170177d91f4896283cfbd1886ffbb67c581e4d4a0c9b  .codex/agents/developmental_editor.toml
d700d641aff9002a0239cb464ae0dfa879cc3f8d9c2d2058a9288e3a6cdd09dc  .codex/agents/drafter.toml
b216d9d6115327af06fc911fa23c781a99ee311d101b2238d60667ae66d53190  .codex/agents/line_editor.toml
3551299e29ef1f5e88126de6399bcc0ab5345d4d27fb131a3d71b36d1e4f1ce9  .codex/agents/nonfiction_editor.toml
7f431a06e9a43b8cb63a37cbae2d938bf95579b4087c151187570d10fd924bce  .codex/agents/production_editor.toml
8d04275c846bf85355e7bfe4b1b65c3d170887d905d9dc01b54876e6e8ec176d  .codex/agents/reader_advocate.toml
5f55122d116c0fbe4503cbde37d6d2c1328ebfafe91779959d7ad45b48a6b3ea  .codex/agents/researcher.toml
88be32a239a4df2fa2fb5d1672ffb588293698aa8bd615e5f17d939d592c8491  .codex/agents/series_showrunner.toml
b2434662cae189d87232a2019311cf162296df99a9e18dfc1cef3e94114e0953  .codex/agents/story_architect.toml
cde36c6040121878bff1f1aa921cd9e39b2bf3a7ce7429ef71b13cc99f7c2340  .codex/agents/studio_director.toml
89b0fcdb16f8c3775d5ebdaabd0ecbda4f1409c9e9be86f9b34376b1b97363be  .codex/agents/universe_architect.toml
c6e02d3e16be38ff3358a1d6a1ee154ec1a6d6787dff029212f32427d5e0c0e9  .codex/config.toml
6231cd2ee047fbcfbc2fb7dfb9baa4b57e81e9e5a782b6f8601f7e0bd233aeea  .opencode/agents/acquisitions_editor.md
dcaf4a47c57b5252f9adf66f00341f9307144e684ac73551cfe4b82dbd7de98f  .opencode/agents/art_director.md
43278ef0e6de0e39bf9c3a775b4c47a7cd254c6f5fcf18fbd605aae7638f548c  .opencode/agents/canon_keeper.md
b984d21d8cda11d6dc1149eee21a572efce3df15e2f2551b654161d1fb297b4b  .opencode/agents/character_director.md
2125580c7892cc0aa9ed02b77e92938ba5beb92a6584ed407190edd8bdd0daad  .opencode/agents/copy_editor.md
19e205e8b0be98937c8e1a156d774b2f6a264a00977f4da8485f2247cf5f2311  .opencode/agents/developmental_editor.md
3cf09b5d8d152a68bcfecab903faf712adc57c36d8fea92fb72c427565ae25e2  .opencode/agents/drafter.md
10e0444fbd24c27d3a954a2efc3def748439e7b8d36dcc33c5b26b0a8f253bf7  .opencode/agents/line_editor.md
e00daf82a31e4f9d8e9500beaa110c300a643527a2b8169e3c41ea2bd2062e36  .opencode/agents/nonfiction_editor.md
11caf314e4ceeb7833b46683fab404d575873594ab001e435f2e0bba68089201  .opencode/agents/production_editor.md
4a102ce5086b49d0e1ae2e7833d2a7f44c6f71ca675fc120415561b3f06221ab  .opencode/agents/reader_advocate.md
70fddb6cb9d3f9e4a9f6c5701e0c4a82e0856b766d7640ed8e120c5696c8e779  .opencode/agents/researcher.md
1a27ab320292df618f251a8344545144e673a541736fe2fb23e296537d0ee769  .opencode/agents/series_showrunner.md
6a70f0d29611ab87ed669eab3316f829d8f6beccf670cb939153b87a8a0925e8  .opencode/agents/story_architect.md
2cf4493b5e868b7634ec7607739dd6cef033387a2b6cbf078908f230b3e44406  .opencode/agents/studio_director.md
ff0e4ae305294b71a6dc182547e731e31f174dcf273da2bd26a7d6f1c292a9e2  .opencode/agents/universe_architect.md
88153fc5ad58c096979c41b8b2e822be07cf6a6bf89d0a12d6da1d853d74ba41  .opencode/commands/studio-canon.md
fb7bf3c9ac4836a1444247d606ac3faabf24934dc1a0a9f76daab6ef892509ec  .opencode/commands/studio-debate.md
65770131c1b6e5971f5edf395e339dc8fea8ccdcab7cc06195c4b605514f6a0e  .opencode/commands/studio-draft.md
dd587dfe55d8dff5417c6f82d580009412bec2adfe51dd6c8140f54060a38a56  .opencode/commands/studio-plan.md
d0d3e597dd1561001be7b23b47bdf6318d68a0fe6a90bd1348447f45baaf1b86  .opencode/commands/studio-release.md
80f695a8a45ebdd271642e6ea7a6ce13c2f1839e0e38c8def8cec8ae5f83fcbc  .opencode/commands/studio-resume.md
144e3a83bf57e5f0a889211e5f1cb75758001fbf709db6512445464703194266  .opencode/commands/studio-review.md
87fb233629083ac072630875dcc0dafd8e00cda4e2a0e768ad645f2c2aa84ce6  .opencode/commands/studio-start.md
226f7896441dea91e734502fafc6c8af17bcbe1979b880770f19d10066312c44  .studio/agents/acquisitions_editor.md
ff6ff518e5883f9d9e23b28a99f4a5d3f5fa43e4ef698683b6d00f0e5f631707  .studio/agents/art_director.md
bf315922deec494478a95d61ba3426b5626efc65c8b844976fe851a41ebcd191  .studio/agents/canon_keeper.md
d5a93d736442e58bb264d049803758f0f85d6eae1ae11020b3f1fef624aa732d  .studio/agents/character_director.md
6e7b2c5e61d132f2a45ec3d063c3dc7693a406ec5f749e5e63a4116dafccf399  .studio/agents/copy_editor.md
d0a60b784c86041f7e63b8795e65a7aed4d1c781e1fa03840ab500e0d17d2f2e  .studio/agents/developmental_editor.md
429fca1135efd01207de3394116aeae5c0c282a0c0e90e091fd5539f31d78c2a  .studio/agents/drafter.md
3aaf71bfdc3efffb0ff8363102c09962eaf9cef165f534f135fbf78d2727da2d  .studio/agents/line_editor.md
5fcc8b9425fdb2ee0023753c1ed73bb7b79fdbb94c364a80ce4bd6617f6fffe6  .studio/agents/nonfiction_editor.md
adaf2cf36368902309e19278b9306d66c3f3a62756a325709eb5baab828af9fb  .studio/agents/production_editor.md
23eff3150a8de8eadd8814eb7b6b93f4fccc65ad3478be302e2463d2963cad89  .studio/agents/reader_advocate.md
9c0480ff2d1957d4c489474c58e38c842c8c365ccc2b4130f1c2a46b233ee532  .studio/agents/researcher.md
41589c00908e0d5b9f4b47e032de22de36b76cfc056f38cddc0d091ace9bc9a1  .studio/agents/series_showrunner.md
edd60d5950d92e684bdc75e497ad1cda0562478faa09dfdcb7dddfa2121adcb6  .studio/agents/story_architect.md
0511f9b8a922697f53634728c97c92b3d3d491190a38be3486888d99759ed315  .studio/agents/studio_director.md
a91c1f49b4cd9589c2978d3f5ce13e28644f80c5dabddc658f3092075269414d  .studio/agents/universe_architect.md
75e9edd073fefde194a636b837d511dc1f5244c613d6475cedcc14766c4d1ec4  .studio/roster.json
f8dacd16a2b3a37720b7a9fad23dff0dccdc63a1912e51c742ca0fa9018f9967  .studio/workflow.md
38423e37183fb9dcf5c6e0a76c795807bf7aa63def64ba18493d4ffb85962900  AGENTS.md
43562c56c388953f6296715b7a460e3566e9cbbd3190fbaf9edaf34c5691df79  README.md
83bb5a344e9a96a3c2bab52281c46c0b405da124f6382f4c2f76bf99ee12f869  docs/tooling.md
7b4ce0ac5b4012f141f1f993916d4fa47056d97ea9bec2b74f42f0f8c2d1f17d  opencode.json
```
