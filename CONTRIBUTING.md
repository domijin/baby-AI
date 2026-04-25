# Contributing to baby-AI

baby-AI is **open-specs** before it is open-source: the work is to make
each spec under `specs/` into a tested, reproducible subsystem with
signed evidence in `receipts/`. Code is a means; receipts are the goal.

This document covers tier definitions, the bounty mechanism, and the
acceptance bar. Autonomous agents should also read [`AGENTS.md`](AGENTS.md).

## Contribution tiers

| Tier | What it is                                | Evidence required                       |
| ---- | ----------------------------------------- | --------------------------------------- |
| 1    | Triage / spec-gap issue with citation     | Issue + ≥ 1 verifiable artifact link    |
| 2    | Evaluation receipt (baseline or replication) | Signed JSON under `receipts/`         |
| 3    | Implementation that hits a spec's target  | PR + receipt + model cards (if any)     |
| 4    | Sustained review / spec ownership         | ≥ 1 accepted tier-3 + structured reviews |

A contribution is graded by the tier it actually clears, not the tier
its author claimed. A tier-3 PR with a non-validating receipt is
treated as tier-2 (evidence) at best, and the implementation portion is
re-reviewed once a valid receipt is attached.

## Promotion of a spec

Specs move along a fixed status ladder:

```
proposed  →  active  →  implemented  →  retired
```

- `proposed → active`: at least one receipt validates against the
  schema and replicates a stated baseline.
- `active → implemented`: at least one receipt **meets the spec's
  target metric** *and* a second independent receipt replicates that
  result on the same hardware tier.
- `implemented → retired`: superseded by a new spec, or the
  hypothesis is falsified by accumulated receipts.

Maintainers update the status frontmatter in a separate PR after
receipts land — this keeps spec changes auditable.

## Bounty mechanism

The repository structure supports cash / credit bounties without
requiring them. Anyone (maintainer, sponsor, or third party) may
**pledge** a bounty against a specific tier of a specific spec by
opening a PR that adds an entry under that spec's `bounty.pledged_by`
list:

```yaml
bounty:
  tiers_open: [2, 3]
  pledged_by:
    - sponsor: "@example-org"
      tier: 3
      amount: "USD 500"
      escrow: "https://algora.io/<...>"   # or sigstore-attested promise
      conditions: "first receipt that meets target on T2"
      expires: 2026-09-01
```

Pledges with no `escrow` link are advisory only and do not bind
maintainers. Pledges with escrow are paid out on the first PR that
maintainers accept against the stated condition.

Without any active pledge, contributions still count for tier
attribution and spec ownership — the project's primary currency is
**verifiable contribution history**, not money.

## Acceptance bar

A PR is accepted when:

1. It targets exactly one tier and meets that tier's evidence bar.
2. Any new file lives under the directory the spec assigns to it
   (e.g. `perception/`, `audio/`, `memory/`, `interaction/`,
   `eval/`). Don't sprawl.
3. CI checks pass (once they exist; until then, maintainers run the
   validator manually). At minimum:
   - JSON Schema validation on touched receipts.
   - Markdown lint on touched specs.
4. The PR description fills in the template — including the **two
   independent verifiable links** that AGENTS.md requires for tier
   ≥ 2 contributions.

## What to skip

These will not be merged:

- Repository-wide reformatting / linter retrofits without a spec
  motivating them.
- New dependencies in a subsystem that already has a working impl,
  unless the swap is justified by a metric delta documented in a
  receipt.
- "AI-generated boilerplate" with no contributor judgment in the
  diff. Receipts and metrics are the proof of judgment.
- Documentation that paraphrases a spec without adding information.

## Getting started

If you (human or agent) are looking at this repo for the first time:

- For a tier-1 contribution: pick any `proposed` spec, find one
  citation that's stale or one number that's `tbd`, open an issue.
- For a tier-2 contribution: pick the spec with the smallest stated
  compute budget, run its baseline, submit a receipt.
- For a tier-3 contribution: claim a spec by commenting on its
  tracking issue, then implement against the metric target.

## Questions

Open an issue with the `question` label. Maintainers do not respond
to DMs.
