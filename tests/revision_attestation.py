"""Prototipo del verificador de dictámenes. No es un gate operativo.

La firma demuestra posesión de una clave, NO que el firmante esté aislado.
Sólo se puede confiar en ella después de verificar custodia y anclar su clave pública.
"""
import base64
import json
import re
import subprocess
import tempfile
from pathlib import Path

MARKER = "NEXUS_REVIEW_V1"
KEYS = frozenset({"version", "repo", "issue", "pr", "head_sha", "base_sha",
                  "diff_sha256", "report_sha256", "reviewer", "verdict"})
HEX64 = re.compile(r"[a-f0-9]{64}\Z")
HEX40 = re.compile(r"[a-f0-9]{40}\Z")
REVIEWER = "revisor-independiente-piloto-3"


class InvalidAttestation(ValueError):
    """Un dictamen es inválido o su procedencia no es autenticable."""


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidAttestation("JSON_DUPLICATE_KEY")
        result[key] = value
    return result


def canonical_payload(payload):
    """Bytes exactos que el firmante debe firmar con Ed25519."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def parse_comment(comment):
    """Formato: NEXUS_REVIEW_V1, newline, objeto JSON, sin contenido extra."""
    if not isinstance(comment, str) or len(comment.encode("utf-8")) > 8192:
        raise InvalidAttestation("COMMENT_SIZE_INVALID")
    lines = comment.strip().split("\n", 1)
    if len(lines) != 2 or lines[0] != MARKER:
        raise InvalidAttestation("MARKER_INVALID")
    try:
        att = json.loads(lines[1], object_pairs_hook=_unique_pairs)
    except (ValueError, TypeError) as exc:
        raise InvalidAttestation("JSON_INVALID") from exc
    if not isinstance(att, dict) or set(att) != {"payload", "signature"}:
        raise InvalidAttestation("ENVELOPE_INVALID")
    return att


def verify(comment, public_pem, *, repo, issue, pr, head_sha, base_sha):
    """Valida esquema, destino, SHA y firma; no revisa semántica."""
    att = parse_comment(comment)
    payload, sig_b64 = att["payload"], att["signature"]
    if not isinstance(payload, dict) or set(payload) != KEYS:
        raise InvalidAttestation("SCHEMA_INVALID")
    if type(payload["version"]) is not int or payload["version"] != 1:
        raise InvalidAttestation("VERSION_INVALID")
    if type(payload["issue"]) is not int or type(payload["pr"]) is not int:
        raise InvalidAttestation("TYPE_INVALID")
    if payload["repo"] != repo or payload["issue"] != issue or payload["pr"] != pr:
        raise InvalidAttestation("TARGET_MISMATCH")
    for key, expected in (("head_sha", head_sha), ("base_sha", base_sha)):
        if not isinstance(payload[key], str) or not HEX40.fullmatch(payload[key]):
            raise InvalidAttestation("SHA_FORMAT_INVALID")
        if payload[key] != expected:
            raise InvalidAttestation("SHA_MISMATCH")
    if any(not isinstance(payload[x], str) or not HEX64.fullmatch(payload[x])
           for x in ("diff_sha256", "report_sha256")):
        raise InvalidAttestation("DIGEST_INVALID")
    if payload["reviewer"] != REVIEWER:
        raise InvalidAttestation("REVIEWER_UNEXPECTED")
    if payload["verdict"] not in ("APPROVE", "REQUEST_CHANGES", "BLOCK", "STALE"):
        raise InvalidAttestation("VERDICT_INVALID")
    if not isinstance(sig_b64, str) or len(sig_b64) > 128:
        raise InvalidAttestation("SIGNATURE_FORMAT_INVALID")
    try:
        signature = base64.b64decode(sig_b64, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise InvalidAttestation("SIGNATURE_FORMAT_INVALID") from exc
    if len(signature) != 64:
        raise InvalidAttestation("SIGNATURE_LENGTH_INVALID")
    if (not isinstance(public_pem, str) or
            not public_pem.startswith("-----BEGIN PUBLIC KEY-----") or
            len(public_pem) > 4096):
        raise InvalidAttestation("TRUST_ANCHOR_MISSING")
    with tempfile.TemporaryDirectory(prefix="nexus-review-check-") as work:
        root = Path(work)
        (root / "payload.json").write_bytes(canonical_payload(payload))
        (root / "sig.bin").write_bytes(signature)
        (root / "pub.pem").write_text(public_pem, encoding="ascii")
        try:
            outcome = subprocess.run([
                "openssl", "pkeyutl", "-verify", "-pubin", "-inkey", str(root / "pub.pem"),
                "-rawin", "-in", str(root / "payload.json"), "-sigfile", str(root / "sig.bin"),
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=8)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise InvalidAttestation("SIGNATURE_VERIFICATION_ERROR") from exc
    if outcome.returncode != 0:
        raise InvalidAttestation("SIGNATURE_INVALID")
    return payload
