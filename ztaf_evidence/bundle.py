"""The escalation evidence bundle (ZT-013).

OVR-1: escalation transfers a decision to a human carrying a complete
bundle — context, matched rule, proposed action, options, and provenance.
OVR-3: the bundle is assembled by the oversight path outside the model
context. The decision record carries only the bundle's hash (the
``evidence_bundle_hash`` field), so sensitive payload never enters the
record while remaining provable.
"""

from __future__ import annotations

from typing import Any

from .store import canonical_bytes  # same canonical form
import hashlib

HASH_PREFIX = "zt-sha256:"

REQUIRED_CONTEXT = [
    "decision_class",   # the class the action was evaluated under
    "matched_rule",     # the rule that triggered escalation
    "proposed_action",  # what the agent proposed (payload allowed here)
    "options",          # the choices presented to the approver
    "provenance",       # mandate_id/mandate_hash and task identity
]


def assemble(context: dict, bundle_id: str, created: str) -> dict:
    """Assemble and hash a bundle. Raises if the context is incomplete
    (OVR-1: an approver never rules on a mystery)."""
    missing = [k for k in REQUIRED_CONTEXT if k not in context]
    if missing:
        raise ValueError(f"evidence bundle context incomplete: {missing}")
    bundle = {
        "zt_bundle_version": "0.1.0",
        "bundle_id": bundle_id,
        "created": created,
        "context": context,
    }
    bundle["bundle_hash"] = HASH_PREFIX + hashlib.sha256(canonical_bytes(bundle)).hexdigest()
    return bundle


def verify(bundle: dict) -> bool:
    body = {k: v for k, v in bundle.items() if k != "bundle_hash"}
    expected = HASH_PREFIX + hashlib.sha256(canonical_bytes(body)).hexdigest()
    return bundle.get("bundle_hash") == expected
