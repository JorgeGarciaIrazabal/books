# Independent editorial-system audit

Date: 2026-10-23. Reviewer: native Codex child assigned an independent editorial-system audit; no external model consultation or additional agents.

## Assessment

The studio is usable for a first sample and provides substantive guidance for fiction, nonfiction, and shared universes. The existing roles cover the requested work; no added role is justified. The craft rules protect voice, agency, subtext, fair payoff, and evidence rather than imposing numeric quality scores or a rigid plot. Canon proposals, accepted facts, attributed beliefs, chronological state, cross-book promises, and claim-level verification are meaningfully distinguished. Empty optional records and the one-unit writing loop keep the initial administrative burden proportionate.

Two instruction conflicts should be repaired before relying on independent checkpoints. These findings concern the instructions themselves, not an observed contaminated review or a claim about runtime behavior.

## Findings

### 1. Major: the generated book instructions contaminate fresh reviews

Evidence: `templates/book/AGENTS.md:2` unconditionally tells every book-scoped agent to read `handoff.md` and relevant outline records. Its review sentence at line 5 does not make an exception. This conflicts with `AGENTS.md:17`, `.studio/workflow.md:81`, and the independent reviewer contracts, such as `.studio/agents/developmental_editor.md:7`, which explicitly withhold handoff and outline on an initial manuscript assessment.

Failure scenario: the director requests a fresh reader response to the first opening chapter. The reader follows the nearest book instructions, opens the handoff containing the drafter's explanation and intended twist, then reports comprehension or surprise using information the actual opening never supplied. Sending a clean packet alone cannot prevent this if the agent also obeys the generated AGENTS file.

Smallest fix: add the same explicit initial-review exception to the book template, directing independent reviewers to the brief, actual review target, necessary constraints, and chapter order while withholding handoff, rationale, and prior verdicts. Preserve normal handoff/outline loading for creation and integration. If generated books exist, patch their corresponding instruction files too.

### 2. Moderate: the outline checkpoint conflicts with the reviewers' ban on reading outlines

Evidence: `.studio/workflow.md:16` assigns the structure checkpoint to the architect plus an independent developmental/nonfiction editor. But `.studio/agents/developmental_editor.md:7` and `.studio/agents/nonfiction_editor.md:7` prohibit reading an outline for an independent initial assessment; their specialty instructions at line 11 assume actual manuscript text. `.studio/workflow.md:81` likewise describes only an independent manuscript-review packet.

Failure scenario: after the first-book outline is written and before full drafting, the director assigns the documented structure check. A literal reviewer declines to read the outline, assesses only the brief, or silently disregards its own contract. The checkpoint then lacks a clear distinction between evaluating a proposed causal/argument structure and determining whether the eventual manuscript actually achieves it.

Smallest fix: distinguish two review targets in workflow and both contracts. For an explicitly assigned outline/structure review, the outline or scene contracts are the actual target and may be read; the report must say that execution, pacing in prose, and an earned ending remain unassessed. For a fresh manuscript review, continue withholding the outline and the drafter's defense. No new agent or new ledger is needed.

## Coverage and limitations

