# Receipts

Every claim in this project — "I ran spec X on tier Y and got metric Z" —
lives here as a single signed JSON file. No receipt, no claim.

## How to submit

1. Run the eval defined in the target spec under `specs/`.
2. Upload your full eval log somewhere durable and public (HF dataset, gist,
   IPFS, S3 with a stable URL). Compute its SHA-256.
3. Fill in a JSON file conforming to [`schema.json`](schema.json) and place
   it at `receipts/<spec_id>/<agent-id>-<short-git-sha>.json`.
4. Sign the canonicalized body (all fields except `signature`) with
   `ssh-keygen -Y sign -f <key> -n baby-ai-receipt-v0`. Paste the signature
   into the `signature.value` field.
5. Open a PR. CI runs `eval/validate_receipt.py` (deferred — until then,
   maintainers validate by hand).

## What CI checks (or will, once implemented)

- JSON Schema validity against `schema.json`.
- `log_sha256` matches the file at `log_uri`.
- Signature verifies against the `agent.public_key` declared in the receipt
  (or against a previously-recorded key for the same `agent.id`).
- `dataset_sha256` matches `dataset_uri` if both are provided.
- For HF model revisions, the SHA exists on the Hub.

## Naming convention

```
receipts/<spec_id>/<agent-id>-<7-char-git-sha>.json
```

Example: `receipts/perception-smart-moment/octocat-3f5a1c2.json`.

If you re-run after fixing a bug, **do not delete the old receipt**. Submit
a new one with `supersedes` set to the old receipt's SHA-256.

## Why this matters

Open-spec projects fail when claims aren't reproducible. This directory is
the project's evidence base — promotion of a spec from `proposed` to
`active` to `implemented` is gated on receipts here, not on conversation.
See [`specs/05-eval.md`](../specs/05-eval.md) for the contract.
