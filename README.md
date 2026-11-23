# ztaf-evidence

The evidence-plane reference for the Zero-Trust Agent Framework: the hash-chained decision-record store, batch Merkle roots (RFC 6962-style), independent verification, the evidence-bundle schema, and the transparency anchoring profile (SCITT / RFC 9943).

| Field | Value |
|---|---|
| Authority | Reference implementation + profile — the normative record fields live in [ztaf-spec](https://github.com/Zero-TAF/ztaf-spec) (decision record document) |
| Tier | T3 (substrate) |
| Wave | W3 |
| Version | 0.1.0 |
| Status | Active |
| Licence | MIT |

## What this repository owns

- `ztaf_evidence/store.py` — the append-only, hash-chained decision-record store: record hashing (transparency-attachment-safe), chain linking from `zt-genesis`, full-chain verification, RFC 6962-style batch roots, exports with a checkable head.
- `ztaf_evidence/bundle.py` — the escalation evidence bundle (ZT-013): complete-context assembly (OVR-1), canonical hashing; the record carries only the bundle hash.
- `schemas/` — the store-export envelope and the evidence-bundle schema (JSON Schema draft 2020-12).
- `docs/evidence-store-specification-scope.md` — the store semantics: chain, batch root, export head, the three-step independent-verification protocol, AOP SEC-8 compatibility notes.
- `docs/transparency-anchoring-profile.md` — the TG-3+ anchoring profile: the SCITT/RFC 9943 mapping (batch root as Signed Statement payload), operational rules (order, degradation-not-deletion, independence, currency).
- `tests/` — 13 tests: chain verification, tamper detection (payload, splice, forged head), required-field enforcement (approver, bundle reference), transparency-attachment hash stability, bundle integrity.

## What this repository does not own

- The normative decision-record fields — [ztaf-spec](https://github.com/Zero-TAF/ztaf-spec).
- The transparency service itself — any SCITT-conformant service qualifies; this repo defines the mapping, not the service.
- The enforcement loop that emits records — `ztaf-reference-harness` (Wave 4).
- Mandate verification — `ztaf-mandate` (Wave 3 sibling).

## Status and scope warning

**Reference only.** In-memory store, standard library only, no persistence layer, no network. The chain semantics, the root definition, and the verification protocol are the tested specification; production stores implement the same semantics over durable storage.

## Running

```bash
python -m unittest discover -s tests -v
```

No dependencies beyond the standard library.
