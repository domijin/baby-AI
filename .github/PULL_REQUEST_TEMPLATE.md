<!--
Read AGENTS.md and CONTRIBUTING.md before opening this PR. Sections
below are required for tier >= 2 contributions; tier-1 (spec edits
prompted by a triage issue) may leave the receipts section blank.
-->

## Tier and intent

- [ ] Tier 1 — spec edit / doc fix (link the issue this addresses)
- [ ] Tier 2 — evaluation receipt only
- [ ] Tier 3 — implementation + receipt
- [ ] Tier 4 — review / spec ownership change

## Target spec

- `spec_id`:
- `spec_version`:
- Status change requested (if any): `proposed → active` / `active → implemented` / none

## Summary

<!-- One paragraph. What changed, why. Link to the metric this contribution moves. -->

## Receipts touched

<!-- For tier >= 2: list the receipt files added/superseded. -->

- `receipts/<spec_id>/<your-id>-<short-sha>.json`
  - hardware tier:
  - metric value:
  - prior receipt superseded (sha-256, if any):

## Verifiable artifact links

<!--
At least TWO independently verifiable links for tier >= 2 contributions.
Content-addressed only (HF revision SHA, git SHA, IPFS CID, archived
DOI). Branch-only or tag-only links are insufficient.
-->

1.
2.

## Reproducibility checklist (tier >= 2)

- [ ] Receipt validates against `receipts/schema.json`
- [ ] `log_sha256` matches the file at `log_uri`
- [ ] Signature verifies (`ssh-keygen -Y verify ...`)
- [ ] All `dataset_*` / `model_*` references include a SHA, not just a tag
- [ ] Hardware tier matches the spec's compute envelope
- [ ] Random seeds recorded in the receipt
- [ ] Same `agent.id` as my prior receipts (or this PR documents a
      key-rotation supersede)

## For implementation PRs (tier 3) only

- [ ] Source code lives under exactly one subsystem dir
- [ ] No new heavyweight dependency without a metric-delta justification
- [ ] Spec status updated in the same or follow-up PR, not retroactively
