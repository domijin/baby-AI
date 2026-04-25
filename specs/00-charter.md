---
spec_id: charter
status: active
version: 0.1.0
last_updated: 2026-04-25
---

# baby-AI charter

## Mission

Demonstrate that **grounded perceptual–linguistic concepts can be acquired on
edge hardware through closed-loop verbal interaction** — without retraining a
foundation model from scratch — using a small VLM, a hybrid memory store, and
preference-based fine-tuning of a lightweight adapter.

The original 2018 brain-dump (motion-flag + MobileNet + static knowledge graph
+ hand-wavy "verbal RL") is preserved in git history and refreshed below
against state-of-the-art findings circa 2025–2026.

## Hypothesis (refreshed)

**H1.** A 2–3 B-parameter open-weight VLM (e.g. SmolVLM2-2.2B, Moondream2,
PaliGemma-2-3B) can run interactively on a Raspberry Pi 5 (16 GB) +
Hailo-8L NPU at ≥ 3 tok/s with ≤ 2 GB resident memory and serve as the
perceptual–linguistic backbone for a household agent.

**H2.** A "smart-moment" selector based on **embedding-space novelty**
(cosine distance to a sliding window of SigLIP / SigLIP-2 image
embeddings) achieves higher precision@10 of human-judged "interesting
moments" than the legacy motion-flag heuristic on a fixed Yi Dome stream.

**H3.** A **hybrid memory** (episodic vector store keyed on event time +
concept knowledge graph extracted from VLM captions) outperforms either
component alone on relational + temporal recall tasks evaluated locally.

**H4.** Verbal feedback ("yes / no / wrong / it's a X") collected during
interaction can be converted into preference pairs and used to fine-tune
a **LoRA adapter** via DPO or KTO, closing a measurable concept-recognition
gap on a user-defined concept set within < 100 labeled interactions and
< 1 GPU-hour of training (offline, off-device).

**H5.** Direction-of-arrival from a ReSpeaker 4-mic array can be fused as
**spatial grounding tokens** in the VLM prompt, reducing referent ambiguity
("that one over there") in multi-object scenes.

Each hypothesis is owned by one spec under `specs/`, with an explicit
metric, baseline, and target.

## Non-goals

- Pretraining a foundation model from scratch.
- Beating frontier closed models on academic VQA leaderboards.
- Continuous on-device gradient updates (we use periodic, off-device
  adapter training; the device runs inference + data collection only).
- Replacing the Yi Dome firmware with a custom build — the camera stays a
  dumb frame source. All inference is on the Pi or off-device.
- Anything that requires modern glibc / Python 3.10+ / systemd on the Yi
  Dome (toolchain there is gcc 4.8.3 / kernel 3.4.35).

## Compute envelope

| Tier | Hardware                              | Role                         |
| ---- | ------------------------------------- | ---------------------------- |
| T0   | Yi Dome 1080p (Hi3518EV200, ARMv5)    | Frame source, motion gating  |
| T1   | Raspberry Pi 5 16 GB                  | Stream router, audio, memory |
| T2   | Pi 5 + Hailo-8L (13 TOPS)             | VLM inference, novelty embed |
| T3   | Off-device GPU (e.g. RTX 4070 / cloud) | Adapter training, eval batch |

A spec is **"computationally feasible"** iff it lists a tier, a measured
latency, and a measured peak memory on that tier — preferably with a
receipt under `receipts/`.

## Subsystem decomposition

| Spec                             | Owns hypothesis | One-line scope                          |
| -------------------------------- | --------------- | --------------------------------------- |
| [01-perception](01-perception.md) | H2              | Frame ingest + smart-moment selector    |
| [02-audio](02-audio.md)           | H5              | Streaming ASR + DoA fusion              |
| [03-memory](03-memory.md)         | H3              | Hybrid episodic-vector + concept-KG     |
| [04-interaction](04-interaction.md) | H1, H4        | VLM dialogue + verbal-feedback adapter  |
| [05-eval](05-eval.md)             | (cross-cutting) | Distributed eval harness + receipts     |

## SOTA anchors (load-bearing references)

These are the papers / artifacts a spec contributor is expected to be
familiar with. Each spec narrows the list to what that subsystem touches.

- SmolVLM / SmolVLM2 — small open-weight VLMs targeting edge
- Moondream2 / Moondream3 — sub-2B VLM with practical Pi-class inference
- PaliGemma 2 — 3B / 10B VLMs with strong fine-tuning recipes
- SigLIP / SigLIP-2 — sigmoid-loss image–text encoders
- V-JEPA 2 — predictive video representation (alternative perception backbone)
- Distil-Whisper / Whisper.cpp — streaming ASR on CPU
- DPO (Rafailov et al. 2023) / KTO (Ethayarajh et al. 2024) — preference tuning
- LoRA / QLoRA — adapter fine-tuning that fits on consumer GPU
- mem0 / Letta — agent memory frameworks (prior art for H3)
- Hailo-8L — 13 TOPS NPU, M.2 form factor, Pi 5 compatible

Specs should cite the exact revision / commit they target.

## Why this is bounty-able

- **Small artifacts.** Every spec's deliverable fits in a single PR:
  code under one subsystem dir + a model card / adapter on Hugging Face +
  a signed receipt JSON under `receipts/`.
- **Hard, public metrics.** Each hypothesis lists a numeric target on a
  named dataset / benchmark. No vague "improve quality" goals.
- **Composable.** A contributor can take exactly one spec, hit its
  metric, and ship — no need to understand the whole system.
- **Verifiable.** Receipts are content-addressed (HF revision, git SHA,
  dataset hash) and signed; an aggregator can rank them mechanically.

See [`CONTRIBUTING.md`](../CONTRIBUTING.md) for tier definitions and
[`AGENTS.md`](../AGENTS.md) for the autonomous-contributor entry point.
