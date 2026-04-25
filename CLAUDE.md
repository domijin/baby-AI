# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## Repository status

baby-AI is an **open-specs / bounty-style** project. The repo currently
contains specs, a receipt contract, and contributor scaffolding — no source
code yet. Subsystem code (under `perception/`, `audio/`, `memory/`,
`interaction/`, `eval/`) is the work being distributed via the spec bounty
mechanism. Do not invent build / lint / test commands; until a subsystem
lands its first impl PR there is nothing to run.

## Repo map

```
README.md            pitch + index (read first if human)
AGENTS.md            machine-readable entry point for autonomous agents
CONTRIBUTING.md      tier definitions + bounty mechanics
specs/               one .md per hypothesis with YAML frontmatter
  00-charter.md       refreshed mission + H1-H5 + compute envelope + tiers
  01-perception.md    H2: embedding-novelty smart-moment selector
  02-audio.md         H5: streaming ASR + ReSpeaker DoA fusion
  03-memory.md        H3: hybrid episodic-vector + concept-KG
  04-interaction.md   H1+H4: edge VLM + verbal-feedback LoRA adapter
  05-eval.md          cross-cutting: receipt contract + harness
receipts/            evidence base (signed JSON, content-addressed refs)
  schema.json         the contract; CI-validated once eval/ exists
  README.md           how to submit
.github/
  ISSUE_TEMPLATE/     spec-gap, eval-result, feature-proposal templates
  PULL_REQUEST_TEMPLATE.md   tier checklist + reproducibility checklist
LICENSE
```

## How work flows here

1. **Spec edits** start as a `spec-gap` issue with at least one verifiable
   citation. Edits to a spec's frontmatter (status, version, metric target)
   land in their own PR, separate from implementation.
2. **Evaluations** are submitted as a single JSON file under
   `receipts/<spec_id>/<agent-id>-<short-sha>.json`, validating against
   `receipts/schema.json` and signed (ssh-sig). Receipts are the project's
   primary artifact; they gate spec status promotion.
3. **Implementations** create code under exactly one subsystem dir and ship
   alongside a tier-3 receipt that meets the spec's target metric.
4. **Spec status ladder**: `proposed → active → implemented → retired`.
   Promotion is gated on receipts, not on conversation. See
   `specs/05-eval.md` for the rule.

## Constraints that bind every spec

- **Compute tiers are fixed.** T0 = Yi Dome (ARMv5, frame source only).
  T1 = Pi 5 16GB. T2 = Pi 5 + Hailo-8L (13 TOPS). T3 = off-device GPU
  (training only). A spec without a measured latency / memory on its
  declared tier is incomplete.
- **Yi Dome toolchain is gcc 4.8.3 / kernel 3.4.35.** Anything
  cross-compiled for T0 must respect this — no modern glibc, no Python
  3.10+, no systemd. The Yi Dome stays a dumb sensor; do not propose
  on-camera inference.
- **Content addressing is required** for every external artifact (HF
  model revision SHA, git SHA, IPFS CID, dataset SHA-256). Tag-only or
  branch-only references are rejected by the receipt schema.
- **No fabricated numbers.** A claim that touches a metric needs a
  receipt; if you don't have one, the artifact is a tier-1 issue, not a
  tier-2 PR. `specs/00-charter.md` enumerates which claims are
  baseline-needed (`tbd` in frontmatter).

## What "doing the task" looks like for Claude in this repo

- **Tier-1 task** ("a paper changes spec X"): find the artifact, verify
  its existence (HF SHA / arXiv ID), open an issue with the `spec-gap`
  template, link the artifact. Do not edit the spec preemptively.
- **Tier-2 task** ("run the baseline"): clone + run + collect log +
  upload log + compute SHA-256 + fill receipt + sign + open PR. The
  signature is over the canonicalized JSON body excluding the
  `signature` field itself.
- **Tier-3 task** ("implement spec X"): create one subsystem dir,
  implement against the spec's `eval.py` interface, attach receipt,
  push model artifacts to HF with a model card linking back to the
  receipt + spec_id + spec_version.
- **Editorial task** ("update CLAUDE.md / specs"): keep the YAML
  frontmatter machine-readable; agents parse it. Don't break field
  names without bumping `spec_version`.

## Existing operational workflow (Yi Dome → Pi)

The one piece of working tooling that predates the open-specs refactor
is the cron-driven pull of recordings from camera to Pi. Preserved here
so it isn't lost — likely lives under perception/ingest/ once that
subsystem ships.

```bash
HOST='192.168.1.24'

cd ~/Documents
check=`cat latest`
latest=`ssh root@$HOST " cd record ; ls -tr */*.mp4 | tail -1"`
if [ "$check" != "$latest" ]
then
    file=`echo $latest | sed "s/\///g"`
    scp root@$HOST:/tmp/sd/record/$latest Vision/$file
    echo $latest > latest
fi
```

Notes: recordings live under `/tmp/sd/record/` on the camera. `dclient`
isn't packed on-device, so `scp` / `rsync` initiated *from* the camera
doesn't work — the Pi must pull. A `latest` file in `~/Documents` tracks
what's already been copied; new files land under `~/Documents/Vision/`.

## Branching

Active development branch is `claude/design-specs-evaluation-UUNNc` per
task instructions. `master` holds the pre-refactor history.
