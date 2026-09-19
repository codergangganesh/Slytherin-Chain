"""Blockchain client for anchoring Merkle roots onto the IntegrityAnchor smart contract."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from web3 import AsyncHTTPProvider, AsyncWeb3
except ImportError:
    from web3 import AsyncWeb3  # type: ignore

    AsyncHTTPProvider = getattr(AsyncWeb3, "AsyncHTTPProvider", None)  # type: ignore

from app.config.settings import get_settings
from app.domain.exceptions import BlockchainClientError


@dataclass(frozen=True)
class AnchoredRootResult:
    """Receipt of an on-chain anchor transaction."""

    tx_hash: str
    block_number: int
    contract_address: str
    merkle_root: str
    from_sequence: int
    to_sequence: int


class AnchorChainClient:
    """Asynchronous Web3 client for the IntegrityAnchor smart contract."""

    def __init__(
        self,
        rpc_url: str | None = None,
        contract_address: str | None = None,
        private_key: str | None = None,
    ) -> None:
        self._settings = get_settings()
        self._rpc_url = rpc_url or self._settings.anchor_chain_rpc_url
        self._contract_address = contract_address or self._settings.anchor_contract_address
        self._private_key = private_key or self._settings.anchor_wallet_private_key
        self._w3: AsyncWeb3 | None = None
        self._abi = self._load_abi()

    def _load_abi(self) -> list[dict[str, Any]]:
        """Load ABI from JSON artifact."""
        abi_file = Path(__file__).resolve().parent / "integrity_anchor_abi.json"
        if abi_file.exists():
            with open(abi_file, encoding="utf-8") as f:
                return json.load(f)
        return []

    async def get_w3(self) -> AsyncWeb3:
        """Lazily initialize AsyncWeb3 connection."""
        if self._w3 is None:
            if AsyncHTTPProvider is not None:
                self._w3 = AsyncWeb3(AsyncHTTPProvider(self._rpc_url))
            else:
                self._w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(self._rpc_url))
        return self._w3

    async def check_connection(self) -> bool:
        """Check whether the configured RPC endpoint is reachable."""
        try:
            w3 = await self.get_w3()
            return await w3.is_connected()
        except Exception:
            return False

    async def anchor_root(
        self,
        merkle_root: str,
        from_sequence: int,
        to_sequence: int,
    ) -> AnchoredRootResult:
        """Submit a Merkle root to the smart contract."""
        w3 = await self.get_w3()
        if not await w3.is_connected():
            raise BlockchainClientError(f"Cannot connect to RPC at {self._rpc_url}")

        if not self._contract_address:
            # Simulated transaction in offline dev mode
            import hashlib

            sim_tx = (
                "0x"
                + hashlib.sha256(
                    f"{merkle_root}:{from_sequence}:{to_sequence}".encode()
                ).hexdigest()
            )
            return AnchoredRootResult(
                tx_hash=sim_tx,
                block_number=1,
                contract_address="0x0000000000000000000000000000000000000000",
                merkle_root=merkle_root,
                from_sequence=from_sequence,
                to_sequence=to_sequence,
            )

        try:
            account = w3.eth.account.from_key(self._private_key)
            contract = w3.eth.contract(
                address=AsyncWeb3.to_checksum_address(self._contract_address),
                abi=self._abi,
            )

            root_bytes = bytes.fromhex(
                merkle_root[2:] if merkle_root.startswith("0x") else merkle_root
            )

            nonce = await w3.eth.get_transaction_count(account.address)
            chain_id = self._settings.anchor_chain_id

            tx = await contract.functions.anchorRoot(
                root_bytes,
                from_sequence,
                to_sequence,
            ).build_transaction(
                {
                    "from": account.address,
                    "nonce": nonce,
                    "chainId": chain_id,
                    "gas": 150000,
                }
            )

            signed_tx = account.sign_transaction(tx)
            tx_hash_bytes = await w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash = "0x" + tx_hash_bytes.hex()

            receipt = await w3.eth.wait_for_transaction_receipt(
                tx_hash_bytes,
                timeout=120,
            )

            return AnchoredRootResult(
                tx_hash=tx_hash,
                block_number=receipt["blockNumber"],
                contract_address=self._contract_address,
                merkle_root=merkle_root,
                from_sequence=from_sequence,
                to_sequence=to_sequence,
            )
        except Exception as err:
            raise BlockchainClientError(f"Failed to anchor root on chain: {err}") from err
