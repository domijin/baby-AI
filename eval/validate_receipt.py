#!/usr/bin/env python3
"""eval/validate_receipt.py — verify a baby-AI evaluation receipt.

Checks (in order):
  1. JSON Schema validation against receipts/schema.json
  2. log_sha256 matches the file at log_uri (skipped with --no-network)
  3. signature.value verifies over the canonicalized receipt body
     using agent.public_key (ssh-sig only; sigstore/minisign deferred)
  4. (advisory) dataset_sha256 matches dataset_uri, if both are present
  5. (advisory) HF model revision exists at huggingface.co

Canonicalization (for both signing and verification):
  json.dumps(body_without_signature, sort_keys=True,
             separators=(',', ':'), ensure_ascii=False).encode('utf-8')

Exit codes:
  0  receipt valid
  1  schema invalid
  2  log hash mismatch
  3  signature invalid
  4  advisory check failed (only with --strict)
  5  IO / dependency / unsupported scheme

Usage:
  python eval/validate_receipt.py path/to/receipt.json
  python eval/validate_receipt.py path/to/receipt.json --strict
  python eval/validate_receipt.py path/to/receipt.json --no-network
  python eval/validate_receipt.py path/to/receipt.json --no-signature
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "receipts" / "schema.json"
SIGNATURE_NAMESPACE = "baby-ai-receipt-v0"


class ValidationError(Exception):
    def __init__(self, exit_code: int, message: str) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def canonicalize(body: dict) -> bytes:
    return json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def schema_check(receipt: dict) -> None:
    try:
        import jsonschema
    except ImportError as e:
        raise ValidationError(
            5,
            "jsonschema not installed (pip install -r eval/requirements.txt)",
        ) from e
    schema = json.loads(SCHEMA_PATH.read_text())
    try:
        jsonschema.validate(receipt, schema)
    except jsonschema.ValidationError as e:
        path = "/".join(str(p) for p in e.absolute_path) or "<root>"
        raise ValidationError(1, f"schema: {e.message} at {path}") from e


def fetch(uri: str, timeout_s: int = 30) -> bytes:
    parsed = urllib.parse.urlparse(uri)
    if parsed.scheme in ("", "file"):
        return Path(parsed.path or uri).read_bytes()
    if parsed.scheme not in ("http", "https"):
        raise ValidationError(5, f"unsupported uri scheme: {parsed.scheme}")
    req = urllib.request.Request(uri, headers={"User-Agent": "baby-ai-validate/0.1"})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        return resp.read()


def log_hash_check(receipt: dict, allow_network: bool) -> bool:
    if not allow_network:
        return False
    log_uri = receipt["log_uri"]
    expected = receipt["log_sha256"]
    try:
        data = fetch(log_uri)
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(5, f"log fetch failed ({log_uri}): {e}") from e
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        raise ValidationError(
            2, f"log_sha256 mismatch: expected {expected}, got {actual}"
        )
    return True


def signature_check(receipt: dict) -> None:
    sig = receipt["signature"]
    scheme = sig["scheme"]
    if scheme != "ssh-sig":
        raise ValidationError(
            5, f"signature scheme '{scheme}' not yet supported by validator"
        )
    pubkey = receipt.get("agent", {}).get("public_key")
    if not pubkey:
        raise ValidationError(
            3, "agent.public_key is required for signature verification"
        )
    if shutil.which("ssh-keygen") is None:
        raise ValidationError(5, "ssh-keygen not found in PATH")

    namespace = sig.get("namespace", SIGNATURE_NAMESPACE)
    identity = receipt.get("agent", {}).get("id", "agent")
    body = {k: v for k, v in receipt.items() if k != "signature"}
    canonical = canonicalize(body)

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        allowed = tmp / "allowed_signers"
        allowed.write_text(f"{identity} {pubkey}\n")
        sig_path = tmp / "sig"
        sig_path.write_text(sig["value"])
        proc = subprocess.run(
            [
                "ssh-keygen", "-Y", "verify",
                "-f", str(allowed),
                "-I", identity,
                "-n", namespace,
                "-s", str(sig_path),
            ],
            input=canonical,
            capture_output=True,
        )
    if proc.returncode != 0:
        raise ValidationError(
            3, f"signature: ssh-keygen verify failed:\n{proc.stderr.decode().strip()}"
        )


def dataset_hash_check(
    receipt: dict, allow_network: bool, strict: bool
) -> bool:
    refs = receipt.get("artifact_refs", {})
    uri = refs.get("dataset_uri")
    expected = refs.get("dataset_sha256")
    if not uri or not expected or not allow_network:
        return False
    try:
        data = fetch(uri)
    except Exception as e:
        msg = f"dataset fetch failed ({uri}): {e}"
        if strict:
            raise ValidationError(4, msg) from e
        print(f"warn dataset {msg}", file=sys.stderr)
        return False
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        msg = f"dataset_sha256 mismatch: expected {expected}, got {actual}"
        if strict:
            raise ValidationError(4, msg)
        print(f"warn dataset {msg}", file=sys.stderr)
        return False
    return True


def hf_revision_check(
    receipt: dict, allow_network: bool, strict: bool
) -> bool:
    refs = receipt.get("artifact_refs", {})
    repo = refs.get("model_repo")
    rev = refs.get("model_revision")
    if not repo or not rev or not allow_network:
        return False
    url = f"https://huggingface.co/api/models/{repo}/revision/{rev}"
    try:
        req = urllib.request.Request(url, method="HEAD",
                                     headers={"User-Agent": "baby-ai-validate/0.1"})
        urllib.request.urlopen(req, timeout=15).close()
    except Exception as e:
        msg = f"HF revision check failed ({repo}@{rev}): {e}"
        if strict:
            raise ValidationError(4, msg) from e
        print(f"warn hf-revision {msg}", file=sys.stderr)
        return False
    return True


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("receipt", type=Path, help="path to receipt JSON")
    ap.add_argument("--strict", action="store_true",
                    help="treat advisory checks as errors")
    ap.add_argument("--no-network", action="store_true",
                    help="skip log fetch, dataset fetch, HF check")
    ap.add_argument("--no-signature", action="store_true",
                    help="skip signature verification (maintainers only)")
    args = ap.parse_args()

    try:
        receipt = json.loads(args.receipt.read_text())
    except Exception as e:
        print(f"fail read {e}", file=sys.stderr)
        sys.exit(5)

    allow_net = not args.no_network

    try:
        schema_check(receipt)
        print("ok schema")

        if log_hash_check(receipt, allow_net):
            print("ok log_sha256")
        else:
            print("skip log_sha256 (--no-network)")

        if not args.no_signature:
            signature_check(receipt)
            print("ok signature")
        else:
            print("skip signature (--no-signature)")

        if dataset_hash_check(receipt, allow_net, args.strict):
            print("ok dataset_sha256")
        else:
            print("skip dataset_sha256 (not asserted or --no-network)")

        if hf_revision_check(receipt, allow_net, args.strict):
            print("ok hf-revision")
        else:
            print("skip hf-revision (not asserted or --no-network)")

        print("ok receipt valid")
    except ValidationError as e:
        print(f"fail {e}", file=sys.stderr)
        sys.exit(e.exit_code)


if __name__ == "__main__":
    main()
