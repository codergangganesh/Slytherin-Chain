// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import "forge-std/Test.sol";
import "../src/IntegrityAnchor.sol";

/**
 * @title IntegrityAnchorTest
 * @notice Foundry tests for the IntegrityAnchor contract.
 * @dev Covers: successful anchor, unauthorized caller, overlapping ranges,
 *      event emission, getter correctness, and anchorer management.
 */
contract IntegrityAnchorTest is Test {
    IntegrityAnchor public anchor;
    address public owner;
    address public unauthorized = address(0xBEEF);
    address public newAnchorer = address(0xCAFE);

    function setUp() public {
        owner = address(this);
        anchor = new IntegrityAnchor();
    }

    // ── Successful anchor ────────────────────────────────────────────────

    function test_anchor_root_success() public {
        bytes32 root = keccak256("test-root");

        anchor.anchorRoot(root, 1, 10);

        IntegrityAnchor.Batch memory batch = anchor.getBatch(0);
        assertEq(batch.merkleRoot, root);
        assertEq(batch.fromSequence, 1);
        assertEq(batch.toSequence, 10);
        assertEq(batch.anchorer, owner);
        assertEq(anchor.batchCount(), 1);
        assertEq(anchor.lastToSequence(), 10);
    }

    // ── Multiple batches ─────────────────────────────────────────────────

    function test_anchor_multiple_batches() public {
        anchor.anchorRoot(keccak256("root-1"), 1, 10);
        anchor.anchorRoot(keccak256("root-2"), 11, 20);

        assertEq(anchor.batchCount(), 2);
        assertEq(anchor.lastToSequence(), 20);

        IntegrityAnchor.Batch memory batch2 = anchor.getBatch(1);
        assertEq(batch2.fromSequence, 11);
        assertEq(batch2.toSequence, 20);
    }

    // ── Unauthorized caller reverts ──────────────────────────────────────

    function test_anchor_root_unauthorized_reverts() public {
        vm.prank(unauthorized);
        vm.expectRevert(IntegrityAnchor.NotAnchorer.selector);
        anchor.anchorRoot(keccak256("root"), 1, 10);
    }

    // ── Overlapping range reverts ────────────────────────────────────────

    function test_overlapping_sequence_reverts() public {
        anchor.anchorRoot(keccak256("root-1"), 1, 10);

        vm.expectRevert(IntegrityAnchor.OverlappingSequence.selector);
        anchor.anchorRoot(keccak256("root-2"), 5, 15);
    }

    // ── Invalid range reverts ────────────────────────────────────────────

    function test_invalid_sequence_range_reverts() public {
        vm.expectRevert(IntegrityAnchor.InvalidSequenceRange.selector);
        anchor.anchorRoot(keccak256("root"), 10, 5);
    }

    // ── Event emission ───────────────────────────────────────────────────

    function test_anchor_root_emits_event() public {
        bytes32 root = keccak256("root-event");

        vm.expectEmit(true, false, false, true);
        emit IntegrityAnchor.RootAnchored(0, root, 1, 10, block.timestamp);

        anchor.anchorRoot(root, 1, 10);
    }

    // ── Anchorer management ──────────────────────────────────────────────

    function test_add_anchorer() public {
        anchor.addAnchorer(newAnchorer);
        assertTrue(anchor.authorizedAnchorers(newAnchorer));
    }

    function test_add_anchorer_unauthorized_reverts() public {
        vm.prank(unauthorized);
        vm.expectRevert(IntegrityAnchor.Unauthorized.selector);
        anchor.addAnchorer(newAnchorer);
    }

    function test_remove_anchorer() public {
        anchor.addAnchorer(newAnchorer);
        anchor.removeAnchorer(newAnchorer);
        assertFalse(anchor.authorizedAnchorers(newAnchorer));
    }

    function test_new_anchorer_can_anchor() public {
        anchor.addAnchorer(newAnchorer);

        vm.prank(newAnchorer);
        anchor.anchorRoot(keccak256("new-anchorer-root"), 1, 5);

        assertEq(anchor.batchCount(), 1);
    }

    // ── Getter correctness ───────────────────────────────────────────────

    function test_get_batch_returns_correct_data() public {
        bytes32 root = keccak256("getter-test");
        anchor.anchorRoot(root, 100, 200);

        IntegrityAnchor.Batch memory batch = anchor.getBatch(0);
        assertEq(batch.merkleRoot, root);
        assertEq(batch.fromSequence, 100);
        assertEq(batch.toSequence, 200);
        assertGt(batch.timestamp, 0);
    }
}
