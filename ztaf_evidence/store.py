"""The hash-chained decision-record store.

Reference implementation of the evidence plane's core (ztaf-spec, decision
record document; ZT-NM-EVD-1..6). Pure standard library: the store's own
integrity needs only SHA-256 and canonical serialisation. Transparency
anchoring is a separate concern (docs/transparency-anchoring-profile.md).

Rules implemented here:
- ``record_hash``  = canonical hash of the record *without* ``record_hash``,
  ``previous_record_hash``, and ``transparency`` (the anchor is attached
  after the fact and must not change the record's own hash);
- ``previous_record_hash`` links to the prior record; the store's genesis
  value is ``zt-genesis`` (EVD-2);
- verification recomputes every hash and every link (EVD-3);
- the batch root is the RFC 6962-style Merkle tree head over the record
  digests (leaf = SHA-256(0x00 || d), node = SHA-256(0x01 || l || r)) —
  the value a transparency service would anchor at TG-3+;
- append is the only mutation; corrections are new records referencing the
  record they correct (EVD-4).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, List, Optional

STORE_VERSION = "0.1.0"
GENESIS = "zt-genesis"
HASH_PREFIX = "zt-sha256:"

REQUIRED_FIELDS = [
    "zt_record_version", "record_id", "timestamp", "task_identity",
    "mandate_id", "mandate_hash", "decision_class", "action",
    "rule_applied", "decision", "required_grade", "evidenced_grade",
    "record_hash", "previous_record_hash",
]
DECISIONS = {"permit", "deny", "escalate", "approve"}
GRADES = ["TG-0", "TG-1", "TG-2", "TG-3", "TG-4"]
UNHASHED_FIELDS = {"record_hash", "previous_record_hash", "transparency"}


def canonical_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def record_content_hash(record: dict) -> str:
    content = {k: v for k, v in record.items() if k not in UNHASHED_FIELDS}
    return HASH_PREFIX + hashlib.sha256(canonical_bytes(content)).hexdigest()


def _digest32(hash_string: str) -> bytes:
    if not hash_string.startswith(HASH_PREFIX):
        raise ValueError(f"not a zt-sha256 hash: {hash_string!r}")
    return bytes.fromhex(hash_string[len(HASH_PREFIX):])


def merkle_root(leaves: List[bytes]) -> bytes:
    """RFC 6962-style Merkle tree head over 32-byte leaf digests."""
    if not leaves:
        return hashlib.sha256(b"").digest()
    if len(leaves) == 1:
        return hashlib.sha256(b"\x00" + leaves[0]).digest()
    k = 1
    while k * 2 < len(leaves):
        k *= 2
    left = merkle_root(leaves[:k])
    right = merkle_root(leaves[k:])
    return hashlib.sha256(b"\x01" + left + right).digest()


class StoreError(Exception):
    pass


class EvidenceStore:
    """An in-memory append-only store. Production stores persist records and
    serve exports; the chain and root semantics are identical."""

    def __init__(self):
        self._records: List[dict] = []

    def append(self, record: dict) -> dict:
        # record_hash and previous_record_hash are computed by the store;
        # everything else must be present on intake.
        intake_required = [f for f in REQUIRED_FIELDS
                           if f not in ("record_hash", "previous_record_hash")]
        missing = [f for f in intake_required if f not in record]
        if missing:
            raise StoreError(f"record missing required fields: {missing}")
        if record["decision"] not in DECISIONS:
            raise StoreError(f"unknown decision: {record['decision']}")
        for g in ("required_grade", "evidenced_grade"):
            if record[g] not in GRADES:
                raise StoreError(f"unknown grade: {record[g]}")
        if record["decision"] == "approve" and not record.get("approver"):
            raise StoreError("an approval record MUST carry the approver (OVR-4)")
        if record["decision"] == "escalate" and not record.get("evidence_bundle_hash"):
            raise StoreError("an escalation record MUST reference its evidence bundle (OVR-1)")

        stored = dict(record)
        stored["previous_record_hash"] = (
            self._records[-1]["record_hash"] if self._records else GENESIS
        )
        stored["record_hash"] = record_content_hash(stored)
        self._records.append(stored)
        return dict(stored)

    def verify(self) -> tuple[bool, Optional[str]]:
        previous = GENESIS
        for i, record in enumerate(self._records):
            if record["previous_record_hash"] != previous:
                return False, f"chain link broken at record {i}"
            if record["record_hash"] != record_content_hash(record):
                return False, f"record hash mismatch at record {i}"
            previous = record["record_hash"]
        return True, None

    def batch_root(self) -> str:
        """The Merkle tree head over all record digests (RFC 6962-style)."""
        leaves = [_digest32(r["record_hash"]) for r in self._records]
        return HASH_PREFIX + merkle_root(leaves).hex()

    def export(self) -> dict:
        return {
            "zt_store_version": STORE_VERSION,
            "records": [dict(r) for r in self._records],
            "head": {
                "record_count": len(self._records),
                "last_record_hash": (
                    self._records[-1]["record_hash"] if self._records else GENESIS
                ),
                "batch_root": self.batch_root(),
            },
        }

    @staticmethod
    def verify_export(exported: dict) -> tuple[bool, Optional[str]]:
        store = EvidenceStore()
        store._records = [dict(r) for r in exported.get("records", [])]
        ok, reason = store.verify()
        if not ok:
            return False, reason
        head = exported.get("head", {})
        if head.get("record_count") != len(store._records):
            return False, "head record_count mismatch"
        if head.get("last_record_hash") != (
            store._records[-1]["record_hash"] if store._records else GENESIS
        ):
            return False, "head last_record_hash mismatch"
        if head.get("batch_root") != store.batch_root():
            return False, "head batch_root mismatch"
        return True, None