Read in full: root AGENTS.md and README.md; .studio/workflow.md and .studio/craft.md; all sixteen .studio/agents/*.md contracts; every template file, including all JSON scaffolds; docs/records.md. Reviewed role boundaries, creative guidance, proposed versus accepted facts, beliefs and disclosures, state chronology, series promises, independent review, nonfiction evidence, and first-book workflow. The JSON templates deliberately contain empty arrays; the richer examples are editorial conventions rather than a fully enforced schema, and the documentation states that limitation accurately.

Not assessed: native adapter correctness, model availability, helper implementation, mechanical validation behavior, production conversion tools, or actual book-length performance. No new manuscript, live multi-agent writing run, nonfiction source verification, or release candidate was produced. Prior setup reports, consultations, and fixture verdicts were not read. Remaining risks of poor prose or missed continuity cannot be resolved by configuration inspection alone.

Next action: reconcile the two review-loading rules, then exercise the first-book outline check and fresh manuscript check with clearly separated inputs. The parent owns integration and shared handoffs; this reviewer changed only this report.

## Source inventory

SHA-256 inventory captured after the reads (source files were not edited by this reviewer):

```text
38423e37183fb9dcf5c6e0a76c795807bf7aa63def64ba18493d4ffb85962900  AGENTS.md
43562c56c388953f6296715b7a460e3566e9cbbd3190fbaf9edaf34c5691df79  README.md
f8dacd16a2b3a37720b7a9fad23dff0dccdc63a1912e51c742ca0fa9018f9967  .studio/workflow.md
1b8eac06977488d587b7c08dece2fedd7e948e8ce9160f67701e6d62d2f3ef20  .studio/craft.md
9392057b7441038401804414973ae729a34c6ffa6d219b20482e3f140deb862d  docs/records.md
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
641a4b0efcee87ebda2092f74cb0d71276ea7752b9c9dd334e9e95a451017c9f  templates/book/AGENTS.md
53b40bb13ec856256e805e83ec98a714cb5c52bba44751f2afa8c13582b2a9d3  templates/book/book.json
2b7e7a7d0e7d152a387d2151d07cbe526c3d831bb2b02e449379b0eb230cb838  templates/book/brief.md
35f8f2c414a6c13a5ccb367e625f0afd22543b75033c4f3a8d29efb343751be9  templates/book/canon/proposals.json
fdf02ac6f27c6fc68c9af1bf46f801314837aba2e77fa56be8d82f3d93156803  templates/book/decisions.md
01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b  templates/book/exports/.gitkeep
6c7ae18a245bef1c1f2131ac19dfe098d97c39e58d7ec5f3086fcc7b4dc0181d  templates/book/handoff.md
a616a7cea750e37485f28bec0e76dad9d944bc6c4aab82f4d58bdea1f8974e88  templates/book/knowledge.json
01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b  templates/book/manuscript/.gitkeep
9efefdb536b9252e2150cd0ebbba1167c33a082572d1b2c10d62e540a40d4fa0  templates/book/outline.md
68d7efb6b3aa0402da25057ed92eeea877ffc180c1e0bbda39b5b1429afba73d  templates/book/production/brief.md
7a8f76d2425071dd1e9d38c60815b7c8627884b510229d4525776dd8ef23bc3d  templates/book/research/claims.json
b253878c592b62704a1e45a6f8b3f6ddf948a4cf0fd2244c12a392eb43eb706c  templates/book/research/notes.md
a22dedf6efbb8e2882d0ef055b93d2eb07d25119af346ef2379ec9d0349471ad  templates/book/research/sources.json
d59755bfd2de4c2bfa97889f5b7695f641350fddf5e041faf2d6dd70ef4f9e7e  templates/book/reviews/README.md
60f961929b66accd8b2516bfbd48c6b030775fd67ef51e36e6cba98d13d5caee  templates/book/reviews/gates.json
7963620baed62c1a60e1996765d3dd1d132b8aadcd3bcffae6a8a7ae88d8990d  templates/book/reviews/issues.json
7d93de33083dfa3aa90526d86b06d9eb9139b9fd09f4e47208e45d7b17a66baa  templates/book/scenes.json
77a175321bbb09ef6a2371370c21210933d222f26b3fd818666f7645dac9e9ec  templates/book/state.md
68a86b5130e1786429a56678cd69ed2640d500e0049aa41a2a5862f6e75538ee  templates/book/style.md
2c64cc5d5e0800c7829f8784506d36224f4ec583a4348457055288824c37b45b  templates/book/tasks.json
12f52c0d9f5ed73d0775192e6daf80c8d0428ba43bb9dc467267b22aeb87912d  templates/book/threads.json
75fbc6b3387ecc0509b1146846dcc308ff543d0adc9869058388bac6449f7e03  templates/series/AGENTS.md
346e12cfba3c7882380af7955959d26777e0b0fa9a1e7c181a20d9192abd5bc8  templates/series/bible.md
fdf02ac6f27c6fc68c9af1bf46f801314837aba2e77fa56be8d82f3d93156803  templates/series/decisions.md
e89ad5312381bea21fbd3672ebafd86ba9e4cc7a2cb23b2c704367c6988f7d6f  templates/series/promises.json
9b942c43a66ad2c8ef34f58ca887ac1cf9de6cc8787823f0d27fe5adace7a03f  templates/series/roadmap.md
97c8e6add4cdc4d9343ee86e3c31247a687ec5b231d2868b986643c1ebe0aa83  templates/series/series.json
f8e4ad6a438d8bb7bdeb4c072b3fa8edb0d93aa61888e2abf66e819fb1c83d5c  templates/universe/AGENTS.md
8c87eebfa705fdd2a24789e513e87b9424ad75e04a0cf74f3e57d41568dc3ca3  templates/universe/bible.md
72b006138c6bb23ad55aafea474ece1f5c57830f5b867c786347a4f0021cdcef  templates/universe/canon.json
20b713bef77c28b5661648126f3618d38258d8bf61e38fd51faed35b696c69ca  templates/universe/characters/README.md
c5c2a336728162e77cec49ffe1ed8d539e52bfd1e26a65c6eaa6d23a021d102a  templates/universe/characters/_template.md
fdf02ac6f27c6fc68c9af1bf46f801314837aba2e77fa56be8d82f3d93156803  templates/universe/decisions.md
7ada4464e29442c04ac2edd9bc0e83cf0a148d94635e7dd6bfcab308ef66b4d9  templates/universe/glossary.md
db5114221f17e827ff297da1b5bc9be7a0dd29730e02fe397ca8b8034513459f  templates/universe/timeline.json
f9be63c2740d8ee1f5ddcc1f9f1681659abbda2aaf0aa934bfbb6e99761c79a1  templates/universe/universe.json
```
