"""
Plaid Banking Integration
Connects to bank accounts for balance/transaction data and ACH transfers
"""

from dataclasses import dataclass
from typing import Any, Optional

import httpx
from loguru import logger

from config import settings


@dataclass
class PlaidResult:
    """Result of a Plaid operation"""

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class PlaidIntegration:
    """
    Plaid API integration for banking data

    Capabilities:
    - Link bank accounts (get access tokens via Link flow)
    - Fetch account balances
    - Fetch transaction history
    - ACH transfer initiation (Plaid Transfer API)
    - Income/identity verification

    NOTE: Actual account linking requires the Plaid Link UI flow.
          This module handles server-side API calls only.
    """

    ENV_URLS = {
        "sandbox": "https://sandbox.plaid.com",
        "development": "https://development.plaid.com",
        "production": "https://production.plaid.com",
    }

    def __init__(self):
        env = settings.plaid_env or "sandbox"
        self.base_url = self.ENV_URLS.get(env, self.ENV_URLS["sandbox"])
        self.client_id = settings.plaid_client_id
        self.secret = settings.plaid_secret

    def _auth_payload(self) -> dict:
        return {"client_id": self.client_id, "secret": self.secret}

    async def health_check(self) -> bool:
        """Verify Plaid credentials are valid"""
        if not settings.plaid_enabled or not self.client_id or not self.secret:
            return False
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/categories/get",
                    json=self._auth_payload(),
                    timeout=10.0,
                )
                return resp.status_code == 200
        except Exception as e:
            logger.error(f"Plaid health check failed: {e}")
            return False

    async def exchange_public_token(self, public_token: str) -> PlaidResult:
        """
        Exchange a Plaid Link public token for a permanent access token.
        Call this after the user completes the Link flow in the UI.
        """
        if not settings.plaid_enabled:
            return PlaidResult(success=False, error="Plaid integration not enabled")
        try:
            payload = {**self._auth_payload(), "public_token": public_token}
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/item/public_token/exchange",
                    json=payload,
                    timeout=10.0,
                )
            data = resp.json()
            if resp.status_code == 200:
                return PlaidResult(success=True, data=data)
            return PlaidResult(success=False, error=data.get("error_message", resp.text))
        except Exception as e:
            logger.error(f"Plaid token exchange failed: {e}")
            return PlaidResult(success=False, error=str(e))

    async def get_balances(self, access_token: str) -> PlaidResult:
        """Fetch real-time account balances for a linked item"""
        if not settings.plaid_enabled:
            return PlaidResult(success=False, error="Plaid integration not enabled")
        try:
            payload = {**self._auth_payload(), "access_token": access_token}
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/accounts/balance/get",
                    json=payload,
                    timeout=15.0,
                )
            data = resp.json()
            if resp.status_code == 200:
                return PlaidResult(success=True, data=data.get("accounts", []))
            return PlaidResult(success=False, error=data.get("error_message", resp.text))
        except Exception as e:
            logger.error(f"Plaid get_balances failed: {e}")
            return PlaidResult(success=False, error=str(e))

    async def get_transactions(
        self,
        access_token: str,
        start_date: str,
        end_date: str,
        count: int = 100,
    ) -> PlaidResult:
        """
        Fetch transactions for a linked item.

        Args:
            access_token: Item access token
            start_date: ISO date string YYYY-MM-DD
            end_date:   ISO date string YYYY-MM-DD
            count:      Max number of transactions (max 500)
        """
        if not settings.plaid_enabled:
            return PlaidResult(success=False, error="Plaid integration not enabled")
        try:
            payload = {
                **self._auth_payload(),
                "access_token": access_token,
                "start_date": start_date,
                "end_date": end_date,
                "options": {"count": min(count, 500)},
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/transactions/get",
                    json=payload,
                    timeout=20.0,
                )
            data = resp.json()
            if resp.status_code == 200:
                return PlaidResult(success=True, data=data)
            return PlaidResult(success=False, error=data.get("error_message", resp.text))
        except Exception as e:
            logger.error(f"Plaid get_transactions failed: {e}")
            return PlaidResult(success=False, error=str(e))

    async def create_transfer(
        self,
        access_token: str,
        account_id: str,
        amount: str,
        description: str,
        network: str = "ach",
        transfer_type: str = "credit",
    ) -> PlaidResult:
        """
        Initiate an ACH transfer (requires Plaid Transfer product).

        NOTE: This is a write operation that moves real money. Big Homie
              will require explicit human confirmation before calling this.

        Args:
            access_token:  Item access token
            account_id:    Plaid account_id for the source/destination account
            amount:        Dollar amount as string e.g. "10.00"
            description:   ACH description (15 char max for most banks)
            network:       "ach" or "same-day-ach"
            transfer_type: "credit" (send money to account) or "debit" (pull from account)
        """
        if not settings.plaid_enabled:
            return PlaidResult(success=False, error="Plaid integration not enabled")
        try:
            payload = {
                **self._auth_payload(),
                "access_token": access_token,
                "account_id": account_id,
                "type": transfer_type,
                "network": network,
                "amount": amount,
                "description": description[:15],
                "ach_class": "ppd",
                "user": {"legal_name": "Big Homie User"},
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/transfer/create",
                    json=payload,
                    timeout=20.0,
                )
            data = resp.json()
            if resp.status_code == 200:
                logger.info(f"Plaid transfer created: {data.get('transfer', {}).get('id')}")
                return PlaidResult(success=True, data=data.get("transfer"))
            return PlaidResult(success=False, error=data.get("error_message", resp.text))
        except Exception as e:
            logger.error(f"Plaid create_transfer failed: {e}")
            return PlaidResult(success=False, error=str(e))

    async def get_identity(self, access_token: str) -> PlaidResult:
        """Fetch identity (owner name, addresses, emails) for a linked item"""
        if not settings.plaid_enabled:
            return PlaidResult(success=False, error="Plaid integration not enabled")
        try:
            payload = {**self._auth_payload(), "access_token": access_token}
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/identity/get",
                    json=payload,
                    timeout=15.0,
                )
            data = resp.json()
            if resp.status_code == 200:
                return PlaidResult(success=True, data=data.get("accounts", []))
            return PlaidResult(success=False, error=data.get("error_message", resp.text))
        except Exception as e:
            logger.error(f"Plaid get_identity failed: {e}")
            return PlaidResult(success=False, error=str(e))


# Global instance
plaid = PlaidIntegration()
