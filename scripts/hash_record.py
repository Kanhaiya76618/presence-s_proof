#!/usr/bin/env python3
"""
Standalone RFC-8785 Keccak-256 Hasher.
Requires zero codebase dependencies (only `rfc8785` and standard library / eth_utils).
Usage: python scripts/hash_record.py [path/to/record.json]
"""
import sys
import json
import rfc8785

def hash_record(record_path: str = "out/record.json") -> str:
    with open(record_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    clean_record = {k: v for k, v in data.items() if k != "onchain_anchoring"}
    canonical_bytes = rfc8785.dumps(clean_record)
    try:
        from eth_utils import keccak
        digest = keccak(canonical_bytes)
    except ImportError:
        from Crypto.Hash import keccak
        k = keccak.new(digest_bits=256)
        k.update(canonical_bytes)
        digest = k.digest()
    return "0x" + digest.hex()

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "out/record.json"
    print(hash_record(target))
