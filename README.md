# Face ID + Blockchain Verification Pipeline

A tamper-evident, decentralized verification pipeline that detects and encodes a face from an input image, identifies matching public social media posts via genuine Google Lens reverse-image search, computes cross-image facial similarity, and anchors a cryptographic root proof onto Ethereum Sepolia.

---

## 🏛️ Architecture & Verification Flow

```
[ input.jpg ] (Selfie / Portrait)
     │
     ├──► [1] Face Detection & Feature Hashing
     │          ├── Extracts normalized 128-d/512-d feature vector (ArcFace / CNN)
     │          └── Computes embedding_sha256 = SHA-256(raw_embedding_bytes)
     │          └── Raw vector is NEVER persisted in the record
     │
     ├──► [2] Live Reverse Image Search (Google Lens via SerpAPI)
     │          ├── Discovers public appearances across LinkedIn, X/Twitter, Instagram
     │          └── Archives raw API response to `out/search_raw.json` (search provenance)
     │
     ├──► [3] Candidate Social Post & Facial Cross-Verification
     │          ├── Downloads candidate post media / thumbnail
     │          ├── Performs cosine similarity comparison across detected candidate faces
     │          └── Computes candidate thumbnail SHA-256 and cosine similarity (rounded to 4 decimals)
     │
     ├──► [4] Canonical Tamper-Evident Record Construction (Schema v2)
     │          ├── Computes SHA-256 of input photo & candidate thumbnails (raw bytes)
     │          ├── Computes SHA-256 of raw search response
     │          ├── Serializes record strictly conforming to RFC-8785 (JSON Canonicalization Scheme)
     │          └── Computes 32-byte Keccak-256 cryptographic digest
     │
     ├──► [5] On-Chain Anchoring (Ethereum Sepolia)
     │          ├── Calls `FaceMatchRegistry.anchorRecord(recordHash, cid)`
     │          └── Emits `MatchAnchored` event on Etherscan
     │
     └──► [6] Zero-Gas Independent Verification (`verify` CLI)
                ├── Independent auditors recompute the root hash from `record.json`
                └── Calls public view function `verifyRecord(recordHash)` to prove authenticity
```

---

## 🔒 Cryptographic Tamper-Evidence & RFC-8785 Specification

To guarantee that no record can be fabricated or modified post-anchoring, this pipeline enforces strict cryptographic commitments:

### 1. True RFC-8785 Canonicalization (JSON Canonicalization Scheme - JCS)
RFC 8785 defines a deterministic JSON representation regardless of programming language or runtime environment:
- Keys are sorted lexicographically by UTF-16 code units.
- Numbers follow ECMAScript canonical representation (no NaN, Infinity, or non-standard notation).
- Delimiters contain zero insignificant whitespace (no space after commas or colons).
- Strings are encoded in strict UTF-8 without unnecessary escapes.

Implementation in Python:
```python
import rfc8785
canonical_bytes = rfc8785.dumps(record)
```

### 2. Ethereum Keccak-256 Root Digest
The canonical bytes are hashed using Ethereum-standard Keccak-256:
$$\text{record\_hash} = \text{Keccak-256}(\text{canonical\_bytes})$$

### 3. Zero Biometric Exposure
Raw image files, floating-point embedding vectors, and biometric PII **never** touch the record or the blockchain. The identity claim only holds the SHA-256 digest of the embedding bytes (`embedding_sha256`), the model architecture, and the embedding dimension.

---

## 🚀 Standalone Independent Verifier Snippet

Any third party can audit a `record.json` file independently using only public RPC endpoints without needing the private key, our repository, or custom tools:

