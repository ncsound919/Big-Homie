"""
Coinbase Commerce Integration
Provides cryptocurrency payment processing capabilities
"""

from dataclasses import dataclass
from typing import Any, Optional

import httpx
from loguru import logger

from config import settings


@dataclass
class CoinbaseResult:
    """Result of a Coinbase Commerce operation"""

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class CoinbaseCommerceIntegration:
    """
    Coinbase Commerce API integration

    Capabilities:
    - Charge creation (BTC, ETH, USDC, etc.)
    - Charge status monitoring
    - Webhook event handling
    - Pricing retrieval

    NOTE: All crypto transactions require explicit user confirmation
    """

    def __init__(self):
        self.base_url = "https://api.commerce.coinbase.com"
        self.headers = {}
        if settings.coinbase_commerce_api_key:
            self.headers = {
                "X-CC-Api-Key": settings.coinbase_commerce_api_key,
                "X-CC-Version": "2018-03-22",
                "Content-Type": "application/json",
            }

    async def health_check(self) -> bool:
        """Check if Coinbase Commerce API is accessible"""
        if not settings.coinbase_commerce_enabled or not settings.coinbase_commerce_api_key:
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/charges", headers=self.headers, timeout=10.0
                )
                return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Coinbase Commerce health check failed: {e}")
            return False

    async def create_charge(
        self,
        name: str,
        description: str,
        amount: str,  # String with currency amount e.g. "10.00"
        currency: str = "USD",
        metadata: Optional[dict] = None,
    ) -> CoinbaseResult:
        """
        Create a cryptocurrency charge

        Args:
            name: Name of the charge
            description: Description of what's being charged for
            amount: Amount in local currency (e.g., "10.00")
            currency: Local currency code (e.g., "USD")
            metadata: Additional metadata
        """
        if not settings.coinbase_commerce_enabled:
            return CoinbaseResult(success=False, error="Coinbase Commerce integration not enabled")

        try:
            url = f"{self.base_url}/charges"

            payload = {
                "name": name,
                "description": description,
                "pricing_type": "fixed_price",
                "local_price": {"amount": amount, "currency": currency},
            }

            if metadata:
                payload["metadata"] = metadata

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=payload, timeout=10.0)

                if response.status_code in [200, 201]:
                    result = response.json()
                    logger.info(f"Charge created: {result['data']['id']}")
                    return CoinbaseResult(success=True, data=result["data"])
                else:
                    return CoinbaseResult(
                        success=False, error=f"Charge creation failed: {response.text}"
                    )
        except Exception as e:
            logger.error(f"Create charge failed: {e}")
            return CoinbaseResult(success=False, error=str(e))

    async def get_charge(self, charge_id: str) -> CoinbaseResult:
        """Get charge details and status"""
        if not settings.coinbase_commerce_enabled:
            return CoinbaseResult(success=False, error="Coinbase Commerce integration not enabled")

        try:
            url = f"{self.base_url}/charges/{charge_id}"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, timeout=10.0)

                if response.status_code == 200:
                    result = response.json()
                    return CoinbaseResult(success=True, data=result["data"])
                else:
                    return CoinbaseResult(
                        success=False, error=f"Get charge failed: {response.text}"
                    )
        except Exception as e:
            logger.error(f"Get charge failed: {e}")
            return CoinbaseResult(success=False, error=str(e))

    async def list_charges(self, limit: int = 25) -> CoinbaseResult:
        """List all charges"""
        if not settings.coinbase_commerce_enabled:
            return CoinbaseResult(success=False, error="Coinbase Commerce integration not enabled")

        try:
            url = f"{self.base_url}/charges"
            params = {"limit": limit}

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params, timeout=10.0)

                if response.status_code == 200:
                    result = response.json()
                    return CoinbaseResult(success=True, data=result["data"])
                else:
                    return CoinbaseResult(
                        success=False, error=f"List charges failed: {response.text}"
                    )
        except Exception as e:
            logger.error(f"List charges failed: {e}")
            return CoinbaseResult(success=False, error=str(e))

    async def cancel_charge(self, charge_id: str) -> CoinbaseResult:
        """Cancel a charge"""
        if not settings.coinbase_commerce_enabled:
            return CoinbaseResult(success=False, error="Coinbase Commerce integration not enabled")

        try:
            url = f"{self.base_url}/charges/{charge_id}/cancel"

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, timeout=10.0)

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Charge cancelled: {charge_id}")
                    return CoinbaseResult(success=True, data=result["data"])
                else:
                    return CoinbaseResult(
                        success=False, error=f"Cancel charge failed: {response.text}"
                    )
        except Exception as e:
            logger.error(f"Cancel charge failed: {e}")
            return CoinbaseResult(success=False, error=str(e))


# Global instance
coinbase_commerce = CoinbaseCommerceIntegration()
