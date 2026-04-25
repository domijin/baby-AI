---
spec_id: audio-asr-doa
status: proposed
version: 0.1.0
owns_hypothesis: H5
hypothesis: |
  Direction-of-arrival from a ReSpeaker 4-mic array, fused into the VLM
  prompt as spatial grounding tokens (e.g. "[speaker@-30deg]"), reduces
  referent-resolution error on multi-object scenes vs. the same VLM with
  no spatial conditioning.
metric:
  name: referent_resolution_accuracy
  unit: ratio
  baseline:
    method: vlm-only-no-spatial
    model: smolvlm2-2.2b-instruct
    score: tbd  # contributor establishes via the protocol below
    notes: |
      Same VLM, same prompt, same scenes — only the spatial token is
      removed. Establishing this baseline IS a tier-2 contribution.
  target_delta: +0.10  # absolute accuracy gain over baseline
  also_report:
    - WER on common_voice_17_en  # ASR side, must not regress vs. distil-whisper-small
    - DoA_mean_absolute_error_deg
asr:
  default_model: distil-whisper/distil-small.en
  fallback: openai/whisper-tiny.en (whisper.cpp INT8)
  streaming_chunk_ms: 500
  target_latency_ms_p95: 600
doa:
  hardware: ReSpeaker 4-Mic Array v2.0 (UAC1.0) on Pi 5
  algorithm_default: GCC-PHAT with SRP-PHAT fallback
  resolution_deg: 5
compute_budget:
  tier: T1  # Pi 5, no NPU needed for ASR + DoA
  latency_ms_p95: 600
  peak_memory_mb: 800
artifacts_required:
  - code: git SHA in this repo
  - eval_log: receipts/audio-asr-doa/
  - synthetic_doa_set: SHA-256 of WAV manifest (rendered with pyroomacoustics)
  - referent_eval_set: image+utterance pairs with ground-truth referent IDs
bounty:
  tiers_open: [2, 3]
  pledged_by: []
references:
  - https://arxiv.org/abs/2311.00430  # Distil-Whisper
  - https://github.com/ggerganov/whisper.cpp
  - https://wiki.seeedstudio.com/ReSpeaker_Mic_Array_v2.0/
  - https://www.pyroomacoustics.org/
---

# Audio — streaming ASR + direction-of-arrival fusion

## Problem

The interaction subsystem needs to know not just *what* was said but
*where it came from*, so the VLM can disambiguate deictic references
("that one", "the red one over there") in scenes with multiple
candidate objects. The legacy plan was "ASR converts to NLP problem",
which leaves spatial information on the floor.

## Approach

Two parallel paths, fused at prompt-construction time:

1. **ASR path.** Streaming distil-whisper-small.en (or whisper.cpp tiny
   for ultra-low-mem) on 500 ms chunks. Emits token stream with
   per-utterance start/end timestamps.
2. **DoA path.** GCC-PHAT on the 4-mic array, computed every 100 ms,
   smoothed with a 1-second median filter. Per-utterance DoA = mode of
   the smoothed track over the utterance window.

Fusion: at prompt time, the interaction subsystem inserts a spatial
token of the form `[speaker_at:-30deg]` immediately before the
transcribed utterance. The VLM is conditioned (via system prompt) to
treat the angle as the speaker's bearing relative to the camera.

## Why this is feasible

- Distil-Whisper-small.en is ~ 166 M params, runs at ~ 6× realtime on
  Pi 5 CPU (4 threads) per upstream reports.
- GCC-PHAT on 4 channels at 16 kHz is < 5 % of one core.
- No NPU required — frees Hailo-8L for perception + interaction.

## Evaluation protocol

**ASR side.** WER on Common Voice 17 English test split, single-speaker.
Must not regress more than 1 % WER vs. distil-whisper-small reference
score on the same hardware.

**DoA side.** Synthetic dataset of 500 utterances rendered with
pyroomacoustics in a 4 × 4 m room with reverberation T60 = 0.4 s,
ground-truth source angles uniform in [-90°, +90°]. Report mean
absolute error.

**Fusion side.** A held-out set of N ≥ 100 (image, utterance, ground-truth
referent) triples, with two or more candidate objects per scene where
the deictic phrase is the only disambiguator. Accuracy = fraction where
the VLM's selected referent matches ground truth.

## Required artifacts

- `audio/` source dir.
- `audio/eval.py` emitting receipt JSON.
- Synthetic DoA dataset (or its generation script with fixed seed).
- Referent evaluation set with documented collection protocol.
- Receipt at `receipts/audio-asr-doa/<agent-id>-<short-sha>.json`.

## Open questions

1. Is a single DoA scalar enough, or should the fusion token encode
   uncertainty (e.g. `[speaker_at:-30deg±10]`)?
2. Does the VLM benefit from natural-language phrasing
   (`"the speaker is to the left"`) over coded tokens? Run the A/B.
3. How to handle silent moments / non-speech audio? Out of scope for
   v0 — but a follow-up spec on event audio (glass break, doorbell)
   is a natural extension.

## Out of scope

- Speaker diarization / voice ID (separate spec if pursued).
- On-device wake-word (use push-to-talk or always-on for v0).
- Far-field beam-forming beyond what ReSpeaker firmware provides.
