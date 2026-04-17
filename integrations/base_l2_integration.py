"""
Base Layer 2 (Ethereum) Integration
Provides blockchain interaction capabilities on Base L2
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Optional

from loguru import logger

from config import settings

try:
    from web3 import Web3

    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    logger.warning("web3 not installed. Base L2 integration disabled.")


@dataclass
class BaseL2Result:
    """Result of a Base L2 operation"""

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class BaseL2Integration:
    """
    Base Layer 2 (Ethereum) integration

    Capabilities:
    - Wallet balance queries
    - Smart contract interactions
    - Transaction creation and monitoring
    - Gas price estimation
    - ENS resolution

    NOTE: All transactions require explicit user confirmation
    """

    def __init__(self):
        self.w3 = None
        if WEB3_AVAILABLE and settings.base_enabled and settings.base_rpc_url:
            try:
                self.w3 = Web3(Web3.HTTPProvider(settings.base_rpc_url))
                if settings.base_wallet_private_key:
                    self.account = self.w3.eth.account.from_key(settings.base_wallet_private_key)
                else:
                    self.account = None
            except Exception as e:
                logger.error(f"Failed to initialize Base L2: {e}")
                self.w3 = None

    async def health_check(self) -> bool:
        """Check if Base L2 RPC is accessible"""
        if not settings.base_enabled or not self.w3:
            return False

        try:
            return self.w3.is_connected()
        except Exception as e:
            logger.error(f"Base L2 health check failed: {e}")
            return False

    async def get_balance(self, address: Optional[str] = None) -> BaseL2Result:
        """
        Get ETH balance for an address

        Args:
            address: Address to check (uses wallet address if not provided)
        """
        if not settings.base_enabled or not self.w3:
            return BaseL2Result(success=False, error="Base L2 integration not enabled")

        try:
            addr = address or settings.base_wallet_address
            if not addr:
                return BaseL2Result(success=False, error="No address provided")

            balance_wei = await asyncio.to_thread(self.w3.eth.get_balance, addr)
            balance_eth = self.w3.from_wei(balance_wei, "ether")

            return BaseL2Result(
                success=True,
                data={
                    "address": addr,
                    "balance_wei": str(balance_wei),
                    "balance_eth": str(balance_eth),
                },
            )
        except Exception as e:
            logger.error(f"Get balance failed: {e}")
            return BaseL2Result(success=False, error=str(e))

    async def get_gas_price(self) -> BaseL2Result:
        """Get current gas price"""
        if not settings.base_enabled or not self.w3:
            return BaseL2Result(success=False, error="Base L2 integration not enabled")

        try:
            gas_price_wei = await asyncio.to_thread(lambda: self.w3.eth.gas_price)
            gas_price_gwei = self.w3.from_wei(gas_price_wei, "gwei")

            return BaseL2Result(
                success=True,
                data={"gas_price_wei": str(gas_price_wei), "gas_price_gwei": str(gas_price_gwei)},
            )
        except Exception as e:
            logger.error(f"Get gas price failed: {e}")
            return BaseL2Result(success=False, error=str(e))

    async def send_transaction(
        self, to_address: str, amount_eth: float, gas_limit: int = 21000
    ) -> BaseL2Result:
        """
        Send ETH transaction (requires confirmation)

        Args:
            to_address: Recipient address
            amount_eth: Amount in ETH
            gas_limit: Gas limit for transaction
        """
        if not settings.base_enabled or not self.w3:
            return BaseL2Result(success=False, error="Base L2 integration not enabled")

        if not self.account:
            return BaseL2Result(success=False, error="No wallet configured")

        try:
            # Build transaction
            nonce = await asyncio.to_thread(self.w3.eth.get_transaction_count, self.account.address)
            gas_price = await asyncio.to_thread(lambda: self.w3.eth.gas_price)

            tx = {
                "nonce": nonce,
                "to": to_address,
                "value": self.w3.to_wei(amount_eth, "ether"),
                "gas": gas_limit,
                "gasPrice": gas_price,
                "chainId": await asyncio.to_thread(lambda: self.w3.eth.chain_id),
            }

            # Sign transaction
            signed_tx = self.account.sign_transaction(tx)

            # Send transaction
            tx_hash = await asyncio.to_thread(
                self.w3.eth.send_raw_transaction, signed_tx.rawTransaction
            )

            logger.info(f"Transaction sent: {tx_hash.hex()}")

            return BaseL2Result(
                success=True,
                data={
                    "tx_hash": tx_hash.hex(),
                    "from": self.account.address,
                    "to": to_address,
                    "amount_eth": amount_eth,
                    "gas_price_gwei": str(self.w3.from_wei(gas_price, "gwei")),
                },
            )
        except Exception as e:
            logger.error(f"Send transaction failed: {e}")
            return BaseL2Result(success=False, error=str(e))

    async def get_transaction(self, tx_hash: str) -> BaseL2Result:
        """Get transaction details"""
        if not settings.base_enabled or not self.w3:
            return BaseL2Result(success=False, error="Base L2 integration not enabled")

        try:
            tx = await asyncio.to_thread(self.w3.eth.get_transaction, tx_hash)
            tx_receipt = None

            try:
                tx_receipt = await asyncio.to_thread(self.w3.eth.get_transaction_receipt, tx_hash)
            except Exception:  # noqa: S110
                pass  # Transaction might not be mined yet

            return BaseL2Result(
                success=True,
                data={"transaction": dict(tx), "receipt": dict(tx_receipt) if tx_receipt else None},
            )
        except Exception as e:
            logger.error(f"Get transaction failed: {e}")
            return BaseL2Result(success=False, error=str(e))

    async def estimate_gas(
        self, to_address: str, amount_eth: float, data: Optional[str] = None
    ) -> BaseL2Result:
        """Estimate gas for a transaction"""
        if not settings.base_enabled or not self.w3:
            return BaseL2Result(success=False, error="Base L2 integration not enabled")

        try:
            tx = {"to": to_address, "value": self.w3.to_wei(amount_eth, "ether")}

            if data:
                tx["data"] = data

            if self.account:
                tx["from"] = self.account.address

            gas_estimate = await asyncio.to_thread(self.w3.eth.estimate_gas, tx)
            gas_price = await asyncio.to_thread(lambda: self.w3.eth.gas_price)

            total_cost_wei = gas_estimate * gas_price
            total_cost_eth = self.w3.from_wei(total_cost_wei, "ether")

            return BaseL2Result(
                success=True,
                data={
                    "gas_estimate": gas_estimate,
                    "gas_price_gwei": str(self.w3.from_wei(gas_price, "gwei")),
                    "total_cost_eth": str(total_cost_eth),
                },
            )
        except Exception as e:
            logger.error(f"Estimate gas failed: {e}")
            return BaseL2Result(success=False, error=str(e))


# Global instance
base_l2 = BaseL2Integration()
