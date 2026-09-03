// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title FaceMatchRegistry
 * @notice Tamper-evident on-chain registry for face-verification and social-match records.
 * @dev Stores cryptographic hashes of verification packages. Never stores raw images, embeddings, or PII.
 */
contract FaceMatchRegistry {
    struct Record {
        address submitter;
        uint64 anchoredAt;
        string cid; // Optional IPFS CID or metadata reference URI
    }

    // Mapping: recordHash (Keccak-256) => Record
    mapping(bytes32 => Record) private _records;
    
    // Ordered list of all anchored hashes
    bytes32[] public allHashes;

    event MatchAnchored(
        bytes32 indexed recordHash,
        address indexed submitter,
        uint64 anchoredAt,
        string cid
    );

    /**
     * @notice Anchor a tamper-evident record hash on-chain.
     * @param recordHash Keccak-256 hash of the canonical JSON record
     * @param cid Optional IPFS CID or reference string (pass "" if none)
     */
    function anchorRecord(bytes32 recordHash, string calldata cid) external {
        require(recordHash != bytes32(0), "Invalid record hash");
        require(_records[recordHash].anchoredAt == 0, "Record already anchored");

        _records[recordHash] = Record({
            submitter: msg.sender,
            anchoredAt: uint64(block.timestamp),
            cid: cid
        });
        allHashes.push(recordHash);

        emit MatchAnchored(recordHash, msg.sender, uint64(block.timestamp), cid);
    }

    /**
     * @notice Verify whether a record hash exists on-chain and retrieve its provenance.
     * @param recordHash Keccak-256 hash to query
     * @return exists True if the record is anchored
     * @return submitter Address that submitted the anchor transaction
     * @return anchoredAt Block timestamp of anchoring
     * @return cid The attached metadata reference or IPFS CID
     */
    function verifyRecord(bytes32 recordHash)
        external
        view
        returns (
            bool exists,
            address submitter,
            uint64 anchoredAt,
            string memory cid
        )
    {
        Record storage r = _records[recordHash];
        return (r.anchoredAt > 0, r.submitter, r.anchoredAt, r.cid);
    }

    /**
     * @notice Returns total number of anchored records.
     */
    function totalRecords() external view returns (uint256) {
        return allHashes.length;
    }
}
