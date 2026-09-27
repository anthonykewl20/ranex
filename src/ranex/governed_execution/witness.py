"""External witness — DSSE-wrapped verdicts anchored in a Rekor log (ADR-067).

After ``publish_verdict``, an opt-in ``--witness`` wraps the canonical verdict
envelope bytes in a DSSE envelope (pure Ed25519 over PAE by the verdict signer),
submits it as a Rekor ``dsse`` entry, and stores the returned inclusion proof
beside the verdict as ``<subject>.witness.json``. ``journal verify
--against-verdict --witnessed`` recomputes the payload digest, verifies the
inclusion proof against the pinned log public key, and refuses when the local
verdict no longer matches what the log holds.

Stdlib HTTP only. No new runtime dependency. The log URL defaults to the public
Sigstore instance and may be overridden with ``RANEX_WITNESS_URL``.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519

from ranex.foundation import atomic_writer
from ranex.foundation.dsse import PAYLOAD_TYPE_VERDICT_V2, sign_envelope
from ranex.foundation.merkle import leaf_hash, verify_inclusion
from ranex.foundation.signing import _decode

DEFAULT_WITNESS_URL = "https://rekor.sigstore.dev"
WITNESS_URL_VARIABLE = "RANEX_WITNESS_URL"
WITNESS_SCHEMA = "ranex-witness-v1"
DEFAULT_LOG_PUBLIC_KEY = "governance/rekor_public_key.pem"

# Operational refusal when --witness is set and the log cannot take the entry.
WITNESS_REFUSAL = "E-WITNESS"


def witness_path_for(verdict_path: Path) -> Path:
    """``subject.json`` → ``subject.witness.json`` beside it."""

    return verdict_path.with_name(verdict_path.stem + ".witness.json")


def _log_url() -> str:
    configured = os.environ.get(WITNESS_URL_VARIABLE, "").strip()
    return configured.rstrip("/") if configured else DEFAULT_WITNESS_URL


def _pem_public_key(raw_public_key: str) -> bytes:
    """SPKI PEM for the Ed25519 verifier material Rekor's dsse type expects."""

    public = ed25519.Ed25519PublicKey.from_public_bytes(
        _decode(raw_public_key, expected=32, field="public key")
    )
    return public.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def _payload_digest(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _post_dsse(log_url: str, envelope: dict[str, Any], verifier_pem: bytes) -> dict[str, Any]:
    """Submit one DSSE envelope; return the single-entry response map.

    An HTTP 409 from Rekor means an equivalent entry is already in the log.
    That is success for witnessing: fetch the existing entry by the UUID the
    refusal names and return it in the same shape as a fresh 201.
    """

    body = {
        "apiVersion": "0.0.1",
        "kind": "dsse",
        "spec": {
            "proposedContent": {
                "envelope": json.dumps(envelope, separators=(",", ":"), ensure_ascii=False),
                "verifiers": [base64.standard_b64encode(verifier_pem).decode("ascii")],
            }
        },
    }
    request = urllib.request.Request(
        f"{log_url}/api/v1/log/entries",
        data=json.dumps(body, separators=(",", ":")).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        if exc.code == 409:
            uuid = _uuid_from_conflict(detail)
            return _get_entry(log_url, uuid)
        raise ValueError(
            f"{WITNESS_REFUSAL}: log refused the entry (HTTP {exc.code}): {detail[:500]}"
        ) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ValueError(
            f"{WITNESS_REFUSAL}: cannot reach transparency log at {log_url}: {exc}"
        ) from exc
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{WITNESS_REFUSAL}: log returned non-JSON") from exc
    if not isinstance(parsed, dict) or len(parsed) != 1:
        raise ValueError(f"{WITNESS_REFUSAL}: log returned an unexpected entry shape")
    return parsed


def _uuid_from_conflict(detail: str) -> str:
    """Pull the existing entry UUID out of a Rekor 409 body."""

    try:
        payload = json.loads(detail)
        message = payload.get("message", "")
    except json.JSONDecodeError:
        message = detail
    marker = "UUID "
    index = message.rfind(marker)
    if index < 0:
        raise ValueError(
            f"{WITNESS_REFUSAL}: log reported a duplicate without a UUID: {detail[:500]}"
        )
    uuid = message[index + len(marker) :].strip().rstrip(".")
    if not uuid or any(ch.isspace() for ch in uuid):
        raise ValueError(
            f"{WITNESS_REFUSAL}: log reported a duplicate without a UUID: {detail[:500]}"
        )
    return uuid


def _get_entry(log_url: str, entry_uuid: str) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{log_url}/api/v1/log/entries/{entry_uuid}",
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read()
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ValueError(
            f"{WITNESS_REFUSAL}: cannot fetch coalesced entry {entry_uuid}: {exc}"
        ) from exc
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{WITNESS_REFUSAL}: coalesced entry is not JSON") from exc
    if not isinstance(parsed, dict) or len(parsed) != 1:
        raise ValueError(f"{WITNESS_REFUSAL}: coalesced entry has unexpected shape")
    return parsed


def _witness_record(
    *,
    log_url: str,
    entry_uuid: str,
    entry: dict[str, Any],
    payload_digest: str,
) -> dict[str, Any]:
    verification = entry.get("verification")
    if not isinstance(verification, dict):
        raise ValueError(f"{WITNESS_REFUSAL}: log entry omits verification")
    proof = verification.get("inclusionProof")
    if not isinstance(proof, dict):
        raise ValueError(f"{WITNESS_REFUSAL}: log entry omits inclusion proof")
    required_proof = ("logIndex", "treeSize", "rootHash", "hashes", "checkpoint")
    if any(key not in proof for key in required_proof):
        raise ValueError(f"{WITNESS_REFUSAL}: inclusion proof is incomplete")
    if not isinstance(proof["hashes"], list) or not all(
        isinstance(item, str) for item in proof["hashes"]
    ):
        raise ValueError(f"{WITNESS_REFUSAL}: inclusion proof hashes are malformed")
    body = entry.get("body")
    if not isinstance(body, str) or not body:
        raise ValueError(f"{WITNESS_REFUSAL}: log entry omits body")
    for field in ("logIndex", "integratedTime", "logID"):
        if field not in entry:
            raise ValueError(f"{WITNESS_REFUSAL}: log entry omits {field}")
    return {
        "schema": WITNESS_SCHEMA,
        "log_url": log_url,
        "entry_uuid": entry_uuid,
        "log_index": entry["logIndex"],
        "integrated_time": entry["integratedTime"],
        "log_id": entry["logID"],
        "payload_digest": payload_digest,
        "body": body,
        "inclusion_proof": {
            "log_index": proof["logIndex"],
            "tree_size": proof["treeSize"],
            "root_hash": proof["rootHash"],
            "hashes": list(proof["hashes"]),
            "checkpoint": proof["checkpoint"],
        },
    }


def witness_verdict(
    *,
    verdict_path: Path,
    verdict_bytes: bytes,
    private_key: str,
    public_key: str,
    root: Path,
) -> Path:
    """Submit the verdict to the log and write ``<stem>.witness.json``.

    The caller must already have published ``verdict_bytes`` at ``verdict_path``.
    On refusal this raises and the caller removes the published verdict so
    ``--witness`` never leaves an unwitnessed file.
    """

    envelope = sign_envelope(
        payload_type=PAYLOAD_TYPE_VERDICT_V2,
        payload=verdict_bytes,
        private_key=private_key,
    )
    log_url = _log_url()
    response = _post_dsse(log_url, envelope, _pem_public_key(public_key))
    entry_uuid, entry = next(iter(response.items()))
    if not isinstance(entry, dict):
        raise ValueError(f"{WITNESS_REFUSAL}: log entry is not an object")
    record = _witness_record(
        log_url=log_url,
        entry_uuid=entry_uuid,
        entry=entry,
        payload_digest=_payload_digest(verdict_bytes),
    )
    path = witness_path_for(verdict_path)
    atomic_writer.write_atomic(
        path,
        (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        root=root,
    )
    return path


def _verify_checkpoint(checkpoint: str, public_key_pem: bytes) -> bytes:
    """Return the root hash the signed checkpoint attests, or raise."""

    parts = checkpoint.split("\n\n", 1)
    if len(parts) != 2:
        raise ValueError(f"{WITNESS_REFUSAL}: checkpoint is malformed")
    note, signatures = parts
    note_bytes = (note + "\n").encode("utf-8")
    lines = [line for line in note.split("\n") if line]
    if len(lines) < 3:
        raise ValueError(f"{WITNESS_REFUSAL}: checkpoint note is incomplete")
    try:
        root = base64.standard_b64decode(lines[2])
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{WITNESS_REFUSAL}: checkpoint root is not base64") from exc
    if len(root) != 32:
        raise ValueError(f"{WITNESS_REFUSAL}: checkpoint root has wrong length")
    public = serialization.load_pem_public_key(public_key_pem)
    if not isinstance(public, ec.EllipticCurvePublicKey):
        raise ValueError(f"{WITNESS_REFUSAL}: log public key is not ECDSA")
    verified = False
    for line in signatures.strip().split("\n"):
        pieces = line.split(" ", 2)
        if len(pieces) != 3:
            continue
        try:
            blob = base64.standard_b64decode(pieces[2])
        except (ValueError, TypeError):
            continue
        if len(blob) <= 4:
            continue
        try:
            public.verify(blob[4:], note_bytes, ec.ECDSA(hashes.SHA256()))
        except InvalidSignature:
            continue
        verified = True
        break
    if not verified:
        raise ValueError(f"{WITNESS_REFUSAL}: checkpoint signature does not verify")
    return root


def verify_witness(
    *,
    verdict_path: Path,
    witness_path: Path,
    log_public_key_path: Path,
) -> None:
    """Refuse unless the local verdict matches a log-anchored witness.

    Raises ``ValueError`` with an ``E-WITNESS`` prefix on every failure mode.
    """

    if not witness_path.is_file():
        raise ValueError(f"{WITNESS_REFUSAL}: witness file does not exist: {witness_path}")
    if not verdict_path.is_file():
        raise ValueError(f"{WITNESS_REFUSAL}: verdict does not exist: {verdict_path}")
    if not log_public_key_path.is_file():
        raise ValueError(
            f"{WITNESS_REFUSAL}: pinned log public key does not exist: {log_public_key_path}"
        )
    try:
        record = json.loads(witness_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{WITNESS_REFUSAL}: witness file is not readable JSON") from exc
    if not isinstance(record, dict) or record.get("schema") != WITNESS_SCHEMA:
        raise ValueError(f"{WITNESS_REFUSAL}: witness schema is not {WITNESS_SCHEMA}")
    verdict_bytes = verdict_path.read_bytes()
    local_digest = _payload_digest(verdict_bytes)
    witnessed_digest = record.get("payload_digest")
    if witnessed_digest != local_digest:
        raise ValueError(
            f"{WITNESS_REFUSAL}: local verdict digest {local_digest} does not "
            f"match witnessed digest {witnessed_digest!r}"
        )
    proof = record.get("inclusion_proof")
    body_b64 = record.get("body")
    if not isinstance(proof, dict) or not isinstance(body_b64, str):
        raise ValueError(f"{WITNESS_REFUSAL}: witness is missing proof or body")
    try:
        body = base64.b64decode(body_b64, validate=True)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{WITNESS_REFUSAL}: witness body is not base64") from exc
    try:
        hashes = [bytes.fromhex(item) for item in proof["hashes"]]
        root_hex = proof["root_hash"]
        if not isinstance(root_hex, str):
            raise ValueError("root")
        stored_root = bytes.fromhex(root_hex)
        index = int(proof["log_index"])
        size = int(proof["tree_size"])
        checkpoint = proof["checkpoint"]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{WITNESS_REFUSAL}: inclusion proof fields are malformed") from exc
    if not isinstance(checkpoint, str):
        raise ValueError(f"{WITNESS_REFUSAL}: checkpoint is malformed")
    pinned_root = _verify_checkpoint(checkpoint, log_public_key_path.read_bytes())
    if pinned_root != stored_root:
        raise ValueError(
            f"{WITNESS_REFUSAL}: checkpoint root does not match inclusion proof root"
        )
    if not verify_inclusion(
        index=index,
        size=size,
        leaf=leaf_hash(body),
        hashes=hashes,
        root=stored_root,
    ):
        raise ValueError(f"{WITNESS_REFUSAL}: inclusion proof does not verify")
    try:
        logged = json.loads(body.decode("utf-8"))
        payload_hash = logged["spec"]["payloadHash"]["value"]
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError(f"{WITNESS_REFUSAL}: logged body is not a dsse entry") from exc
    if payload_hash != local_digest.removeprefix("sha256:"):
        raise ValueError(
            f"{WITNESS_REFUSAL}: logged payload hash does not match local verdict"
        )
