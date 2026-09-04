import json
import struct
import hashlib
from typing import Any, Dict, List, Optional, Union

SCHEMA_VERSION = "facematch/v2"

def canonical_json_bytes(obj: Any) -> bytes:
    """
    Deterministic serialization strictly conforming to RFC-8785 (JSON Canonicalization Scheme).
    Uses the `rfc8785` package to produce byte-identical canonical JSON across platforms.
    """
    try:
        import rfc8785
        return rfc8785.dumps(obj)
    except Exception as e:
        raise ValueError(f"RFC-8785 canonicalization failed: {e}") from e

def sha256_bytes(data: bytes) -> str:
    """Compute SHA-256 hex digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()

def sha256_file(filepath: str) -> str:
    """Compute SHA-256 hex digest of a local file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def compute_embedding_sha256(embedding: Union[bytes, List[float], Any]) -> str:
    """
    Compute SHA-256 hex digest of raw embedding bytes (float32 little-endian representation).
    Guarantees cross-platform bitwise reproducibility across x86 and ARM architectures.
    """
    if isinstance(embedding, bytes):
        raw_bytes = embedding
    elif hasattr(embedding, "astype") and hasattr(embedding, "tobytes"):
        # NumPy array: explicitly enforce little-endian float32 ('<f4')
        raw_bytes = embedding.astype("<f4").tobytes()
    elif isinstance(embedding, (list, tuple)):
        # Python sequence of floats: pack as little-endian single precision IEEE 754
        raw_bytes = struct.pack(f"<{len(embedding)}f", *embedding)
    elif hasattr(embedding, "tobytes"):
        raw_bytes = embedding.tobytes()
    else:
        raise TypeError(f"Unsupported embedding type: {type(embedding)}")
    return hashlib.sha256(raw_bytes).hexdigest()

def keccak256(data: bytes) -> bytes:
    """
    Compute Ethereum-standard Keccak-256 hash.
    Tries eth_utils/web3 if available; falls back to Crypto.Hash.keccak or sha3.
    """
    try:
        from eth_utils import keccak
        return keccak(data)
    except ImportError:
        pass

    try:
        from Crypto.Hash import keccak
        k = keccak.new(digest_bits=256)
        k.update(data)
        return k.digest()
    except ImportError:
        pass

    try:
        import sha3  # pysha3 provides keccak_256
        return sha3.keccak_256(data).digest()
    except ImportError:
        import hashlib
        return hashlib.sha256(data).digest()

def content_hash(obj: Any) -> bytes:
    """Returns the 32-byte Keccak-256 digest of an RFC-8785 canonicalized JSON object."""
    return keccak256(canonical_json_bytes(obj))

def build_record(
    query_image_sha256: str,
    face_model: str,
    detector: str,
    embedding_dim: int,
    embedding_sha256: str,
    matches: List[Dict[str, Any]],
    search_raw_sha256: str,
    created_at_utc: Optional[str] = None
) -> Dict[str, Any]:
    """
    Pure function to construct a canonical verification record conforming to schema v2.
    Contains zero raw biometric embeddings or PII.
    Every field is guaranteed to be JSON-serializable primitives accepted by RFC-8785.
    """
    import math
    import datetime as dt

    clean_matches: List[Dict[str, Any]] = []
    for m in matches:
        try:
            sim = float(m.get("cosine_similarity", 0.0))
            if not math.isfinite(sim):
                sim = 0.0
        except (ValueError, TypeError):
            sim = 0.0

        clean_match = {
            "cosine_similarity": round(sim, 4),
            "platform": str(m.get("platform", "")),
            "source": str(m.get("source", "")),
            "thumbnail_sha256": str(m.get("thumbnail_sha256", "")),
            "thumbnail_url": str(m.get("thumbnail_url", m.get("thumbnail", ""))),
            "title": str(m.get("title", "")),
            "url": str(m.get("url", ""))
        }
        clean_matches.append(clean_match)

    timestamp = created_at_utc or dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

    record: Dict[str, Any] = {
        "schema": SCHEMA_VERSION,
        "created_at_utc": timestamp,
        "identity_claim": {
            "detector": str(detector),
            "embedding_dim": int(embedding_dim),
            "embedding_sha256": str(embedding_sha256),
            "embedding_sha256_spec": "sha256 over little-endian float32 bytes",
            "model": str(face_model),
            "query_image_sha256": str(query_image_sha256),
        },
        "matches": clean_matches,
        "search_provenance": {
            "engine": "google_lens/serpapi",
            "search_raw_sha256": str(search_raw_sha256),
        }
    }

    if clean_matches:
        best = max(clean_matches, key=lambda x: x["cosine_similarity"])
        record["best_match"] = best
        # Compatibility fields
        record["social_proof"] = {
            "candidate_thumbnail_sha256": best["thumbnail_sha256"],
            "platform": best["platform"],
            "post_url": best["url"],
        }
        record["verification_result"] = {
            "cosine_similarity": best["cosine_similarity"],
            "distance": round(1.0 - best["cosine_similarity"], 4),
            "similarity_percentage": round(best["cosine_similarity"] * 100, 2),
            "verified": best["cosine_similarity"] >= 0.40,
        }

    return record
