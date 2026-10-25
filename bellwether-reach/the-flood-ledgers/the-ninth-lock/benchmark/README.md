**Effort-control correction:** Kimi/Mistral labels were configured variants, not verified effective effort. Their effort-effect conclusions are withdrawn; [read the correction](effort-control-correction.md). Use the corrected follow-up configuration for new runs.

# The Ninth Lock — model pilot
Start with [report.md](report.md) for phase recommendations, complete ranks, reviewer disagreement, effort comparisons and limitations. [results.json](results.json) contains the preference calculations; these are recorded peer preferences, not literary quality scores.

Universe **Bellwether Reach**; series **The Flood Ledgers**; book **The Ninth Lock**. An original adult speculative mystery about two incompatible flood-protection certificates. This workspace contains a controlled sample experiment, not a completed novel.

| Model | Settings tested | Candidate artifacts |
| --- | --- | --- |
| GPT-6.1 Sol | medium / high | [medium](outputs/sol61-medium.md), [high](outputs/sol61-high.md) |
| GPT-6 Sol | medium / high | [medium](outputs/sol6-medium.md), [high](outputs/sol6-high.md) |
| Kimi K3 | low / high, as selected by author | [low original](outputs/kimi-low.md), [high](outputs/kimi-high.md), [low with process-note tail removed](outputs-corrected/kimi-low.md) |
| Mistral Large 4 | none / high, supported thinking controls | [none](outputs/mistral-none.md), [high](outputs/mistral-high.md) |

Eight phases: concept/world/series, plot, character/dialogue, scene drafting, developmental editing, line editing, copy/continuity, and blurb. Each condition has one substantive generation. Its exact model is excluded from judging its samples at both settings. Original reviews are in `reviews/`; six fresh P8-only comparisons are in `reviews-corrected/`; `effective-reviews/` merges that correction with unchanged P1–P7. Only the runtime-note tail was removed; all original fiction and ranks remain preserved. See [correction provenance](blurb-correction.json) and [original report](original-report.md).

[Protocol](protocol.md), [amendments](protocol-amendments.md), [run manifest](run-manifest.json), [source snapshot](source-snapshot.json), [candidate snapshot](candidate-snapshot.json), [evidence dispositions](evidence-disposition.json), and [director audit](director-audit.json) provide provenance. `blind-keys.json` and `blurb-correction-keys.json` reveal identities; they were withheld from reviewers.

Offline reproduction from this directory: `python3 analyze.py`, `python3 verify_artifacts.py`, then `python3 render_report.py`. `python3 analyze.py --original` reproduces the raw run into `original-results.json` and `original-validation.json`. `merge_blurb_correction.py` recreates derived effective reviews without changing originals. None of these scripts calls models or runs agents. Model execution used native Codex subagents and native OpenCode CLI. The nested `opencode.json` is benchmark-only configuration.

The strongest stable pilot leads are GPT-6.1 Sol high for plotting, dialogue, line editing and copy/continuity, and GPT-6.1 Sol medium for blurbs. Concept development, drafting and developmental editing are reviewer-sensitive. Read the report before generalizing to other books. No permanent studio defaults were changed.
