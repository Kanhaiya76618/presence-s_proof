# 🎬 Official 3.5-Minute Demo Screen Recording Script
**Rule**: Unedited, single-take video screen recording. No video cuts.

---

### ⚙️ Pre-Flight Setup (Do this 5 minutes BEFORE hitting Record)
1. **Terminal Font**: Set terminal font size to ≥16pt (so scores & hashes are readable on laptop screens).
2. **Terminal Prompt**: Clean up path wrapping by running:
   ```bash
   export PS1="hackathon $ "
   ```
3. **Browser Setup**: Open [Sepolia Etherscan](https://sepolia.etherscan.io/) in a dedicated tab and zoom in (`Cmd + +` twice).
4. **Model Cache**: Ensure DeepFace model weights are pre-cached:
   ```bash
   python pipeline.py encode data/sample.png
   ```
5. **Node.js dependencies**: Ensure `npm i` is already installed.

---

### ⏱️ Run-of-Show (Exact Commands & Timing)

| Time | Action / Terminal Command | Spoken Narration Script / Visual Cue |
| :--- | :--- | :--- |
| **0:00 - 0:15** | `clear && ls -la` | *"Hello judges. We present Task #3: Face ID + Blockchain Verification Pipeline by Team Pixel.ai. We've built an auditable system with zero-biometric on-chain leakage and cross-platform verification."* |
| **0:15 - 0:30** | `pytest tests/ -q` | *"First, running our offline test suite: 6 unit tests passing in 0.13 seconds verifying RFC-8785 canonicalization stability and tamper detection."* |
| **0:30 - 1:45** | `python pipeline.py run data/sample.png` | *(LIVE run — no cache flags)*<br>*"Now running our live end-to-end pipeline on sample.png. Stage 1 extracts the ArcFace embedding and computes the little-endian float32 SHA-256 hash. Notice Stage 2 hits SerpAPI live—no hardcoded results. It retrieves public appearances across LinkedIn and social media, downloads thumbnails, computes cosine similarity, formats an RFC-8785 canonical record, and anchors the 32-byte Keccak-256 hash to Ethereum Sepolia."* |
| **1:45 - 2:00** | `cat out/record.json \| head -n 25` | *"Inspecting the canonical record: notice what is NOT here—no raw face vector or image bytes. Only cryptographic commitments and audit hashes."* |
| **2:00 - 2:30** | Switch to Etherscan Tab | *Paste Tx hash into Sepolia Etherscan search bar.<br>Highlight **Input Data**: "Only the 32-byte recordHash and CID reference are stored on-chain."<br>Highlight **Event Logs**: "MatchAnchored event emitted with indexed recordHash and block timestamp."* |
| **2:30 - 2:50** | `python pipeline.py verify out/record.json` | *"Verifying the record independently using our zero-gas Python client: Queries `verifyRecord` on-chain. Output: VERIFIED AUTHENTIC ON-CHAIN ✅."* |
| **2:50 - 3:10** | `node verifiers/verify.mjs out/record.json` | *"Crucially, here is our independent Node.js reference verifier. Zero Python code. Independent RFC-8785 JCS implementation and Keccak-256. It produces the exact same 32-byte root and confirms on-chain existence: VERIFIED AUTHENTIC ON-CHAIN ✅."* |
| **3:10 - 3:30** | `python pipeline.py tamper-demo` | *"Finally, adversarial integrity: We flip a single similarity score. The avalanche effect shifts the Keccak digest, breaking the on-chain root: TAMPER DETECTED ❌."* |
| **3:30 - 3:40** | `git log --oneline -5` | *"Clean Git commit history, fully reproducible. Thank you."* |
