"""Domain-separated Merkle tree implementation with inclusion proof generation and verification."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class MerkleProofStep:
    """Single step in a Merkle inclusion proof."""

    position: str  # "left" or "right"
    hash_value: str


@dataclass(frozen=True)
class MerkleProof:
    """Cryptographic proof of inclusion for a specific leaf."""

    leaf_hash: str
    leaf_index: int
    total_leaves: int
    proof_steps: list[MerkleProofStep]
    root: str


class MerkleTree:
    """Cryptographic Merkle tree using SHA-256 with domain separation.

    Domain separation:
        Leaf hash = SHA256( 0x00 || entry_hash_bytes )
        Internal node = SHA256( 0x01 || left_child || right_child )

    Odd leaf count strategy:
        Promotes the single odd node to the parent layer directly without duplication.
    """

    LEAF_PREFIX = b"\x00"
    INTERNAL_PREFIX = b"\x01"

    def __init__(self, leaf_hashes: list[str]) -> None:
        if not leaf_hashes:
            raise ValueError("Cannot construct MerkleTree with zero leaves.")
        self._raw_leaves = leaf_hashes
        self._leaf_nodes = [self._hash_leaf(h) for h in leaf_hashes]
        self._layers: list[list[str]] = [self._leaf_nodes]
        self._build_tree()

    @classmethod
    def _hash_leaf(cls, entry_hash: str) -> str:
        """Hash leaf with domain prefix 0x00."""
        raw_bytes = (
            bytes.fromhex(entry_hash) if len(entry_hash) == 64 else entry_hash.encode("utf-8")
        )
        return hashlib.sha256(cls.LEAF_PREFIX + raw_bytes).hexdigest()

    @classmethod
    def _hash_internal(cls, left_hex: str, right_hex: str) -> str:
        """Hash two child nodes with domain prefix 0x01."""
        left_bytes = bytes.fromhex(left_hex)
        right_bytes = bytes.fromhex(right_hex)
        return hashlib.sha256(cls.INTERNAL_PREFIX + left_bytes + right_bytes).hexdigest()

    def _build_tree(self) -> None:
        """Construct layers bottom-up up to the root."""
        current_layer = self._leaf_nodes
        while len(current_layer) > 1:
            next_layer: list[str] = []
            i = 0
            while i < len(current_layer):
                if i + 1 < len(current_layer):
                    # Pair nodes
                    parent = self._hash_internal(current_layer[i], current_layer[i + 1])
                    next_layer.append(parent)
                    i += 2
                else:
                    # Odd node promoted directly
                    next_layer.append(current_layer[i])
                    i += 1
            self._layers.append(next_layer)
            current_layer = next_layer

    @property
    def root(self) -> str:
        """Retrieve root hash (32 bytes hex, formatted with optional 0x prefix)."""
        return "0x" + self._layers[-1][0]

    @property
    def raw_root(self) -> str:
        """Retrieve 64-char hex string root without 0x prefix."""
        return self._layers[-1][0]

    def get_proof(self, leaf_index: int) -> MerkleProof:
        """Generate an inclusion proof for a leaf index."""
        if not 0 <= leaf_index < len(self._raw_leaves):
            raise IndexError("Leaf index out of bounds")

        proof_steps: list[MerkleProofStep] = []
        idx = leaf_index

        for layer in self._layers[:-1]:
            is_odd = idx % 2 == 1
            pair_idx = idx - 1 if is_odd else idx + 1
            if pair_idx < len(layer):
                pos = "left" if is_odd else "right"
                proof_steps.append(MerkleProofStep(position=pos, hash_value=layer[pair_idx]))
            idx = idx // 2

        return MerkleProof(
            leaf_hash=self._raw_leaves[leaf_index],
            leaf_index=leaf_index,
            total_leaves=len(self._raw_leaves),
            proof_steps=proof_steps,
            root=self.root,
        )

    @classmethod
    def verify_proof(cls, proof: MerkleProof) -> bool:
        """Verify the validity of a Merkle inclusion proof."""
        current = cls._hash_leaf(proof.leaf_hash)

        for step in proof.proof_steps:
            if step.position == "left":
                current = cls._hash_internal(step.hash_value, current)
            else:
                current = cls._hash_internal(current, step.hash_value)

        computed_root = "0x" + current
        return computed_root.lower() == proof.root.lower()
