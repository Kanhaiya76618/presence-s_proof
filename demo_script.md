# Hackathon Demo Video Script: Face ID + Blockchain Verification

**Rules Requirement**: *An unedited screen recording of the full pipeline running end to end.*

Follow these exact steps for your video recording (Total Time: ~3–4 minutes). Do not edit or cut the video.

---

### Pre-Recording Checklist
- [ ] Terminal font size set to **18pt+** for crisp readability.
- [ ] Browser window open with two tabs:
  1. [Sepolia Etherscan](https://sepolia.etherscan.io)
  2. The LinkedIn post: `https://www.linkedin.com/posts/aakash-pathrikar-483aa4324_hackathon-halaerothon-teamwork-activity-7416675369304461313-DK1k`
- [ ] `.env` is populated with your `SERPAPI_KEY`, `RPC_URL`, and `PRIVATE_KEY`.
- [ ] Start your screen recording software (OBS Studio or Mac QuickTime Screen Recording).

---

### Step-by-Step Recording Sequence

#### 1. Introduction & Overview (30 seconds)
- **What to show**: Terminal showing the repository directory (`presence-s_proof`) and `data/sample.png`.
- **What to say**:
  > *"Hello judges! This is Team Pixel.ai presenting Task #3: Face ID + Blockchain Verification Pipeline. In this unedited demo, we will detect and encode a face from an input photo, find the real matching public LinkedIn post through live reverse-image search, verify facial similarity, construct a canonical tamper-evident record, and anchor the cryptographic root hash directly onto Ethereum Sepolia."*

#### 2. Local Face Encoding Sanity Test (20 seconds)
- **What to run**:
  ```bash
  python pipeline.py encode data/sample.png
  ```
- **What to say**:
  > *"First, we test our local face detector and feature embedder. The pipeline extracts a normalized 128-dimensional embedding and pinpoints the facial bounding box."*

#### 3. Smart Contract Deployment (30 seconds)
- **What to run**:
  ```bash
  python pipeline.py deploy
  ```
- **What to say**:
  > *"Next, we deploy our `FaceMatchRegistry` Solidity contract to the Ethereum Sepolia testnet. The transaction confirms, and the contract address is recorded."*
- **What to show**: Switch to your browser, open the deployment transaction on Sepolia Etherscan, showing the newly created contract.

#### 4. Full End-to-End Pipeline Execution (60 seconds)
- **What to run**:
  ```bash
  python pipeline.py run data/sample.png
  ```
- **What to say**:
  > *"Now we trigger the end-to-end pipeline:
  > Stage 1 encodes the face and computes the raw image SHA-256.
  > Stage 2 performs live reverse-image search via Google Lens.
  > Stage 3 filters candidate social posts and finds our real HAL Aerothon team award post on LinkedIn. It downloads the candidate thumbnail and cross-verifies facial similarity.
  > Stage 4 generates our canonical RFC-8785 record and computes the 32-byte Keccak-256 root hash.
  > Stage 5 broadcasts the anchoring transaction to Ethereum Sepolia."*
- **What to show**: Switch to your browser, click the printed Etherscan transaction link, and show the confirmed transaction and the `MatchAnchored` event log containing the exact `recordHash`.

#### 5. Independent Verification & Anti-Tamper Demonstration (45 seconds)
- **What to run**:
  ```bash
  python pipeline.py verify out/record.json
  ```
- **What to say**:
  > *"Finally, any third party can independently audit the record. The verify command recomputes the canonical Keccak-256 digest and queries the Sepolia contract's view function with zero gas. It confirms that the record is authentic and exists on-chain at this exact block timestamp."*

- **Tamper Demonstration (Bonus Points)**:
  Open `out/record.json`, modify one digit of the similarity score (e.g., change `89.5` to `99.5`), and run:
  ```bash
  python pipeline.py verify out/record.json
  ```
  Show the terminal immediately failing:
  > *"Notice that tampering with even a single byte off-chain causes an immediate cryptographic mismatch."*

#### 6. Conclusion (15 seconds)
- **What to say**:
  > *"The pipeline completed end-to-end with genuine search, real candidate verification, and tamper-evident blockchain anchoring. Thank you!"*
- Stop the recording.
