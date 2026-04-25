---
spec_id: memory-hybrid
status: proposed
version: 0.1.0
owns_hypothesis: H3
hypothesis: |
  A hybrid memory store — episodic vector index keyed on event time,
  plus a concept knowledge graph extracted from VLM captions —
  outperforms either component alone on relational + temporal recall
  tasks evaluated on a held-out interaction log.
metric:
  primary:
    name: hybrid_recall_at_5
    unit: ratio
    baseline_pure_vector:
      method: sqlite-vec + bge-small-en-v1.5
      score: tbd
    baseline_pure_kg:
      method: kuzu + VLM-extracted triples, cypher exact-match
      score: tbd
    target: 0.10  # absolute gain over the better of the two baselines
  also_report:
    - mean_query_latency_ms_p95
    - storage_bytes_per_event
benchmark:
  name: baby-ai-recall-v0
  composition:
    - 30%  temporal queries  ("what did I bring home on Tuesday?")
    - 30%  relational queries ("which objects has the cat sat on?")
    - 30%  visual-similarity ("anything else like this thing?")
    - 10%  multi-hop          ("the package the courier left two days ago")
  size_target: 200 query / answer pairs
  collection_protocol: |
    Bootstrapped from 1-2 weeks of real interaction logs from at least
    three contributors, then queries hand-authored by a different
    contributor than the one who collected the log. Logs are released
    under CC-BY-NC after PII review (faces blurred, voices dropped).
compute_budget:
  tier: T1
  query_latency_ms_p95: 200
  ingest_latency_ms_p95: 100
  storage_bytes_per_event_target: 4096
artifacts_required:
  - code: git SHA in this repo
  - eval_log: receipts/memory-hybrid/
  - benchmark_manifest: SHA-256 of query/answer set
  - storage_engine_versions: pinned (sqlite-vec, kuzu, etc.)
bounty:
  tiers_open: [2, 3]
  pledged_by: []
references:
  - https://github.com/asg017/sqlite-vec
  - https://kuzudb.com/
  - https://huggingface.co/BAAI/bge-small-en-v1.5
  - https://github.com/mem0ai/mem0
  - https://github.com/letta-ai/letta
---

# Memory — hybrid episodic-vector + concept-KG

## Problem

A persistent memory layer is what separates a conversational toy from
an agent that "knows" the household. Pure vector stores are great for
"find me something like this" but stumble on relational queries
("which object has my child played with most?"). Pure KGs are great
for relations but require schema work and miss visual similarity.

## Approach

Two stores, written together, queried together:

1. **Episodic store** — `sqlite-vec` (or equivalent embedded vector
   index). One row per event from perception or audio, with
   `(timestamp, source, embedding, blob_uri, caption)`. The
   `embedding` is the SigLIP image embedding from spec 01 (no
   re-encode), or the BGE-small text embedding for utterances.
2. **Concept KG** — `kuzu` (embedded property graph). Triples are
   extracted from VLM captions of kept moments using a fixed prompt:
   `(subject, predicate, object, source_event_id, confidence)`.
   Schema is open; a v0 vocabulary lives at `memory/schema.cypher`.

Query router:

- Visual-similarity query → vector store only.
- Relational / multi-hop query → KG only.
- Mixed / temporal query → KG narrows by time + relation, vector
  store reranks within the narrowed set.

## Why this is feasible

- sqlite-vec on Pi 5 holds 1 M embeddings (768-dim, FP16) in ~ 1.5 GB
  with sub-50 ms top-k.
- kuzu is single-binary, no server, < 50 MB resident for typical
  household-scale graphs.
- VLM caption + triple extraction is amortized over the perception
  cadence (~ 1 event / minute when calibrated).

## Evaluation protocol

`memory/eval.py` loads the benchmark manifest, replays all events into
a fresh store, then runs each query with three configs (vector-only,
kg-only, hybrid) and emits per-config metrics into a single receipt.

A submission is valid only if the **same** store implementation answers
all three configs — no cherry-picking the best store per query type.

## Required artifacts

- `memory/` source dir with ingest + query API.
- `memory/eval.py`.
- `memory/schema.cypher` with the v0 KG vocabulary, justified in
  comments.
- Pinned versions of `sqlite-vec`, `kuzu` (or chosen alternatives) in
  the receipt.
- Receipt at `receipts/memory-hybrid/<agent-id>-<short-sha>.json`.

## Open questions

1. Should the KG be VLM-extracted or human-curated bootstrap + VLM
   incremental? The former is honest about real performance; the
   latter is more likely to hit metric. Suggest reporting both.
2. Is a relational DB (Postgres + pgvector) a better single-store
   choice than two engines? Run the comparison if you believe so —
   the spec doesn't mandate the underlying tech.
3. How is memory consolidated / forgotten? Assume "never" for v0;
   a follow-up spec on consolidation (sleep-style replay, summary
   compression) is welcome.

## Out of scope

- Cross-device sync.
- Multi-user / multi-agent memory.
- Encrypted-at-rest storage (Pi-local; user-controlled).
