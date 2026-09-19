"""Unit tests for Merkle tree construction and inclusion proof verification."""

from __future__ import annotations

import hashlib
import pytest

from app.services.integrity.merkle_tree import MerkleTree


def test_merkle_tree_single_leaf() -> None:
    """Test tree with single leaf."""
    leaf = hashlib.sha256(b"entry_1").hexdigest()
    tree = MerkleTree([leaf])
    assert tree.root.startswith("0x")
    assert len(tree.root) == 66

    proof = tree.get_proof(0)
    assert MerkleTree.verify_proof(proof) is True


def test_merkle_tree_even_leaves() -> None:
    """Test tree with even count of leaves."""
    leaves = [hashlib.sha256(f"entry_{i}".encode()).hexdigest() for i in range(4)]
    tree = MerkleTree(leaves)

    for i in range(4):
        proof = tree.get_proof(i)
        assert MerkleTree.verify_proof(proof) is True


def test_merkle_tree_odd_leaves() -> None:
    """Test tree with odd count of leaves (promoting odd node)."""
    leaves = [hashlib.sha256(f"entry_{i}".encode()).hexdigest() for i in range(5)]
    tree = MerkleTree(leaves)

    for i in range(5):
        proof = tree.get_proof(i)
        assert MerkleTree.verify_proof(proof) is True


def test_merkle_proof_tamper_rejection() -> None:
    """Test that a tampered leaf fails proof verification."""
    leaves = [hashlib.sha256(f"entry_{i}".encode()).hexdigest() for i in range(4)]
    tree = MerkleTree(leaves)
    proof = tree.get_proof(0)

    # Tamper the leaf hash in proof
    tampered_proof = type(proof)(
        leaf_hash=hashlib.sha256(b"tampered_data").hexdigest(),
        leaf_index=proof.leaf_index,
        total_leaves=proof.total_leaves,
        proof_steps=proof.proof_steps,
        root=proof.root,
    )
    assert MerkleTree.verify_proof(tampered_proof) is False
