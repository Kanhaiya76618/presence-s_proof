import sys
import copy
import json
from pathlib import Path
import pytest

# Ensure repository root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules.util import (
    canonical_json_bytes,
    content_hash,
    build_record,
    compute_embedding_sha256,
    SCHEMA_VERSION
)
from modules.search import filter_social_matches

def test_no_deepface_imported_at_module_level():
    """Ensure face.py or deepface is never eagerly imported at test import time."""
    assert "deepface" not in sys.modules, "deepface must not be imported at test import time"

def test_unmodified_record_round_trip():
    """(b) The unmodified record round-trips to the exact same hash byte-for-byte."""
    record_path = Path("out/record.json")
    assert record_path.exists(), "out/record.json must exist"
    
    record = json.loads(record_path.read_text(encoding="utf-8"))
    
    # Strip any post-anchoring block receipt
    clean_record = {k: v for k, v in record.items() if k != "onchain_anchoring"}
    
    hash1 = content_hash(clean_record)
    
    # Round-trip through json serialization and back
    serialized = json.dumps(clean_record)
    deserialized = json.loads(serialized)
    hash2 = content_hash(deserialized)
    
    # Round-trip through canonical bytes
    canonical_b = canonical_json_bytes(clean_record)
    from eth_utils import keccak
    hash3 = keccak(canonical_b)
    
    assert hash1 == hash2, "Round-trip JSON serialization altered content_hash"
    assert hash1 == hash3, "Canonical bytes Keccak did not match content_hash"
    assert len(hash1) == 32, "content_hash must be a 32-byte digest"

def test_flip_one_character_changes_hash():
    """(a) Flipping exactly one character in a string field of out/record.json changes content_hash."""
    record_path = Path("out/record.json")
    assert record_path.exists(), "out/record.json must exist"
    
    record = json.loads(record_path.read_text(encoding="utf-8"))
    clean_record = {k: v for k, v in record.items() if k != "onchain_anchoring"}
    orig_hash = content_hash(clean_record)
    
    # Flip exactly one character in a string field: query_image_sha256
    tampered = copy.deepcopy(clean_record)
    orig_sha = tampered["identity_claim"]["query_image_sha256"]
    
    # Flip the first character
    flipped_char = "a" if orig_sha[0] != "a" else "b"
    tampered["identity_claim"]["query_image_sha256"] = flipped_char + orig_sha[1:]
    
    # Ensure only 1 character differed
    diff_count = sum(1 for c1, c2 in zip(orig_sha, tampered["identity_claim"]["query_image_sha256"]) if c1 != c2)
    assert diff_count == 1, "Must flip exactly one character"
    
    tampered_hash = content_hash(tampered)
    assert orig_hash != tampered_hash, "Flipping one character in string field MUST alter content_hash"

def test_social_domain_filter_with_fixture():
    """(c) Unit tests for social-domain result filter using synthetic lens_response.json fixture."""
    fixture_path = Path("tests/fixtures/lens_response.json")
    assert fixture_path.exists(), "Fixture tests/fixtures/lens_response.json must exist"
    
    lens_data = json.loads(fixture_path.read_text(encoding="utf-8"))
    matches = filter_social_matches(lens_data, limit=10)
    
    # Fixture contains 5 items:
    # 1. linkedin.com -> match
    # 2. x.com -> match
    # 3. random-unrelated-blog.example.com -> rejected
    # 4. instagram.com -> match
    # 5. duplicate linkedin.com -> rejected as duplicate
    
    assert len(matches) == 3, f"Expected 3 valid unique social matches, got {len(matches)}"
    
    platforms = [m["platform"] for m in matches]
    assert platforms == ["linkedin", "x", "instagram"]
    
    urls = [m["url"] for m in matches]
    assert "https://random-unrelated-blog.example.com/article-123" not in urls, "Non-social blog must be filtered out"
    assert len(set(urls)) == 3, "All filtered URLs must be unique"

def test_build_record_strips_raw_biometrics():
    """Verify build_record never persists raw embeddings and enforces schema v2."""
    stub_embedding = [0.123456, -0.654321, 0.987654, 0.0]
    emb_sha = compute_embedding_sha256(stub_embedding)
    
    record = build_record(
        query_image_sha256="deadbeef" * 8,
        face_model="ArcFace",
        detector="retinaface",
        embedding_dim=len(stub_embedding),
        embedding_sha256=emb_sha,
        matches=[{
            "cosine_similarity": 0.94218,
            "platform": "linkedin",
            "source": "LinkedIn",
            "thumbnail_sha256": "feedface" * 8,
            "thumbnail_url": "https://example.com/thumb.jpg",
            "title": "Mock Post",
            "url": "https://linkedin.com/posts/mock-post"
        }],
        search_raw_sha256="cafebabe" * 8
    )
    
    assert record["schema"] == SCHEMA_VERSION
    assert record["schema"] == "facematch/v2"
    
    # Check identity_claim fields
    claim = record["identity_claim"]
    assert "embedding" not in claim, "Raw embedding vector must NOT be present in identity_claim"
    assert "embedding_sha256" in claim
    assert claim["embedding_dim"] == 4
    assert claim["embedding_sha256"] == emb_sha
    
    # Check match evidence fields
    match = record["matches"][0]
    assert match["cosine_similarity"] == 0.9422  # rounded to 4 decimals
    assert "thumbnail_sha256" in match
    assert "thumbnail_url" in match
    assert "platform" in match
    assert "url" in match
    assert "title" in match
    assert "source" in match
    
    # Canonical byte serialization check
    b = canonical_json_bytes(record)
    assert isinstance(b, bytes)
    h = content_hash(record)
    assert isinstance(h, bytes) and len(h) == 32

def test_embedding_sha256_stability():
    """Assert embedding_sha256 is bitwise identical across multiple runs and conversions."""
    import numpy as np
    raw_floats = [0.12345, -0.67891, 0.43210, 0.99999, -0.00001]
    
    # Run 10 times with list
    digests_list = [compute_embedding_sha256(raw_floats) for _ in range(10)]
    assert len(set(digests_list)) == 1, "List float32 embedding SHA-256 must be bitwise deterministic"
    
    # Compare with numpy float32 little-endian
    np_arr = np.array(raw_floats, dtype=np.float32)
    digest_np = compute_embedding_sha256(np_arr)
    assert digests_list[0] == digest_np, "Numpy and list float32 representations must produce identical SHA-256"

