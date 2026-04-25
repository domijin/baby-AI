# eval/

The verification side of [`specs/05-eval.md`](../specs/05-eval.md).

Today this directory contains one tool: a receipt validator. The leaderboard
aggregator (`aggregate.py`) is deferred until at least three independent
receipts exist — there's nothing to aggregate before then.

## Files

- `validate_receipt.py` — JSON Schema + log hash + ssh-sig signature verifier.
- `requirements.txt` — single dependency: `jsonschema`.

## Quickstart

```bash
pip install -r eval/requirements.txt

# Maintainer-style local check (skip network + signature for a quick lint):
python eval/validate_receipt.py path/to/receipt.json --no-network --no-signature

# Full check (matches what CI will run, once CI exists):
python eval/validate_receipt.py path/to/receipt.json
```

## Signing a receipt

Canonicalize the receipt body (everything except the `signature` field) with
deterministic JSON, then sign with `ssh-keygen -Y sign`:

```bash
python -c "import json,sys; r=json.load(open(sys.argv[1])); r.pop('signature',None); \
sys.stdout.write(json.dumps(r, sort_keys=True, separators=(',',':'), ensure_ascii=False))" \
  receipt.json > receipt.canonical

ssh-keygen -Y sign \
  -f ~/.ssh/id_ed25519 \
  -n baby-ai-receipt-v0 \
  receipt.canonical

# Then paste the contents of receipt.canonical.sig (multi-line PEM-ish blob)
# into receipt.json's signature.value, set signature.scheme = "ssh-sig",
# and put your public key into agent.public_key (from `cat ~/.ssh/id_ed25519.pub`).
```

The validator reproduces this canonicalization exactly. See
`canonicalize()` at the top of `validate_receipt.py`.

## Exit codes

| code | meaning                                            |
| ---- | -------------------------------------------------- |
| 0    | valid                                              |
| 1    | schema invalid                                     |
| 2    | log_sha256 mismatch (log fetched, hash didn't match) |
| 3    | signature invalid                                  |
| 4    | advisory check failed (only with `--strict`)       |
| 5    | IO / dependency / unsupported scheme               |

## Scope

The validator does **not** judge whether the metric value is good — only
whether the claim is well-formed and signed by someone who can sign for the
claimed `agent.id`. Spec status promotion (`proposed → active → implemented`)
remains a maintainer judgment informed by validated receipts; see
[`specs/05-eval.md`](../specs/05-eval.md).
