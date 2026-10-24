# Native Codex nonfiction review — synthetic fixture

Invocation: native Codex `spawn_agent`, requested model `gpt-6-astra`, fresh context,
role assigned as `nonfiction_editor`, explicitly instructed to read its shared
contract. No Python launcher or native custom-role selector was used. The worker
reported that it could not independently see the exact model variant; the model
request is recorded by the parent invocation rather than inferred from prose.

Inputs: `.studio/agents/nonfiction_editor.md` and the complete synthetic
`.studio/reviews/2026-10-23/fixtures/nonfiction.md`. Read-only; no external sources.

## Returned findings

`CLM-TEST-1` requires revision against supplied synthetic source `SRC-TEST-1`:

1. **Causation:** the causal proof claim contradicts page 2 Methods and page 4
   Limitations: self-selected volunteers and no control group cannot establish it.
2. **Denominator:** page 3 supports 9/12 respondents, or 75%, rather than 75% of all
   residents or all attendees.
3. **Missing data:** 12 of 20 responded, a 60% response rate; eight outcomes remain
   unknown. The excerpt does not establish whether everyone was contacted.
4. **Generalization:** effectiveness for any coastal community exceeds the sample
   and contradicts page 4's restriction against generalizing even to all residents.

The page 3 citation supports counts and self-reported confidence, not causal
effectiveness, prevalence, general applicability, or independently measured improvement.

## Suggested limited replacement

In this synthetic example, 12 of 20 volunteer workshop attendees answered the
follow-up. Nine respondents—75% of those who responded—reported increased
confidence; outcomes for the eight nonrespondents are unknown. Self-selection,
missing responses, and the absence of a comparison group prevent causal conclusions
or generalization to all residents or other communities (SRC-TEST-1, pp. 2–4).

## Coverage

All of `CLM-TEST-1`; direct inspection of supplied `SRC-TEST-1` page 2 Methods,
page 3 Results, and page 4 Limitations. No other claims or real research assessed.
The fixture is invented; this tests internal source support and arithmetic.
