# The Decision-Record Store

**Version 0.1.0.** The store semantics behind the reference implementation in this repository. The record's fields are normative in [ztaf-spec](https://github.com/Zero-TAF/ztaf-spec) (decision record document); this document specifies the *store*: how records chain, how batches root, and how a third party verifies without trusting the operator (EVD-3, SEC-14).

## 1. The chain

- `record_hash` is the canonical hash (sorted keys, no insignificant whitespace, UTF-8) of the record **excluding** `record_hash`, `previous_record_hash`, and `transparency`. The transparency attachment is applied after the fact and must not change the record's own hash.
- `previous_record_hash` links to the prior record; the genesis value is `zt-genesis` (EVD-2).
- Append is the only mutation. A correction is a new record referencing the record it corrects (EVD-4). An evidence-write failure fails the action closed (EVD-6).

## 2. The batch root

The **batch root** is the Merkle tree head over the 32-byte record digests, defined per RFC 6962 Certificate Transparency:

- leaf(n) = SHA-256(0x00 || n)
- node(l, r) = SHA-256(0x01 || l || r)
- MTH(D[0:n]) is the leaf for n = 1, sha256(b"") for n = 0, else node(MTH(first ⌈n/2⌉ rounded down to a power of two split per RFC 6962 §2.1), MTH(rest))

The root over *k* records is what a transparency service anchors. Anchoring batch roots — rather than each record — keeps per-decision overhead at one signed statement per batch while preserving per-record inclusion proofs.

## 3. The export and the head

A store exports:

```
{ "zt_store_version": "0.1.0",
  "records": [ ...decision records... ],
  "head": { "record_count": N, "last_record_hash": H, "batch_root": R } }
```

The head lets a verifier reject an export in constant time before walking the chain: recomputing the chain must reproduce the head's count, last hash, and root. Verification protocol for a third party:

1. Check the head against the recomputed chain (constant-time rejection of most tampering).
2. Walk every record: recompute `record_hash`, check the link sequence from `zt-genesis`.
3. For anchored batches (TG-3+): check the transparency receipt against the batch root (anchoring profile document).

A tampered payload, a spliced history, or a forged head each fails at a different step — the tests in `tests/test_store.py` demonstrate all three.

## 4. Compatibility with the AOP case record

The AOP programme's case record is "append-only, hash-chained, tamper-evident" (SEC-8). The binding document (`ztaf-bindings`, Wave 6) will map the two record shapes; the chain semantics here — canonical hash excluding link fields, genesis marker, correction-by-append — are written so an AOP case record can be exported into this envelope without re-hashing its payload.
