# Face ID + Blockchain Verification Pipeline

A tamper-evident, decentralized verification pipeline that detects and encodes a face from an input image, identifies matching public social media posts via genuine Google Lens reverse-image search, computes cross-image facial similarity, and anchors a cryptographic root proof onto Ethereum Sepolia.

---

## 🏛️ Architecture & Verification Flow

```
[ input.jpg ] (Selfie / Portrait)
     │
     ├──► [1] Face Detection & Embedding
     │          └── Extracts normalized 128-d/512-d feature vector (ArcFace / CNN)
     │
     ├──► [2] Live Reverse Image Search (Google Lens via SerpAPI)
     │          └── Discovers public appearances across LinkedIn, X/Twitter, Instagram
     │          └── Archives raw API response to `out/search_raw.json` (search provenance)
     │
     ├──► [3] Candidate Social Post & Facial Cross-Verification
     │          └── Downloads candidate post media / thumbnail
     │          └── Performs cosine similarity comparison across detected candidate faces
     │          └── Establishes confidence score and verification status
     │
     ├──► [4] Canonical Tamper-Evident Record Construction
     │          ├── Computes SHA-256 of input photo & candidate media (raw bytes)
     │          ├── Computes SHA-256 of raw search response
     │          ├── Serializes record in strict RFC-8785 canonical JSON (sorted keys, UTF-8)
     │          └── Computes 32-byte Keccak-256 cryptographic digest
     │
     ├──► [5] On-Chain Anchoring (Ethereum Sepolia)
     │          └── Calls `FaceMatchRegistry.anchorRecord(recordHash, cid)`
     │          └── Emits `MatchAnchored` event on Etherscan
     │
     └──► [6] Zero-Gas Independent Verification (`verify` CLI)
                └── Independent auditors recompute the root hash from `record.json`
                └── Calls public view function `verifyRecord(recordHash)` to prove authenticity
```

---

## 🔒 Cryptographic Tamper-Evidence Design

To guarantee that no record can be fabricated or modified post-anchoring, this pipeline enforces multi-layer cryptographic commitments:

1. **Deterministic Canonicalization (RFC-8785)**:
   Any JSON record is sorted alphabetically by key and encoded with strict no-whitespace delimiters:
   ```python
   canonical_bytes = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
   ```
2. **Ethereum Keccak-256 Root Digest**:
   The canonical bytes are hashed using Ethereum-standard Keccak-256:
   $$\text{record\_hash} = \text{Keccak-256}(\text{canonical\_bytes})$$
3. **Zero Biometric Exposure**:
   Raw image files, vector embeddings, and PII **never** touch the blockchain. Only cryptographic hashes are recorded.

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10+
- A free **SerpAPI Key** (from [serpapi.com](https://serpapi.com))
- A free **Ethereum Sepolia RPC URL** (from [alchemy.com](https://alchemy.com) or Infura)
- A testnet burner private key funded with free Sepolia ETH (from [Google Cloud Web3 Faucet](https://cloud.google.com/application/web3/faucet) or [Alchemy Faucet](https://sepoliafaucet.com))

### 2. Installation
```bash
git clone https://github.com/Kanhaiya76618/presence-s_proof.git
cd presence-s_proof

# Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy the template and fill in your keys:
```bash
cp .env.example .env
```
Edit `.env`:
```ini
SERPAPI_KEY=your_serpapi_key_here
RPC_URL=https://eth-sepolia.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
PRIVATE_KEY=0x_your_sepolia_burner_private_key
```

---

## 💻 CLI Usage

### A. Deploy Contract to Sepolia
Deploys `FaceMatchRegistry.sol` to Ethereum Sepolia and writes the contract address to `out/deployment.json`:
```bash
python pipeline.py deploy
```

### B. Run Full Verification Pipeline
Runs end-to-end detection, live reverse search, face matching, canonical hashing, and on-chain anchoring:
```bash
python pipeline.py run data/sample.png
```

*Flags available:*
- `--cache`: Uses local cached search audit trail (`out/search_raw.json`) to conserve SerpAPI credits during practice.
- `--limit <N>`: Sets the maximum candidate social matches evaluated (default: 5).
- `--skip-chain`: Executes off-chain stages (useful for dry runs).

### C. Independent Audit & Verification
Anyone with `out/record.json` and a public Ethereum node can independently verify the record without needing original photos:
```bash
python pipeline.py verify out/record.json
```
**Expected Output:**
```text
======================================================================
  INDEPENDENT RECORD AUDIT & ON-CHAIN VERIFICATION
======================================================================

[1] Off-Chain Cryptographic Integrity:
  Recomputed Canonical Keccak-256: 0x96dcb0fe94d7cb923b7d4222760a1b8fe6a84a46fc752d22477b2b666d53b5ed
  ✓ Local record matches stated cryptographic root! (NO TAMPERING)

[2] On-Chain Sepolia Attestation Check:
  Querying Contract: 0x5FbDB2315678afecb367f032d93F642f64180aa3

**************************************************
  RESULT: VERIFIED AUTHENTIC ON-CHAIN ✅
  Submitter Address: 0x90F79bf6EB2c4f870365E785982E1f101E93b906
  Anchored Timestamp: 2026-09-03T03:02:44+00:00
  Post URL Claim:     https://www.linkedin.com/posts/aakash-pathrikar-483aa4324_hackathon-halaerothon-teamwork-activity-7416675369304461313-DK1k
  Similarity Score:   89.5%
**************************************************
```

---

## ⛓️ Why Ethereum Sepolia?

1. **Decentralization & Public Accessibility**: Sepolia is Ethereum’s primary testnet. It provides identical EVM semantics to Ethereum Mainnet without incurring financial cost.
2. **Zero-Trust Independent Audit**: Anyone can inspect transactions, timestamp proofs, and event logs using public block explorers like [sepolia.etherscan.io](https://sepolia.etherscan.io).
3. **No Proprietary Vendor Lock-in**: The verification function is a pure view method (`verifyRecord`), requiring zero gas and zero credentials to query.

---

## ⚠️ Known Limitations & Disclosures

1. **Search Engine Indexing Latency**: Reverse-image engines (Google Lens) can only locate public posts crawled by web spiders. Private accounts or freshly published posts may take hours or days to appear in public indexes.
2. **Face Matching Variances**: Lighting conditions, extreme angles, occlusions (glasses, masks), and image resolution can introduce variance in cosine similarity metrics.
3. **Tamper-Evidence vs. Real-World Truth**: Anchoring on a blockchain cryptographically proves that a specific verification result existed at block timestamp $T$ and was signed by submitter $S$; it does not replace identity authorities or legal certifications.
4. **Rate Limits**: Free SerpAPI plans allow 100 queries/month. Use `--cache` for iterative testing.

---

## 👥 Authors
- **Team Pixel.ai** (IIIT Dharwad)
- Primary Developer: Kanhaiya Mehta
