# The Transparency Anchoring Profile (TG-3+)

**Version 0.1.0. Profile.** How Zero-TAF evidence anchors to an independent transparency service, satisfying EVD-3 and SEC-14: verifiability by parties who do not trust the operator. **Informative on the wire** — the SCITT API surfaces are still consolidating (receipts profiles in progress at the IETF); this profile pins the mapping, not the bytes. Pinning the bytes is a change request once the receipts profiles publish.

## 1. Substrate

The substrate is the IETF SCITT architecture (**RFC 9943**, Proposed Standard, June 2026): issuers register COSE **Signed Statements** about artifacts with **Transparency Services**, and receive verifiable COSE **transparency receipts** (Merkle-inclusion proofs). Lineage: Certificate Transparency (**RFC 9162**); deployment precedent: Sigstore Rekor, including its model-transparency extension.

## 2. Mapping

| Zero-TAF artifact | SCITT artifact |
|---|---|
| Batch root over decision records (store document §2) | The payload digest of a Signed Statement |
| The operator, as evidence custodian | The Statement issuer |
| The Transparency Service | SCITT Transparency Service |
| `transparency.receipt` in a decision record | The returned transparency receipt (Merkle-inclusion proof) |
| `transparency.statement_ref` | The service's statement identifier |
| Independent verifier | Any relying party with the receipt, the root, and no trust in the operator |

What is registered is the **batch root** — one Signed Statement per batch, not per decision. A verifier holding a receipt for batch root R can confirm that record *i* is in the operator's evidence by asking the operator for an inclusion proof of record *i*'s hash against R, and checking the receipt against the service. The operator cannot forge R, and the service cannot fabricate the operator's statements (COSE signing key).

## 3. Operational rules

1. **Order:** records are written to the append-only store *before* anchoring (ZT-ARC-3); anchoring never blocks the enforcement loop, it follows it.
2. **Degradation, not deletion:** a lost or unavailable anchor degrades the evidenced grade to TG-2 for the affected classes (grade-sufficiency rule, ztaf-spec grades document §3) — the records and the chain survive; only the independence claim lapses. The lapse is observable: the register and the receipts' timestamps show the gap (ZT-ARC-8).
3. **Independence:** the service is not operated by the agent operator; self-anchoring never satisfies TG-3+ (ASM-8).
4. **Currency:** receipts reference the service's signed tree head era; verifiers check freshness within the service's STH policy, mirroring CT gossip practice.

## 4. Candidate services

Any SCITT-conformant Transparency Service qualifies. The profile is deliberately service-agnostic; naming concrete service instances and their policies is a deployment-profile concern, not a framework concern.
