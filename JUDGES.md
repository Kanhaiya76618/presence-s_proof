# 🏆 Hackathon Judge Evaluation Guide (Task #3)

**Project**: Face ID + Blockchain Verification Pipeline  
**Team**: Pixel.ai (IIIT Dharwad)  
**Contract on Sepolia**: [`0xF474d2Bd987A556781c5daBE0fe743CBf53F29EC`](https://sepolia.etherscan.io/address/0xF474d2Bd987A556781c5daBE0fe743CBf53F29EC)

---

## ⚡ 30-Second Pitch
Proof-of-Presence detects a face from an authentic photo, discovers matching public social media posts via live Google Lens reverse-image search, verifies cross-image facial similarity, serializes the evidence package into strict RFC-8785 canonical JSON (Schema v2), and anchors an immutable Keccak-256 root hash to Ethereum Sepolia.

---

## 📦 What We Built
1. **Zero-Biometric Privacy (Schema v2)**: Raw face embeddings are **never** published. Only `embedding_sha256` (SHA-256 over little-endian float32 bytes) is committed, adhering to BIPA / GDPR data minimization.
2. **True RFC-8785 (JCS) Canonicalization**: Implemented with the `rfc8785` package to ensure byte-identical cross-platform determinism across Python, JavaScript, and Go.
3. **Evidence-Enriched Records**: Persists candidate thumbnail SHA-256, source links, search audit trail hashes, and cosine similarity rounded to 4 decimals.
4. **Standalone Zero-Gas View Verification**: Auditable via `python pipeline.py verify out/record.json` or our Node.js reference verifier without private keys or gas.
5. **Interactive Adversarial Tamper Demonstration**: `python pipeline.py tamper-demo` proves on-the-fly that flipping a single bit breaks the cryptographic root.
6. **100% Offline Test Suite**: 6 unit tests (`tests/test_tamper.py`) running in ~0.13s with synthetic fixtures.

---

## 🚫 What We Did NOT Build (Deliberate Scope Discipline)
- **We did NOT build a web dashboard**: Per hackathon rules, CLI pipelines are evaluated strictly on architectural rigor and cryptographic integrity.
- **We did NOT hardcode results**: The reverse search executes against real search indices, and offline rehearsals use audited raw snapshots via `--use-cache`.
- **We did NOT store PII or vectors on-chain**: Only a 32-byte Keccak-256 hash is committed to Ethereum.

---

## 🔎 Trust, But Verify: Quick Commands for Judges

Clone and verify the authentic record in 30 seconds:

```bash
git clone https://github.com/Kanhaiya76618/presence-s_proof.git
cd presence-s_proof

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1. Run full offline test suite (runs in ~0.13s)
pytest -q

# 2. Run adversarial tamper demonstration
python pipeline.py tamper-demo

# 3. Verify standalone hash computation
python scripts/hash_record.py out/record.json
```

---

## 🛡️ Threat Model & Security Guarantees

| Threat / Attack Vector | Detected? | Mitigating Mechanism |
| :--- | :---: | :--- |
| **Post-anchoring record modification** | ✅ Yes | RFC-8785 canonicalization + Keccak-256 mismatch |
| **Biometric template reverse-engineering** | 🛡️ Immune | Raw vector is discarded; only SHA-256 commitment stored |
| **Fabricated search results** | ✅ Yes | Raw search response provenance hash (`search_raw_sha256`) |
| **Candidate thumbnail alteration** | ✅ Yes | Direct byte SHA-256 hash (`thumbnail_sha256`) |
| **Contract re-entrancy / state manipulation** | 🛡️ Immune | View-only verification function; checks-effects-interactions |
| **Biometric dictionary / linkage attack** | ⚠️ Documented | Hash commitment proves possession; future iteration would integrate zk-SNARKs |
| **Content truth vs. existence** | ⚠️ Documented | Blockchain proves existence at block $T$, not real-world identity truth; cross-verification mitigated via ArcFace threshold |