```python
import json
import rfc8785
from eth_utils import keccak
from web3 import Web3

# 1. Load record and strip any post-anchoring block metadata
with open("out/record.json", "r", encoding="utf-8") as f:
    full_record = json.load(f)

audit_record = {k: v for k, v in full_record.items() if k != "onchain_anchoring"}

# 2. Recompute RFC-8785 canonical bytes and Keccak-256 digest
canonical_bytes = rfc8785.dumps(audit_record)
recomputed_hash = keccak(canonical_bytes)
print(f"Recomputed Hash: 0x{recomputed_hash.hex()}")

# 3. Query the contract via public Sepolia RPC (zero gas, read-only view)
MINIMAL_ABI = [{
    "inputs": [{"internalType": "bytes32", "name": "recordHash", "type": "bytes32"}],
    "name": "verifyRecord",
    "outputs": [
        {"internalType": "bool", "name": "exists", "type": "bool"},
        {"internalType": "address", "name": "submitter", "type": "address"},
        {"internalType": "uint64", "name": "anchoredAt", "type": "uint64"},
        {"internalType": "string", "name": "cid", "type": "string"}
    ],
    "stateMutability": "view",
    "type": "function"
}]

w3 = Web3(Web3.HTTPProvider("https://rpc.sepolia.org"))
CONTRACT_ADDRESS = "0xF474d2Bd987A556781c5daBE0fe743CBf53F29EC"

contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=MINIMAL_ABI)
exists, submitter, timestamp, cid = contract.functions.verifyRecord(recomputed_hash).call()

if exists:
    print(f"VERIFIED ✅: Anchored by {submitter} at block timestamp {timestamp}")
else:
    print("NOT FOUND ❌: Hash does not exist on-chain or record was modified.")
```

---

## 💻 CLI Quickstart & Usage

### 1. Installation
```bash
git clone https://github.com/Kanhaiya76618/presence-s_proof.git
cd presence-s_proof

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Environment Configuration
Copy the template and fill in your keys:
```bash
cp .env.example .env
```
Edit `.env`:
```ini
SERPAPI_KEY=your_serpapi_key_here
RPC_URL=https://eth-sepolia.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
PRIVATE_KEY=0x_your_sepolia_burner_private_key
ETHERSCAN_API_KEY=your_etherscan_key_here
```

### 3. Deploy Smart Contract
Deploys `FaceMatchRegistry.sol` to Ethereum Sepolia and writes the contract address to `out/deployment.json`:
```bash
python pipeline.py deploy
```

### 4. Run Verification Pipeline
```bash
# Live run
python pipeline.py run data/sample.png

# Offline / dev re-runs using cached search audit trail
python pipeline.py run data/sample.png --use-cache
```

### 5. Independent Verification
```bash
python pipeline.py verify out/record.json
```

---

## ⚠️ Known Limitations

1. **Search Coverage Dynamics**: Google Lens reverse-image search coverage is point-in-time, regional, and depends on public web crawlers. Private profiles or freshly posted images may not be indexed immediately.
2. **Existence Proof vs. Identity Truth**: The on-chain hash cryptographically proves that the record existed and was unmodified since block timestamp $T$. It does **not** prove absolute ground-truth identity; this is mitigated by our ArcFace cosine-similarity thresholding, but not eliminated.
3. **API Dependency & Rate Limits**: Live reverse search relies on SerpAPI/Google Lens quotas. Dev runs should leverage `--use-cache` to avoid quota exhaustion.
4. **Single-Deployer Anchoring**: Single-account transaction submission guarantees tamper-evidence and immutable timestamping, but does not constitute a decentralized multi-party oracle attestation.
5. **Block Timestamp Granularity**: Ethereum block timestamps are determined by validators and are accurate to within approximately ~12 seconds.
6. **Zero Biometrics On-Chain**: The smart contract stores only a 32-byte cryptographic hash. No images, facial embeddings, or PII ever leave the local machine or enter blockchain storage.

---

## 🛡️ Consent & Ethics

- **Consensual Demo**: The demonstration photo depicts the project team members (Team Pixel.ai) who provided explicit consent for this demonstration.
- **Privacy & Compliance**: Users must only process and verify photos for which they possess appropriate legal rights and consent. General-purpose face search of non-consenting individuals touches biometric privacy frameworks including the Illinois Biometric Information Privacy Act (BIPA) and the EU General Data Protection Regulation (GDPR). Raw biometric vectors are hashed and discarded locally to uphold data minimization principles.

---

## 👥 Authors
- **Team Pixel.ai** (IIIT Dharwad)
- Primary Developer: Kanhaiya Mehta
