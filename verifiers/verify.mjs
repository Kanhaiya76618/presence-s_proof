// verifiers/verify.mjs — Standalone Node.js reference verifier (Node >=18)
// Proves cross-platform determinism of RFC-8785 canonicalization and Keccak-256 outside Python.
// Prerequisites: npm install json-canonicalize js-sha3
// Usage: node verifiers/verify.mjs [path/to/record.json] [contract_address] [rpc_url]

import { readFileSync } from "node:fs";

async function main() {
  const recordPath = process.argv[2] || "out/record.json";
  const contractAddress = process.argv[3] || "0xF474d2Bd987A556781c5daBE0fe743CBf53F29EC";
  const rpcUrl = process.argv[4] || process.env.RPC_URL || "https://ethereum-sepolia-rpc.publicnode.com";


  console.log("=".repeat(70));
  console.log("  CROSS-PLATFORM JCS VERIFIER (Node.js Reference)");
  console.log("=".repeat(70));
  console.log(`[1] Reading Record: ${recordPath}`);

  let raw;
  try {
    raw = JSON.parse(readFileSync(recordPath, "utf8"));
  } catch (err) {
    console.error(`Failed to read record file: ${err.message}`);
    process.exit(1);
  }

  // Strip post-anchoring receipt if present
  const { onchain_anchoring, ...auditRecord } = raw;

  let canonicalize, keccak256;
  try {
    const jcsModule = await import("json-canonicalize");
    canonicalize = jcsModule.canonicalize || jcsModule.default?.canonicalize || jcsModule.default;
    const sha3Module = await import("js-sha3");
    keccak256 = sha3Module.keccak256 || sha3Module.default?.keccak256 || sha3Module.default;

  } catch {
    console.log("Notice: json-canonicalize / js-sha3 npm packages not installed globally.");
    console.log("Install with: npm i json-canonicalize js-sha3");
    console.log("Specification: keccak256(canonicalize(auditRecord))");
    return;
  }

  const canonicalJson = canonicalize(auditRecord);
  const hashHex = "0x" + keccak256(new TextEncoder().encode(canonicalJson));

  console.log(`  RFC-8785 Canonical JSON Bytes: ${new TextEncoder().encode(canonicalJson).length} bytes`);
  console.log(`  Recomputed Keccak-256 Digest: ${hashHex}`);

  console.log(`\n[2] Querying Ethereum Sepolia Contract: ${contractAddress}`);
  // verifyRecord(bytes32) function selector = keccak256("verifyRecord(bytes32)")[0..8] = 0x93306db0
  const selector = keccak256("verifyRecord(bytes32)").slice(0, 8);
  const callData = "0x" + selector + hashHex.slice(2);

  try {
    const response = await fetch(rpcUrl, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: 1,
        method: "eth_call",
        params: [{ to: contractAddress, data: callData }, "latest"]
      })
    });
    const res = await response.json();

    if (res.result && res.result !== "0x") {
      // First 32 bytes decode to boolean (offset 0..66)
      const exists = BigInt(res.result.slice(0, 66)) === 1n;
      if (exists) {
        console.log("\n" + "*".repeat(50));
        console.log("  RESULT: VERIFIED AUTHENTIC ON-CHAIN ✅");
        console.log(`  Record Hash: ${hashHex}`);
        console.log("*".repeat(50));
      } else {
        console.log("\n" + "*".repeat(50));
        console.log("  RESULT: NOT FOUND ON BLOCKCHAIN ❌");
        console.log("  The record hash has not been anchored to this contract.");
        console.log("*".repeat(50));
      }
    } else {
      console.log(`RPC Response: ${JSON.stringify(res)}`);
    }
  } catch (err) {
    console.log(`RPC query skipped: ${err.message}`);
  }
}

main();
