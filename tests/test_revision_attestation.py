"""Pruebas sintéticas del contrato de revisión Ed25519, sin claves de Nexus."""
import base64
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from revision_attestation import InvalidAttestation, canonical_payload, verify

REPO = "Leadhousemx/nexus-piloto-sintetico"
HEAD = "b898a455cbb57135d265116a96b213df6374dfec"
BASE = "e122798c7e07de36caba5592438caac888c81862"
ARGS = dict(repo=REPO, issue=9, pr=3, head_sha=HEAD, base_sha=BASE)


class TestRevisionFirmada(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="test-review-")
        cls.root = Path(cls.temp.name)
        cls.private = cls.root / "private.pem"
        cls.public = cls.root / "public.pem"
        subprocess.run(["openssl", "genpkey", "-algorithm", "ed25519", "-out", str(cls.private)],
                       check=True, capture_output=True)
        subprocess.run(["openssl", "pkey", "-in", str(cls.private), "-pubout", "-out", str(cls.public)],
                       check=True, capture_output=True)
        cls.public_pem = cls.public.read_text()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.payload = dict(
            version=1, repo=REPO, issue=9, pr=3, head_sha=HEAD, base_sha=BASE,
            diff_sha256="1b45c895c890e24a078d3803dc823d2003f6766c482667cef38bc28c4395ac79",
            report_sha256="f" * 64, reviewer="revisor-independiente-piloto-3",
            verdict="APPROVE",
        )

    def envelope(self, payload=None, private=None):
        data = canonical_payload(payload if payload is not None else self.payload)
        source, sig = self.root / "payload.json", self.root / "sig.bin"
        source.write_bytes(data)
        subprocess.run(["openssl", "pkeyutl", "-sign", "-inkey", str(private or self.private),
                        "-rawin", "-in", str(source), "-out", str(sig)],
                       check=True, capture_output=True)
        return "NEXUS_REVIEW_V1\n" + json.dumps({
            "payload": payload if payload is not None else self.payload,
            "signature": base64.b64encode(sig.read_bytes()).decode("ascii"),
        }, separators=(",", ":"))

    def assert_invalid(self, body, reason):
        with self.assertRaises(InvalidAttestation) as raised:
            verify(body, self.public_pem, **ARGS)
        self.assertEqual(str(raised.exception), reason)

    def test_valid(self):
        self.assertEqual(verify(self.envelope(), self.public_pem, **ARGS), self.payload)

    def test_tampered_verdict(self):
        obj = json.loads(self.envelope().split("\n", 1)[1])
        obj["payload"]["verdict"] = "BLOCK"
        self.assert_invalid("NEXUS_REVIEW_V1\n" + json.dumps(obj), "SIGNATURE_INVALID")

    def test_tampered_report_digest(self):
        obj = json.loads(self.envelope().split("\n", 1)[1])
        obj["payload"]["report_sha256"] = "0" * 64
        self.assert_invalid("NEXUS_REVIEW_V1\n" + json.dumps(obj), "SIGNATURE_INVALID")

    def test_stale_sha(self):
        self.payload["head_sha"] = "0" * 40
        self.assert_invalid(self.envelope(), "SHA_MISMATCH")

    def test_wrong_pr(self):
        self.payload["pr"] = 4
        self.assert_invalid(self.envelope(), "TARGET_MISMATCH")

    def test_wrong_issue(self):
        self.payload["issue"] = 8
        self.assert_invalid(self.envelope(), "TARGET_MISMATCH")

    def test_bad_reviewer(self):
        self.payload["reviewer"] = "ingeniero"
        self.assert_invalid(self.envelope(), "REVIEWER_UNEXPECTED")

    def test_missing_public_key(self):
        with self.assertRaisesRegex(InvalidAttestation, "TRUST_ANCHOR_MISSING"):
            verify(self.envelope(), "", **ARGS)

    def test_bad_signature(self):
        obj = json.loads(self.envelope().split("\n", 1)[1])
        obj["signature"] = base64.b64encode(b"a" * 64).decode()
        self.assert_invalid("NEXUS_REVIEW_V1\n" + json.dumps(obj), "SIGNATURE_INVALID")

    def test_duplicate_json_key(self):
        self.assert_invalid('NEXUS_REVIEW_V1\n{"payload":{},"payload":{},"signature":"x"}',
                            "JSON_INVALID")

    def test_no_marker(self):
        self.assert_invalid('{"payload":{},"signature":"x"}', "MARKER_INVALID")

    def test_unknown_key(self):
        self.payload["unsafe"] = "yes"
        self.assert_invalid(self.envelope(), "SCHEMA_INVALID")

    def test_bad_digest(self):
        self.payload["report_sha256"] = "invalid"
        self.assert_invalid(self.envelope(), "DIGEST_INVALID")

    def test_bool_pr_rejected(self):
        self.payload["pr"] = True
        self.assert_invalid(self.envelope(), "TYPE_INVALID")

    def test_other_signer_key_rejected(self):
        other = self.root / "other.pem"
        subprocess.run(["openssl", "genpkey", "-algorithm", "ed25519", "-out", str(other)],
                       check=True, capture_output=True)
        self.assert_invalid(self.envelope(private=other), "SIGNATURE_INVALID")


if __name__ == "__main__":
    unittest.main()
