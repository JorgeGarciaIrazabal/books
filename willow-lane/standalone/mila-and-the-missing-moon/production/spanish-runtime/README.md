# Actual Mistral translation run

Native runtime: OpenCode drafter. Exact requested route: `ollama/mistral-large-4:cloud#high`. Native session: `ses_e8ce2502affeqvQl1QRop4i6Px`. `model-provenance.json` is extracted from actual completed assistant-message metadata; all recorded model entries are Mistral Large 4 through Ollama with variant high. No native Codex Mistral selector or substitute model was claimed.

- batch-1: translate chapters 1–4; 22 native tool calls.
- batch-2: continue sequentially with chapters 5–8; 11 calls.
- batch-3: chapters 9–12 and the supplementary questions; 12 calls.
- batch-4: one bounded local correction pass; 59 calls.

Each exact assignment and actual JSONL output is retained. The requested per-assignment cap was forty tool calls; the final pass exceeded it through batched edits already completed when the overrun was observed. It was not mechanically enforced. No additional Mistral round followed. This deviation is recorded in tasks.json, not concealed as a passed budget check.

source-snapshot.json hashes all original English chapters. pre-review-snapshot.json identifies the original complete translation reviewed independently. final-text-snapshot.json hashes all final Spanish text. director-notes.md records local corrections separately from the unprimed first independent assessment. Native Mistral made all chapter prose and the correction pass; the coordinator made one punctuation-only supplementary-page edit afterward. Final editorial coverage lives in reviews/spanish-translation-review.md and reviews/spanish-translation-recheck.md. These logs are provenance, not a claim of human linguistic or child/parent testing.
