"""ztaf-evidence: the Zero-TAF evidence-plane reference.

Reference only. The normative record semantics live in ztaf-spec (decision
record document) and the anchoring profile in docs/ of this repository.
"""

from .bundle import assemble, verify
from .store import EvidenceStore, StoreError, merkle_root, record_content_hash

__version__ = "0.1.0"
