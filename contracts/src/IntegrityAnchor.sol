// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

/**
 * @title IntegrityAnchor
 * @notice Stores Merkle roots of audit-trail batches for tamper-evident integrity verification.
 * @dev Authorized anchorers submit batch roots with sequence ranges. Overlapping or
 *      non-increasing sequences are rejected. This contract is the on-chain anchor for
 *      SentinelChain's hash-chain audit ledger.
 *
 * Full implementation will be added in Phase 6. This placeholder ensures the Foundry
 * project compiles and tests can scaffold against it.
 */
contract IntegrityAnchor {
    // ── Types ────────────────────────────────────────────────────────────────

    struct Batch {
        bytes32 merkleRoot;
        uint64 fromSequence;
        uint64 toSequence;
        uint256 timestamp;
        address anchorer;
    }

    // ── State ────────────────────────────────────────────────────────────────

    address public owner;
    uint256 public batchCount;
    uint64 public lastToSequence;

    mapping(uint256 => Batch) public batches;
    mapping(address => bool) public authorizedAnchorers;

    // ── Events ───────────────────────────────────────────────────────────────

    event RootAnchored(
        uint256 indexed batchId,
        bytes32 merkleRoot,
        uint64 fromSequence,
        uint64 toSequence,
        uint256 timestamp
    );

    event AnchorerAdded(address indexed anchorer);
    event AnchorerRemoved(address indexed anchorer);

    // ── Errors ───────────────────────────────────────────────────────────────

    error Unauthorized();
    error NotAnchorer();
    error InvalidSequenceRange();
    error OverlappingSequence();

    // ── Modifiers ────────────────────────────────────────────────────────────

    modifier onlyOwner() {
        if (msg.sender != owner) revert Unauthorized();
        _;
    }

    modifier onlyAnchorer() {
        if (!authorizedAnchorers[msg.sender]) revert NotAnchorer();
        _;
    }

    // ── Constructor ──────────────────────────────────────────────────────────

    constructor() {
        owner = msg.sender;
        authorizedAnchorers[msg.sender] = true;
    }

    // ── Anchorer management ──────────────────────────────────────────────────

    /**
     * @notice Add an authorized anchorer address.
     * @param anchorer The address to authorize.
     */
    function addAnchorer(address anchorer) external onlyOwner {
        authorizedAnchorers[anchorer] = true;
        emit AnchorerAdded(anchorer);
    }

    /**
     * @notice Remove an authorized anchorer address.
     * @param anchorer The address to deauthorize.
     */
    function removeAnchorer(address anchorer) external onlyOwner {
        authorizedAnchorers[anchorer] = false;
        emit AnchorerRemoved(anchorer);
    }

    // ── Anchoring ────────────────────────────────────────────────────────────

    /**
     * @notice Anchor a Merkle root for a batch of audit ledger entries.
     * @param merkleRoot The Merkle root hash of the batch.
     * @param fromSequence The first sequence number in the batch (inclusive).
     * @param toSequence The last sequence number in the batch (inclusive).
     */
    function anchorRoot(
        bytes32 merkleRoot,
        uint64 fromSequence,
        uint64 toSequence
    ) external onlyAnchorer {
        if (fromSequence > toSequence) revert InvalidSequenceRange();
        if (fromSequence <= lastToSequence && batchCount > 0) revert OverlappingSequence();

        uint256 batchId = batchCount;
        batches[batchId] = Batch({
            merkleRoot: merkleRoot,
            fromSequence: fromSequence,
            toSequence: toSequence,
            timestamp: block.timestamp,
            anchorer: msg.sender
        });

        lastToSequence = toSequence;
        batchCount++;

        emit RootAnchored(batchId, merkleRoot, fromSequence, toSequence, block.timestamp);
    }

    // ── Views ────────────────────────────────────────────────────────────────

    /**
     * @notice Retrieve a batch by its ID.
     * @param batchId The batch identifier (0-indexed).
     * @return The Batch struct for the given ID.
     */
    function getBatch(uint256 batchId) external view returns (Batch memory) {
        return batches[batchId];
    }
}
