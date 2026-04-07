"""
Stripe Integration
Provides tools for payment processing and subscription management
"""
import httpx
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from loguru import logger
from config import settings

@dataclass
class StripeResult:
    """Result of a Stripe operation"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None

class StripeIntegration:
    """
    Stripe API integration

    Capabilities:
    - Customer management
    - Payment intents
    - Subscriptions
    - Invoices
    - Payment methods

    NOTE: All financial operations require explicit user confirmation
    """

    def __init__(self):
        self.base_url = "https://api.stripe.com/v1"
        self.headers = {}
        if settings.stripe_api_key:
            self.headers = {
                "Authorization": f"Bearer {settings.stripe_api_key}",
                "Content-Type": "application/x-www-form-urlencoded"
            }

    async def health_check(self) -> bool:
        """Check if Stripe API is accessible"""
        if not settings.stripe_enabled or not settings.stripe_api_key:
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/balance",
                    headers=self.headers,
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Stripe health check failed: {e}")
            return False

    # Customer Management
    async def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> StripeResult:
        """Create a new customer"""
        if not settings.stripe_enabled:
            return StripeResult(success=False, error="Stripe integration not enabled")

        try:
            url = f"{self.base_url}/customers"

            data = {"email": email}
            if name:
                data["name"] = name
            if metadata:
                for key, value in metadata.items():
                    data[f"metadata[{key}]"] = value

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    data=data,
                    timeout=10.0
                )

                if response.status_code in [200, 201]:
                    return StripeResult(success=True, data=response.json())
                else:
                    return StripeResult(
                        success=False,
                        error=f"Customer creation failed: {response.text}"
                    )
        except Exception as e:
            logger.error(f"Create customer failed: {e}")
            return StripeResult(success=False, error=str(e))

    async def get_customer(self, customer_id: str) -> StripeResult:
        """Get customer details"""
        if not settings.stripe_enabled:
            return StripeResult(success=False, error="Stripe integration not enabled")

        try:
            url = f"{self.base_url}/customers/{customer_id}"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, timeout=10.0)

                if response.status_code == 200:
                    return StripeResult(success=True, data=response.json())
                else:
                    return StripeResult(
                        success=False,
                        error=f"Get customer failed: {response.text}"
                    )
        except Exception as e:
            logger.error(f"Get customer failed: {e}")
            return StripeResult(success=False, error=str(e))

    async def list_customers(self, limit: int = 10) -> StripeResult:
        """List customers"""
        if not settings.stripe_enabled:
            return StripeResult(success=False, error="Stripe integration not enabled")

        try:
            url = f"{self.base_url}/customers"
            params = {"limit": limit}

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return StripeResult(success=True, data=data.get("data", []))
                else:
                    return StripeResult(
                        success=False,
                        error=f"List customers failed: {response.text}"
                    )
        except Exception as e:
            logger.error(f"List customers failed: {e}")
            return StripeResult(success=False, error=str(e))

    # Payment Intents
    async def create_payment_intent(
        self,
        amount: int,  # Amount in cents
        currency: str = "usd",
        customer_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> StripeResult:
        """Create a payment intent (requires confirmation)"""
        if not settings.stripe_enabled:
            return StripeResult(success=False, error="Stripe integration not enabled")

        try:
            url = f"{self.base_url}/payment_intents"

            data = {
                "amount": amount,
                "currency": currency
            }

            if customer_id:
                data["customer"] = customer_id
            if description:
                data["description"] = description

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    data=data,
                    timeout=10.0
                )

                if response.status_code in [200, 201]:
                    result = response.json()
                    logger.info(f"Payment intent created: {result['id']} for ${amount/100:.2f}")
                    return StripeResult(success=True, data=result)
                else:
                    return StripeResult(
                        success=False,
                        error=f"Payment intent creation failed: {response.text}"
                    )
        except Exception as e:
            logger.error(f"Create payment intent failed: {e}")
            return StripeResult(success=False, error=str(e))

    async def get_payment_intent(self, payment_intent_id: str) -> StripeResult:
        """Get payment intent details"""
        if not settings.stripe_enabled:
            return StripeResult(success=False, error="Stripe integration not enabled")

        try:
            url = f"{self.base_url}/payment_intents/{payment_intent_id}"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, timeout=10.0)

                if response.status_code == 200:
                    return StripeResult(success=True, data=response.json())
                else:
                    return StripeResult(
                        success=False,
                        error=f"Get payment intent failed: {response.text}"
                    )
        except Exception as e:
            logger.error(f"Get payment intent failed: {e}")
            return StripeResult(success=False, error=str(e))

    # Subscriptions
    async def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        metadata: Optional[Dict] = None
    ) -> StripeResult:
        """Create a subscription (requires confirmation)"""
        if not settings.stripe_enabled:
            return StripeResult(success=False, error="Stripe integration not enabled")

        try:
            url = f"{self.base_url}/subscriptions"

            data = {
                "customer": customer_id,
                "items[0][price]": price_id
            }

            if metadata:
                for key, value in metadata.items():
                    data[f"metadata[{key}]"] = value

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    data=data,
                    timeout=10.0
                )

                if response.status_code in [200, 201]:
                    result = response.json()
                    logger.info(f"Subscription created: {result['id']}")
                    return StripeResult(success=True, data=result)
                else:
                    return StripeResult(
                        success=False,
                        error=f"Subscription creation failed: {response.text}"
                    )
        except Exception as e:
            logger.error(f"Create subscription failed: {e}")
            return StripeResult(success=False, error=str(e))

    async def cancel_subscription(self, subscription_id: str) -> StripeResult:
        """Cancel a subscription (requires confirmation)"""
        if not settings.stripe_enabled:
            return StripeResult(success=False, error="Stripe integration not enabled")

        try:
            url = f"{self.base_url}/subscriptions/{subscription_id}"

            async with httpx.AsyncClient() as client:
                response = await client.delete(url, headers=self.headers, timeout=10.0)

                if response.status_code == 200:
                    logger.info(f"Subscription cancelled: {subscription_id}")
                    return StripeResult(success=True, data=response.json())
                else:
                    return StripeResult(
                        success=False,
                        error=f"Subscription cancellation failed: {response.text}"
                    )
        except Exception as e:
            logger.error(f"Cancel subscription failed: {e}")
            return StripeResult(success=False, error=str(e))

    async def list_subscriptions(self, customer_id: Optional[str] = None) -> StripeResult:
        """List subscriptions"""
        if not settings.stripe_enabled:
            return StripeResult(success=False, error="Stripe integration not enabled")

        try:
            url = f"{self.base_url}/subscriptions"
            params = {}
            if customer_id:
                params["customer"] = customer_id

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return StripeResult(success=True, data=data.get("data", []))
                else:
                    return StripeResult(
                        success=False,
                        error=f"List subscriptions failed: {response.text}"
                    )
        except Exception as e:
            logger.error(f"List subscriptions failed: {e}")
            return StripeResult(success=False, error=str(e))

# Global instance
stripe = StripeIntegration()
