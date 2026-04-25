---
spec_id: perception-smart-moment
status: proposed
version: 0.1.0
owns_hypothesis: H2
hypothesis: |
  Embedding-novelty selection (cosine distance to a sliding window of
  SigLIP / SigLIP-2 image embeddings) achieves higher precision@10 of
  human-judged "interesting moments" than motion-only flagging, on a
  fixed Yi Dome stream.
metric:
  name: precision_at_10
  unit: ratio
  baseline:
    method: opencv-mog2-motion
    score: 0.30
    notes: |
      Background-subtraction MOG2 + min-blob-area gate. Reference impl
      lives at the URL below. This is the "honest motion-only" baseline
      that the embedding-novelty selector must beat.
    reference_impl: tbd
  target: 0.55
  also_report: [precision_at_5, recall_at_30, false_positive_rate_per_hour]
dataset:
  name: yi-dome-pilot-v0
  status: not_yet_collected
  size_target_hours: 8
  labeling_protocol: |
    Three-rater majority vote on whether a 5-second clip contains a
    "moment worth keeping" (novel object, multi-person interaction,
    pet activity, package delivery, etc.). Inter-rater agreement
    must be >= 0.6 Cohen's kappa for the dataset to be accepted.
  license_target: CC-BY-NC 4.0 (faces blurred via mediapipe)
compute_budget:
  tier: T2  # Pi 5 + Hailo-8L
  latency_ms_per_frame_p95: 50
  peak_memory_mb: 1500
  framerate_hz: 5
artifacts_required:
  - code: git SHA in this repo
  - encoder: HuggingFace revision (e.g. google/siglip2-base-patch16-224 @ <sha>)
  - eval_log: signed receipt under receipts/perception-smart-moment/
  - dataset_manifest: SHA-256 of clip list + label CSV
bounty:
  tiers_open: [2, 3]
  pledged_by: []
references:
  - https://arxiv.org/abs/2303.15343  # SigLIP
  - https://arxiv.org/abs/2502.14786  # SigLIP 2
  - https://ai.googleblog.com/2018/05/automatic-photography-with-google-clips.html
  - https://hailo.ai/products/ai-accelerators/hailo-8l-m2-ai-acceleration-module/
---

# Perception — smart-moment selector

## Problem

The Yi Dome streams continuous video to the Pi (~ 5 fps after downsample).
Storing all of it is wasteful and downstream subsystems (memory, interaction)
care only about a sparse set of "events". The legacy approach is a motion
flag — fast but noisy: lighting changes, curtains, and the camera's own IR
cutover all trigger false positives, and slow novel events (a new object
quietly placed on a table) are missed entirely.

## Approach

Replace the motion-only gate with a two-stage selector:

1. **Cheap gate (T1, CPU):** background-subtraction motion flag, kept
   only as a power-saver — frames that fail this gate skip the encoder.
2. **Novelty gate (T2, Hailo-8L):** SigLIP-2 image embedding of the
   gated frame, compared against a rolling window of the last *N* kept
   embeddings. A frame is "novel" iff its minimum cosine distance to
   the window exceeds threshold τ. τ is tuned per-stream on a held-out
   calibration hour.

A "moment" is the bounding 5-second clip around a sequence of consecutive
novel frames. Moments are emitted as events to the memory subsystem with
the SigLIP embedding attached (zero-cost reuse downstream).

## Why this is feasible

- SigLIP-2-base-patch16-224 is ~ 200 M params, INT8-quantizable, and
  benchmarked at < 30 ms / image on Hailo-8L by upstream reports.
  At 5 fps target and a CPU motion gate dropping ~ 80 % of frames, the
  encoder sees ~ 1 frame/s — well within budget.
- Sliding-window cosine search for *N* ≤ 256 is a single matmul on CPU
  (< 1 ms). No vector DB needed at this stage.

## Required artifacts (PR-ready bundle)

- `perception/` source dir (language at contributor's discretion;
  Python + ONNX Runtime / Hailo-RT recommended).
- `perception/eval.py` that takes `--dataset` and `--model` and emits
  a receipt JSON conforming to `/receipts/schema.json`.
- HuggingFace model card for any custom-trained gate.
- Receipt at `receipts/perception-smart-moment/<agent-id>-<short-sha>.json`.

## Open questions for contributors

1. Is SigLIP-2 the right encoder, or does a CLIP-distilled / DINOv2
   embedding give higher precision at the same compute? Run the bake-off.
2. How should τ adapt to time-of-day (IR vs. visible-light frames)?
   Static τ is the v0; adaptive is bonus.
3. Should consecutive near-duplicate "novel" frames be merged via
   non-max suppression in embedding space? Likely yes.

## Out of scope

- Object detection / bounding boxes (handled later by VLM at
  interaction time, not here).
- Face recognition (privacy + scope).
- On-device fine-tuning of the encoder.
