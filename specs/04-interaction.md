---
spec_id: interaction-vlm-and-adapter
status: proposed
version: 0.1.0
owns_hypothesis: [H1, H4]
hypothesis_h1: |
  A 2-3B-parameter open-weight VLM runs interactively on Pi 5 + Hailo-8L
  at >= 3 tok/s with <= 2 GB resident memory and produces grounded
  responses for household-agent prompts.
hypothesis_h4: |
  Verbal feedback collected during interaction (yes / no / wrong /
  it's a X) can be converted into preference pairs and used to
  fine-tune a LoRA adapter via DPO or KTO, closing a measurable
  concept-recognition gap on a user-defined concept set within
  < 100 labeled interactions and < 1 GPU-hour of off-device training.
metric:
  h1_runtime:
    tokens_per_second_p50_target: 3.0
    peak_memory_mb_max: 2048
    first_token_latency_ms_p95_target: 1500
    measured_on_hardware: rpi5-16gb-hailo8l
    prompt_set: baby-ai-prompts-v0  # 50 image+question pairs in repo
  h4_adaptation:
    name: concept_set_accuracy_delta
    unit: absolute_ratio_gain
    target: 0.20
    pre_adapter_baseline: tbd  # established by contributor
    feedback_budget: 100  # labeled (image, utterance, label) triples
    training_compute_budget: 1.0  # GPU-hours, RTX 4070-class
    eval_holdout_protocol: |
      User-defined concept set (e.g. "the blue mug", "Rex the dog",
      "the corner where the cat sleeps"). Holdout is captured AFTER
      the feedback log is frozen; adapter does not see holdout images.
candidate_models:
  - HuggingFaceTB/SmolVLM2-2.2B-Instruct
  - vikhyatk/moondream2
  - google/paligemma2-3b-mix-224
  contributor_may_propose_others: true
adaptation_method:
  default: LoRA on language-side projection layers + last-N decoder layers
  preference_loss: DPO (Rafailov 2023) primary, KTO (Ethayarajh 2024) fallback
  training_target_hardware: single 12-16 GB consumer GPU, off-device
compute_budget:
  inference_tier: T2
  training_tier: T3
  inference_peak_memory_mb: 2048
  inference_first_token_ms_p95: 1500
artifacts_required:
  - code: git SHA in this repo
  - base_model: HF revision pinned in receipt
  - adapter: HF revision pinned in receipt (LoRA weights)
  - feedback_log: SHA-256 of frozen training set
  - eval_log: receipts/interaction-vlm-and-adapter/
  - prompt_set_version: baby-ai-prompts-v0 SHA in this repo
bounty:
  tiers_open: [2, 3, 4]
  pledged_by: []
references:
  - https://huggingface.co/blog/smolvlm2
  - https://github.com/vikhyat/moondream
  - https://arxiv.org/abs/2412.03555  # PaliGemma 2
  - https://arxiv.org/abs/2305.18290  # DPO
  - https://arxiv.org/abs/2402.01306  # KTO
  - https://arxiv.org/abs/2106.09685  # LoRA
---

# Interaction — on-device VLM dialogue + verbal-feedback adapter

## Problem

The interaction subsystem is the agent's voice. It must (a) run on the
Pi at interactive latency without becoming the bottleneck of the whole
system, and (b) get measurably better at recognizing things its user
cares about, using only the verbal corrections that user is going to
give anyway. A model that needs days of fine-tuning per concept fails
the use case; a model that never improves fails it differently.

## Approach

**Inference path.** A small VLM (default: SmolVLM2-2.2B-Instruct,
INT4 / Q4) loaded on Pi 5 + Hailo-8L. Runtime: llama.cpp / MLC-LLM /
ExecuTorch — contributor's choice, must be reproducible from a
documented build. Prompt template includes:

- System prompt with household-agent persona
- Spatial token from spec 02 (`[speaker_at:Xdeg]`)
- Top-k memory snippets from spec 03 (text + thumbnail caption)
- Current frame from spec 01 (kept moment or live capture)
- User utterance

**Feedback path.** Every turn where the user issues a correction
("no, that's a mug not a cup", "wrong", "yes good") is logged as a
candidate preference pair: `(prompt, model_output, corrected_output,
label)`. Pairs are not used live; they accumulate in a feedback log.

**Adaptation path.** Off-device, periodically (e.g. nightly), the
feedback log is converted into DPO or KTO training pairs and used to
fine-tune a LoRA adapter on the language side of the VLM. Base
weights are frozen. The new adapter is shipped back to the Pi.

## Why this is feasible

- SmolVLM2-2.2B at Q4 fits in ~ 1.4 GB. Moondream2 is smaller still.
  PaliGemma-2-3B at Q4 sits at ~ 1.8 GB.
- Hailo-8L offloads vision encoding; language decode is CPU on Pi 5
  (4 cores @ 2.4 GHz) — measured at 3-6 tok/s for Q4 2-3B models in
  upstream community reports.
- LoRA on r=16, last 8 decoder layers is < 80 MB of trainable params,
  trains in << 1 hour on a single RTX 4070 over < 200 preference
  pairs at sequence length 1024.

## Evaluation protocol

**H1 (runtime).** Run the prompt set `baby-ai-prompts-v0/` (kept in
this repo) end-to-end on the contributor's Pi 5 + Hailo-8L. Report
tok/s p50, first-token latency p95, peak memory. Receipt MUST include
the exact runtime build and quantization settings.

**H4 (adaptation).** Two-phase:

1. *Pre-adapter baseline.* Run the contributor's user-defined concept
   set through the base VLM. Record accuracy.
2. *Post-adapter.* Train LoRA on the frozen feedback log (capped at
   100 pairs by spec). Re-run the concept set. Record accuracy.

Both phases use a holdout captured **after** the feedback log was
frozen. Reusing training images in the eval set invalidates the
receipt.

## Required artifacts

- `interaction/` source dir (inference + feedback logger + DPO/KTO
  trainer entry point).
- `interaction/prompts/baby-ai-prompts-v0/` — 50 fixed prompts for
  the runtime benchmark. Frozen by spec; new versions get new IDs.
- LoRA adapter on Hugging Face with model card linking to feedback
  log SHA and base model revision.
- Receipt at `receipts/interaction-vlm-and-adapter/<agent-id>-<short-sha>.json`.

## Open questions

1. Is DPO or KTO better when the negative class is dominated by
   "wrong" with no specific corrected output? KTO is built for
   un-paired binary feedback — likely better for verbal-only data.
2. Should the adapter be split per-user, or shared? v0 = per-user.
3. Are there safety / drift risks from training on a single user's
   corrections? Yes — see [05-eval](05-eval.md) for the regression
   set every adapter must pass before being shipped back to device.

## Out of scope

- On-device training (T3 only).
- Multi-modal generation (images, audio out) — text + TTS only.
- Continual pretraining of the base VLM.
