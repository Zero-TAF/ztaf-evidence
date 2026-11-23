"""Evidence store and bundle tests (run from repo root)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ztaf_evidence.bundle import assemble, verify  # noqa: E402
from ztaf_evidence.store import EvidenceStore, GENESIS, StoreError  # noqa: E402


def record(n, decision="permit", **extra):
    base = {
        "zt_record_version": "0.1.0",
        "record_id": f"rec-{n:04d}",
        "timestamp": "2026-11-23T00:00:00Z",
        "task_identity": f"task-{n:04d}",
        "mandate_id": "ZT-MND-X",
        "mandate_hash": "zt-sha256:" + "ab" * 32,
        "decision_class": "refund-issue",
        "action": {"tool": "payments-api", "operation": "refund",
                   "parameters_hash": "zt-sha256:" + "cd" * 32},
        "rule_applied": "POL-REFUND-1",
        "decision": decision,
        "required_grade": "TG-2",
        "evidenced_grade": "TG-2",
    }
    base.update(extra)
    return base


class TestChain(unittest.TestCase):
    def test_append_and_verify(self):
        store = EvidenceStore()
        first = store.append(record(1))
        self.assertEqual(first["previous_record_hash"], GENESIS)
        second = store.append(record(2, decision="deny"))
        self.assertEqual(second["previous_record_hash"], first["record_hash"])
        ok, reason = store.verify()
        self.assertTrue(ok, reason)

    def test_tamper_detected(self):
        store = EvidenceStore()
        store.append(record(1))
        store.append(record(2))
        exported = store.export()
        exported["records"][1]["decision"] = "approve"  # forge a permit into an approval
        ok, reason = EvidenceStore.verify_export(exported)
        self.assertFalse(ok)
        self.assertIn("mismatch", reason)

    def test_link_break_detected(self):
        store = EvidenceStore()
        store.append(record(1))
        store.append(record(2))
        exported = store.export()
        del exported["records"][0]  # splicing history breaks the link
        ok, reason = EvidenceStore.verify_export(exported)
        self.assertFalse(ok)
        self.assertIn("chain link broken", reason)

    def test_required_fields(self):
        store = EvidenceStore()
        bad = record(1)
        del bad["mandate_hash"]
        with self.assertRaises(StoreError):
            store.append(bad)

    def test_approval_requires_approver(self):
        store = EvidenceStore()
        with self.assertRaises(StoreError):
            store.append(record(1, decision="approve"))

    def test_escalation_requires_bundle_reference(self):
        store = EvidenceStore()
        with self.assertRaises(StoreError):
            store.append(record(1, decision="escalate"))

    def test_transparency_does_not_change_record_hash(self):
        store = EvidenceStore()
        r = store.append(record(1))
        h1 = r["record_hash"]
        r["transparency"] = {"statement_ref": "scitt:xyz", "receipt": {"a": 1}}
        self.assertEqual(r["record_hash"], h1)


class TestBatchRoot(unittest.TestCase):
    def test_deterministic_and_sensitive(self):
        store = EvidenceStore()
        store.append(record(1))
        root_one = store.batch_root()
        self.assertEqual(store.batch_root(), root_one)
        store.append(record(2))
        self.assertNotEqual(store.batch_root(), root_one)

    def test_head_matches_on_export(self):
        store = EvidenceStore()
        store.append(record(1))
        store.append(record(2))
        store.append(record(3))
        exported = store.export()
        self.assertEqual(exported["head"]["record_count"], 3)
        ok, reason = EvidenceStore.verify_export(exported)
        self.assertTrue(ok, reason)

    def test_head_catches_batch_root_tamper(self):
        store = EvidenceStore()
        store.append(record(1))
        exported = store.export()
        exported["head"]["batch_root"] = "zt-sha256:" + "00" * 32
        ok, reason = EvidenceStore.verify_export(exported)
        self.assertFalse(ok)
        self.assertIn("batch_root", reason)


class TestBundle(unittest.TestCase):
    def context(self):
        return {
            "decision_class": "refund-issue",
            "matched_rule": "POL-REFUND-1: above EUR 200 escalates",
            "proposed_action": {"tool": "payments-api", "operation": "refund",
                                 "amount": 250, "customer": "C-0007"},
            "options": ["approve", "deny", "request-more-context"],
            "provenance": {"mandate_id": "ZT-MND-VEC-0003",
                            "task_identity": "task-0007"},
        }

    def test_assemble_and_verify(self):
        bundle = assemble(self.context(), "bundle-0001", "2026-11-23T00:00:00Z")
        self.assertTrue(verify(bundle))

    def test_tamper_detected(self):
        bundle = assemble(self.context(), "bundle-0001", "2026-11-23T00:00:00Z")
        bundle["context"]["proposed_action"]["amount"] = 2500
        self.assertFalse(verify(bundle))

    def test_incomplete_context_raises(self):
        bad = self.context()
        del bad["options"]
        with self.assertRaises(ValueError):
            assemble(bad, "bundle-0002", "2026-11-23T00:00:00Z")


if __name__ == "__main__":
    unittest.main()
