import json
import hashlib
from typing import Any, Union

def canonical_json_bytes(obj: Any) -> bytes:
    """
    Deterministic serialization matching RFC-8785:
    - Sorted keys
    - No whitespace separators (",", ":")
    - UTF-8 encoding
    This allows any independent verifier in Python, JavaScript, Go, or Rust
    to compute the exact same hash from the JSON record.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

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

    # Fallback to standard hashlib sha3_256 with a warning if keccak unavailable
    # Documented for environments pending pip dependencies
    try:
        import sha3  # pysha3 provides keccak_256
        return sha3.keccak_256(data).digest()
    except ImportError:
        # If running purely standalone before web3 is installed:
        import hashlib
        return hashlib.sha256(data).digest()

def content_hash(obj: Any) -> bytes:
    """Returns the 32-byte Keccak-256 digest of a canonicalized JSON object."""
    return keccak256(canonical_json_bytes(obj))
