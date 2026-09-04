import os
import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

# Default public Sepolia RPC fallback
DEFAULT_SEPOLIA_RPC = "https://rpc.sepolia.org"
SOLC_VERSION = "0.8.24"

# Pre-compiled fallback ABI for FaceMatchRegistry to guarantee zero-failure execution
CONTRACT_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "recordHash", "type": "bytes32"},
            {"indexed": True, "internalType": "address", "name": "submitter", "type": "address"},
            {"indexed": False, "internalType": "uint64", "name": "anchoredAt", "type": "uint64"},
            {"indexed": False, "internalType": "string", "name": "cid", "type": "string"}
        ],
        "name": "MatchAnchored",
        "type": "event"
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "recordHash", "type": "bytes32"},
            {"internalType": "string", "name": "cid", "type": "string"}
        ],
        "name": "anchorRecord",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
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
    },
    {
        "inputs": [],
        "name": "totalRecords",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "name": "allHashes",
        "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# Minimal ABI specifically for independent view verification with zero write/deploy overhead
MINIMAL_ABI = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "recordHash", "type": "bytes32"}
        ],
        "name": "verifyRecord",
        "outputs": [
            {"internalType": "bool", "name": "exists", "type": "bool"},
            {"internalType": "address", "name": "submitter", "type": "address"},
            {"internalType": "uint64", "name": "anchoredAt", "type": "uint64"},
            {"internalType": "string", "name": "cid", "type": "string"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

def get_rpc_url() -> str:
    from dotenv import load_dotenv
    load_dotenv()
    return os.getenv("RPC_URL") or os.getenv("SEPOLIA_RPC") or DEFAULT_SEPOLIA_RPC

def w3_connect(rpc_url: Optional[str] = None):
    """Establish connection to Ethereum node via web3.py."""
    from web3 import Web3
    url = rpc_url or get_rpc_url()
    w3 = Web3(Web3.HTTPProvider(url))
    if not w3.is_connected():
        raise ConnectionError(f"Failed to connect to Ethereum RPC at {url}")
    return w3

def compile_contract(contract_path: str = "contracts/FaceMatchRegistry.sol") -> Tuple[list, str]:
    """Compile Solidity contract using py-solc-x."""
    src = Path(contract_path).read_text(encoding="utf-8")
    try:
        from solcx import compile_source, install_solc, set_solc_version
        try:
            set_solc_version(SOLC_VERSION)
        except Exception:
            install_solc(SOLC_VERSION)
            set_solc_version(SOLC_VERSION)

        compiled = compile_source(src, output_values=["abi", "bin"], solc_version=SOLC_VERSION)
        for key, iface in compiled.items():
            if key.endswith(":FaceMatchRegistry"):
                return iface["abi"], iface["bin"]
    except Exception as e:
        # Fallback: check if precompiled JSON exists
        precompiled = Path("contracts/FaceMatchRegistry.json")
        if precompiled.exists():
            data = json.loads(precompiled.read_text())
            return data["abi"], data["bin"]
        raise RuntimeError(f"Contract compilation failed: {e}")

    raise RuntimeError("FaceMatchRegistry contract not found in compilation output.")

def deploy_contract(w3, private_key: Optional[str] = None) -> Dict[str, Any]:
    """Deploy FaceMatchRegistry to target network."""
    from web3 import Web3
    from dotenv import load_dotenv
    load_dotenv()

    pk = private_key or os.getenv("PRIVATE_KEY")
    if not pk:
        raise ValueError("PRIVATE_KEY not provided in environment or argument.")

    abi, bytecode = compile_contract()
    account = w3.eth.account.from_key(pk)
    balance = w3.eth.get_balance(account.address)
    
    if balance == 0:
        raise ValueError(
            f"Account {account.address} has 0 ETH on chain {w3.eth.chain_id}. "
            "Please fund it with testnet ETH."
        )

    contract_factory = w3.eth.contract(abi=abi, bytecode=bytecode)
    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = max(w3.eth.gas_price, w3.to_wei(2, "gwei"))

    tx = contract_factory.constructor().build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 1_200_000,
        "gasPrice": gas_price,
        "chainId": w3.eth.chain_id
    })

    signed_tx = account.sign_transaction(tx)
    raw_tx = getattr(signed_tx, "raw_transaction", getattr(signed_tx, "rawTransaction", None))
    tx_hash = w3.eth.send_raw_transaction(raw_tx)
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
    contract_address = receipt.contractAddress

    deployment_data = {
        "address": contract_address,
        "deployer": account.address,
        "tx_hash": tx_hash.hex(),
        "chain_id": w3.eth.chain_id,
        "block_number": receipt.blockNumber,
        "abi": abi
    }
    return deployment_data

def anchor_hash(
    w3,
    contract_address: str,
    abi: list,
    record_hash_bytes: bytes,
    private_key: Optional[str] = None,
    cid: str = ""
) -> str:
    """Submit transaction to anchor record hash on-chain."""
    from web3 import Web3
    from dotenv import load_dotenv
    load_dotenv()

    pk = private_key or os.getenv("PRIVATE_KEY")
    if not pk:
        raise ValueError("PRIVATE_KEY not configured.")

    account = w3.eth.account.from_key(pk)
    contract = w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=abi)
    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = max(w3.eth.gas_price, w3.to_wei(2, "gwei"))

    fn = contract.functions.anchorRecord(record_hash_bytes, cid)
    
    # Estimate gas with buffer
    try:
        est_gas = fn.estimate_gas({"from": account.address})
        gas_limit = int(est_gas * 1.3)
    except Exception:
        gas_limit = 250_000

    tx = fn.build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": gas_limit,
        "gasPrice": gas_price,
        "chainId": w3.eth.chain_id
    })

    signed_tx = account.sign_transaction(tx)
    raw_tx = getattr(signed_tx, "raw_transaction", getattr(signed_tx, "rawTransaction", None))
    tx_hash = w3.eth.send_raw_transaction(raw_tx)
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
    return tx_hash.hex()

def verify_hash(
    w3,
    contract_address: str,
    record_hash_bytes: bytes,
    abi: Optional[list] = None
) -> Dict[str, Any]:
    """Query verifyRecord view function (zero gas). Defaults to MINIMAL_ABI."""
    from web3 import Web3
    use_abi = abi if abi is not None else MINIMAL_ABI
    contract = w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=use_abi)
    exists, submitter, ts, cid = contract.functions.verifyRecord(record_hash_bytes).call()
    return {
        "exists": exists,
        "submitter": submitter,
        "anchored_at": ts,
        "cid": cid
    }
