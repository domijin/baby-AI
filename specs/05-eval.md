---
spec_id: eval-distributed-harness
status: proposed
version: 0.1.0
owns_hypothesis: cross-cutting
purpose: |
  Define the receipt format, signing, and reproducibility rules that
  every other spec depends on. This spec is what makes baby-AI
  evidence-based instead of vibes-based.
metric:
  name: receipt_validity_rate
  unit: ratio
  target: 1.0  # all merged receipts must validate against schema
  also_report:
    - reproduce_rate  # fraction of receipts a third party can reproduce
    - median_time_from_receipt_to_replication_hours
artifacts_required:
  - schema: /receipts/schema.json
  - validator: eval/validate_receipt.py
  - aggregator: eval/aggregate.py (deferred until N>=3 receipts exist)
bounty:
  tiers_open: [1, 2, 3, 4]
  pledged_by: []
references:
  - https://json-schema.org/draft/2020-12/schema
  - https://www.sigstore.dev/  # candidate signing scheme
  - https://huggingface.co/docs/hub/en/repositories-revisions  # content addressing
---

# Eval — distributed evaluation harness

## Problem

Bounty-style open specs collapse the moment claims aren't independently
verifiable. The minimum viable form of "verifiable" is: **a third
party with the same hardware tier and the listed artifact references
can reproduce the receipt's score within a stated tolerance.** This
spec defines the contract that makes that possible.

## Receipt contract

A receipt is a single JSON file conforming to
[`/receipts/schema.json`](../receipts/schema.json). Every receipt MUST
include:

- `schema_version` — pin to detect breaking changes.
- `spec_id` and `spec_version` — the target spec at the time of
  evaluation.
- `agent` — `{id, kind: human|autonomous|hybrid, model?}`. Autonomous
  contributors declare the model that ran the eval (e.g.
  `claude-opus-4-7`).
- `artifact_refs` — content-addressed references for everything the
  result depends on:
  - `code_git_sha` (this repo)
  - `model_repo` + `model_revision` (HuggingFace revision SHA, not
    just tag)
  - `dataset_uri` + `dataset_sha256`
  - `runtime` (build identifier, e.g. `llama.cpp@<sha>`,
    `hailort@<version>`, `python@<x.y.z>`)
- `hardware` — fingerprint:
  `{tier, cpu, ram_mb, accelerator?, accelerator_driver_version?, kernel}`.
- `metric` — `{name, value, unit, ci_low?, ci_high?, n_samples}`.
- `seed` — a single integer or list, all random seeds used.
- `log_uri` — public URL to the full eval log (gist, HF dataset,
  IPFS, etc.). The hash of the fetched log MUST match
  `log_sha256` in the receipt.
- `signature` — cryptographic signature over the canonicalized
  receipt body (sigstore / minisign / ssh-sig — choose one;
  ssh-sig is recommended for low friction).

Receipts that fail schema validation, hash check, or signature check
are rejected by the validator and may not be merged.

## Tolerance and replication

Every metric submitted with a receipt must include `n_samples` and
either confidence-interval bounds or enough information to compute
them. A replicating receipt is "compatible" iff its central value
falls within the original CI (or within ± 5 % relative if the original
omits CI — strongly discouraged but allowed for v0).

A spec is upgraded from `proposed` → `active` when at least one
receipt validates and replicates.

A spec is upgraded from `active` → `implemented` when at least one
receipt **meets the spec's target metric** *and* a second independent
receipt replicates that result on the same hardware tier.

## Hardware tiers (canonical)

Receipts MUST declare exactly one of these tier IDs:

- `T0-yi-dome-hi3518ev200`
- `T1-rpi5-16gb`
- `T2-rpi5-16gb-hailo8l`
- `T3-desktop-gpu` — must include GPU model + VRAM in `hardware`
- `T?-other` — explanation required; aggregator may exclude

## Required artifacts

- `eval/validate_receipt.py` — JSON Schema + signature verifier. CI
  hook. Refuses to merge receipts that fail.
- `eval/aggregate.py` — reads all receipts, emits a per-spec
  leaderboard table to `eval/leaderboard.md`. Deferred until at
  least three receipts exist (no point earlier).
- This spec also defines a **regression set** that every adapter
  trained under spec 04 must pass before being shipped back to a
  device: a fixed list of 30 prompts whose answers must not regress
  by more than 5 % accuracy after fine-tuning.

## Open questions

1. ssh-sig vs sigstore — ssh-sig is dependency-free and friction-free
   but offers weaker identity guarantees. v0: ssh-sig.
2. Should receipts be append-only (immutable history) or amendable?
   v0: append-only, supersedes via a `supersedes: <prior-receipt-sha>`
   field.
3. How are autonomous-agent identities established? v0: agent posts
   public key in PR body; subsequent receipts from same agent ID must
   verify against same key, or supersede with a key-rotation receipt.

## Out of scope

- Trust ranking of agents (anti-gaming). Mentioned for future work;
  v0 trusts schema + replication.
- Real-money bounty escrow. The structure supports it (any third
  party can verify a receipt deterministically) but mechanics live
  in `CONTRIBUTING.md`, not here.
