"""
Shopify Ecommerce Integration
Store management: products, orders, customers, inventory, and fulfillment
"""
import httpx
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from loguru import logger
from config import settings


@dataclass
class ShopifyResult:
    """Result of a Shopify operation"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class ShopifyIntegration:
    """
    Shopify Admin REST API integration

    Capabilities:
    - Product CRUD (create/read/update/delete)
    - Order management and fulfillment
    - Customer management
    - Inventory tracking
    - Discount / promo code creation
    - Webhook management

    NOTE: Requires a private app access token or Custom App token
          with appropriate scopes in your Shopify admin.
    """

    API_VERSION = "2024-04"

    def __init__(self):
        domain = settings.shopify_shop_domain
        token = settings.shopify_access_token
        self.base_url = f"https://{domain}/admin/api/{self.API_VERSION}" if domain else ""
        self.headers = {
            "X-Shopify-Access-Token": token,
            "Content-Type": "application/json",
        } if token else {}

    async def health_check(self) -> bool:
        """Verify Shopify credentials by hitting the shop endpoint"""
        if not settings.shopify_enabled or not self.base_url:
            return False
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/shop.json",
                    headers=self.headers,
                    timeout=10.0,
                )
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Shopify health check failed: {e}")
            return False

    # ── Products ──────────────────────────────────────────────────────────────

    async def list_products(self, limit: int = 50) -> ShopifyResult:
        """List products in the store"""
        if not settings.shopify_enabled:
            return ShopifyResult(success=False, error="Shopify integration not enabled")
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/products.json",
                    headers=self.headers,
                    params={"limit": limit},
                    timeout=15.0,
                )
            if resp.status_code == 200:
                return ShopifyResult(success=True, data=resp.json().get("products", []))
            return ShopifyResult(success=False, error=resp.text)
        except Exception as e:
            logger.error(f"Shopify list_products failed: {e}")
            return ShopifyResult(success=False, error=str(e))

    async def create_product(
        self,
        title: str,
        body_html: str,
        vendor: str,
        product_type: str,
        variants: Optional[List[Dict]] = None,
        tags: str = "",
        status: str = "draft",
    ) -> ShopifyResult:
        """
        Create a new product.

        Args:
            title:        Product title
            body_html:    Product description (HTML allowed)
            vendor:       Brand / vendor name
            product_type: Category
            variants:     List of variant dicts with price, sku, inventory_quantity, etc.
            tags:         Comma-separated tag string
            status:       "draft" | "active" | "archived"
        """
        if not settings.shopify_enabled:
            return ShopifyResult(success=False, error="Shopify integration not enabled")
        try:
            product: Dict[str, Any] = {
                "title": title,
                "body_html": body_html,
                "vendor": vendor,
                "product_type": product_type,
                "tags": tags,
                "status": status,
            }
            if variants:
                product["variants"] = variants
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/products.json",
                    headers=self.headers,
                    json={"product": product},
                    timeout=15.0,
                )
            if resp.status_code in (200, 201):
                data = resp.json().get("product", {})
                logger.info(f"Shopify product created: {data.get('id')} - {title}")
                return ShopifyResult(success=True, data=data)
            return ShopifyResult(success=False, error=resp.text)
        except Exception as e:
            logger.error(f"Shopify create_product failed: {e}")
            return ShopifyResult(success=False, error=str(e))

    async def update_product(self, product_id: int, updates: Dict) -> ShopifyResult:
        """Update an existing product"""
        if not settings.shopify_enabled:
            return ShopifyResult(success=False, error="Shopify integration not enabled")
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.put(
                    f"{self.base_url}/products/{product_id}.json",
                    headers=self.headers,
                    json={"product": {"id": product_id, **updates}},
                    timeout=15.0,
                )
            if resp.status_code == 200:
                return ShopifyResult(success=True, data=resp.json().get("product", {}))
            return ShopifyResult(success=False, error=resp.text)
        except Exception as e:
            logger.error(f"Shopify update_product failed: {e}")
            return ShopifyResult(success=False, error=str(e))

    # ── Orders ────────────────────────────────────────────────────────────────

    async def list_orders(
        self,
        status: str = "any",
        limit: int = 50,
    ) -> ShopifyResult:
        """List orders (status: open|closed|cancelled|any)"""
        if not settings.shopify_enabled:
            return ShopifyResult(success=False, error="Shopify integration not enabled")
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/orders.json",
                    headers=self.headers,
                    params={"status": status, "limit": limit},
                    timeout=15.0,
                )
            if resp.status_code == 200:
                return ShopifyResult(success=True, data=resp.json().get("orders", []))
            return ShopifyResult(success=False, error=resp.text)
        except Exception as e:
            logger.error(f"Shopify list_orders failed: {e}")
            return ShopifyResult(success=False, error=str(e))

    async def get_order(self, order_id: int) -> ShopifyResult:
        """Get a specific order by ID"""
        if not settings.shopify_enabled:
            return ShopifyResult(success=False, error="Shopify integration not enabled")
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/orders/{order_id}.json",
                    headers=self.headers,
                    timeout=10.0,
                )
            if resp.status_code == 200:
                return ShopifyResult(success=True, data=resp.json().get("order", {}))
            return ShopifyResult(success=False, error=resp.text)
        except Exception as e:
            logger.error(f"Shopify get_order failed: {e}")
            return ShopifyResult(success=False, error=str(e))

    async def fulfill_order(
        self,
        order_id: int,
        tracking_number: Optional[str] = None,
        tracking_company: Optional[str] = None,
        notify_customer: bool = True,
    ) -> ShopifyResult:
        """Mark an order as fulfilled (requires confirmation)"""
        if not settings.shopify_enabled:
            return ShopifyResult(success=False, error="Shopify integration not enabled")
        try:
            fulfillment: Dict[str, Any] = {
                "location_id": None,
                "notify_customer": notify_customer,
            }
            if tracking_number:
                fulfillment["tracking_number"] = tracking_number
            if tracking_company:
                fulfillment["tracking_company"] = tracking_company
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/orders/{order_id}/fulfillments.json",
                    headers=self.headers,
                    json={"fulfillment": fulfillment},
                    timeout=15.0,
                )
            if resp.status_code in (200, 201):
                data = resp.json().get("fulfillment", {})
                logger.info(f"Shopify order {order_id} fulfilled: {data.get('id')}")
                return ShopifyResult(success=True, data=data)
            return ShopifyResult(success=False, error=resp.text)
        except Exception as e:
            logger.error(f"Shopify fulfill_order failed: {e}")
            return ShopifyResult(success=False, error=str(e))

    # ── Customers ─────────────────────────────────────────────────────────────

    async def list_customers(self, limit: int = 50) -> ShopifyResult:
        """List customers"""
        if not settings.shopify_enabled:
            return ShopifyResult(success=False, error="Shopify integration not enabled")
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/customers.json",
                    headers=self.headers,
                    params={"limit": limit},
                    timeout=15.0,
                )
            if resp.status_code == 200:
                return ShopifyResult(success=True, data=resp.json().get("customers", []))
            return ShopifyResult(success=False, error=resp.text)
        except Exception as e:
            logger.error(f"Shopify list_customers failed: {e}")
            return ShopifyResult(success=False, error=str(e))

    # ── Discounts ─────────────────────────────────────────────────────────────

    async def create_discount_code(
        self,
        title: str,
        code: str,
        value: float,
        value_type: str = "percentage",
        usage_limit: Optional[int] = None,
    ) -> ShopifyResult:
        """
        Create a discount / promo code.

        Args:
            title:       Internal name
            code:        Customer-facing code string
            value:       Discount amount (percent or fixed)
            value_type:  "percentage" or "fixed_amount"
            usage_limit: Max total uses (None = unlimited)
        """
        if not settings.shopify_enabled:
            return ShopifyResult(success=False, error="Shopify integration not enabled")
        try:
            price_rule: Dict[str, Any] = {
                "title": title,
                "value_type": value_type,
                "value": f"-{value}",
                "customer_selection": "all",
                "target_type": "line_item",
                "target_selection": "all",
                "allocation_method": "across",
                "starts_at": "2000-01-01T00:00:00Z",
            }
            if usage_limit:
                price_rule["usage_limit"] = usage_limit
            async with httpx.AsyncClient() as client:
                pr_resp = await client.post(
                    f"{self.base_url}/price_rules.json",
                    headers=self.headers,
                    json={"price_rule": price_rule},
                    timeout=15.0,
                )
            if pr_resp.status_code not in (200, 201):
                return ShopifyResult(success=False, error=pr_resp.text)
            price_rule_id = pr_resp.json()["price_rule"]["id"]
            async with httpx.AsyncClient() as client:
                dc_resp = await client.post(
                    f"{self.base_url}/price_rules/{price_rule_id}/discount_codes.json",
                    headers=self.headers,
                    json={"discount_code": {"code": code}},
                    timeout=15.0,
                )
            if dc_resp.status_code in (200, 201):
                data = dc_resp.json().get("discount_code", {})
                logger.info(f"Shopify discount code created: {code}")
                return ShopifyResult(success=True, data=data)
            return ShopifyResult(success=False, error=dc_resp.text)
        except Exception as e:
            logger.error(f"Shopify create_discount_code failed: {e}")
            return ShopifyResult(success=False, error=str(e))

    # ── Store Stats ───────────────────────────────────────────────────────────

    async def get_store_info(self) -> ShopifyResult:
        """Get basic store information"""
        if not settings.shopify_enabled:
            return ShopifyResult(success=False, error="Shopify integration not enabled")
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/shop.json",
                    headers=self.headers,
                    timeout=10.0,
                )
            if resp.status_code == 200:
                return ShopifyResult(success=True, data=resp.json().get("shop", {}))
            return ShopifyResult(success=False, error=resp.text)
        except Exception as e:
            logger.error(f"Shopify get_store_info failed: {e}")
            return ShopifyResult(success=False, error=str(e))


# Global instance
shopify = ShopifyIntegration()
