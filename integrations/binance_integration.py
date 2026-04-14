"""
Binance Crypto Exchange Integration
Spot trading, account info, market data, and order management
"""
import hashlib
import hmac
import time
import httpx
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from loguru import logger
from config import settings


@dataclass
class BinanceResult:
    """Result of a Binance operation"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class BinanceIntegration:
    """
    Binance REST API integration

    Capabilities:
    - Account info & balances
    - Real-time market prices (ticker)
    - Order book / candlestick data
    - Place / cancel spot orders (requires confirmation)
    - Trade history

    Uses Binance Testnet when binance_testnet=True (default)
    """

    LIVE_BASE = "https://api.binance.com"
    TEST_BASE = "https://testnet.binance.vision"

    def __init__(self):
        self.api_key = settings.binance_api_key
        self.secret = settings.binance_secret_key
        self.base_url = self.TEST_BASE if settings.binance_testnet else self.LIVE_BASE

    def _sign(self, params: Dict) -> str:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return hmac.new(
            self.secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _headers(self) -> Dict:
        return {"X-MBX-APIKEY": self.api_key}

    async def health_check(self) -> bool:
        """Ping Binance API"""
        if not settings.binance_enabled:
            return False
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.base_url}/api/v3/ping", timeout=10.0)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Binance health check failed: {e}")
            return False

    async def get_account(self) -> BinanceResult:
        """Fetch account info and balances"""
        if not settings.binance_enabled:
            return BinanceResult(success=False, error="Binance integration not enabled")
        try:
            params = {"timestamp": int(time.time() * 1000)}
            params["signature"] = self._sign(params)
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/api/v3/account",
                    headers=self._headers(),
                    params=params,
                    timeout=10.0,
                )
            if resp.status_code == 200:
                return BinanceResult(success=True, data=resp.json())
            return BinanceResult(success=False, error=resp.text)
        except Exception as e:
            logger.error(f"Binance get_account failed: {e}")
            return BinanceResult(success=False, error=str(e))

    async def get_price(self, symbol: str) -> BinanceResult:
        """Get latest price for a symbol (e.g. BTCUSDT)"""
        if not settings.binance_enabled:
            return BinanceResult(success=False, error="Binance integration not enabled")
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/api/v3/ticker/price",
                    params={"symbol": symbol.upper()},
                    timeout=10.0,
                )
            if resp.status_code == 200:
                return BinanceResult(success=True, data=resp.json())
            return BinanceResult(success=False, error=resp.text)
        except Exception as e:
            logger.error(f"Binance get_price failed: {e}")
            return BinanceResult(success=False, error=str(e))

    async def get_all_prices(self) -> BinanceResult:
        """Get latest prices for all symbols"""
        if not settings.binance_enabled:
            return BinanceResult(success=False, error="Binance integration not enabled")
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/api/v3/ticker/price", timeout=15.0
                )
            if resp.status_code == 200:
                return BinanceResult(success=True, data=resp.json())
            return BinanceResult(success=False, error=resp.text)
        except Exception as e:
            logger.error(f"Binance get_all_prices failed: {e}")
            return BinanceResult(success=False, error=str(e))

    async def get_klines(
        self,
        symbol: str,
        interval: str = "1h",
        limit: int = 100,
    ) -> BinanceResult:
        """
        Fetch OHLCV candlestick data.

        Args:
            symbol:   e.g. "BTCUSDT"
            interval: 1m, 5m, 15m, 1h, 4h, 1d, etc.
            limit:    Number of candles (max 1000)
        """
        if not settings.binance_enabled:
            return BinanceResult(success=False, error="Binance integration not enabled")
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/api/v3/klines",
                    params={"symbol": symbol.upper(), "interval": interval, "limit": limit},
                    timeout=15.0,
                )
            if resp.status_code == 200:
                return BinanceResult(success=True, data=resp.json())
            return BinanceResult(success=False, error=resp.text)
        except Exception as e:
            logger.error(f"Binance get_klines failed: {e}")
            return BinanceResult(success=False, error=str(e))

    async def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
    ) -> BinanceResult:
        """
        Place a spot order (requires explicit confirmation before calling).

        Args:
            symbol:     e.g. "BTCUSDT"
            side:       "BUY" or "SELL"
            order_type: "MARKET" or "LIMIT"
            quantity:   Amount of base asset
            price:      Required for LIMIT orders
        """
        if not settings.binance_enabled:
            return BinanceResult(success=False, error="Binance integration not enabled")
        try:
            params: Dict[str, Any] = {
                "symbol": symbol.upper(),
                "side": side.upper(),
                "type": order_type.upper(),
                "quantity": quantity,
                "timestamp": int(time.time() * 1000),
            }
            if order_type.upper() == "LIMIT":
                if price is None:
                    return BinanceResult(success=False, error="price required for LIMIT order")
                params["price"] = price
                params["timeInForce"] = "GTC"
            params["signature"] = self._sign(params)
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/api/v3/order",
                    headers=self._headers(),
                    params=params,
                    timeout=15.0,
                )
            data = resp.json()
            if resp.status_code in (200, 201):
                logger.info(f"Binance order placed: {data.get('orderId')} {side} {quantity} {symbol}")
                return BinanceResult(success=True, data=data)
            return BinanceResult(success=False, error=str(data))
        except Exception as e:
            logger.error(f"Binance place_order failed: {e}")
            return BinanceResult(success=False, error=str(e))

    async def cancel_order(self, symbol: str, order_id: int) -> BinanceResult:
        """Cancel an open order"""
        if not settings.binance_enabled:
            return BinanceResult(success=False, error="Binance integration not enabled")
        try:
            params = {
                "symbol": symbol.upper(),
                "orderId": order_id,
                "timestamp": int(time.time() * 1000),
            }
            params["signature"] = self._sign(params)
            async with httpx.AsyncClient() as client:
                resp = await client.delete(
                    f"{self.base_url}/api/v3/order",
                    headers=self._headers(),
                    params=params,
                    timeout=10.0,
                )
            if resp.status_code == 200:
                return BinanceResult(success=True, data=resp.json())
            return BinanceResult(success=False, error=resp.text)
        except Exception as e:
            logger.error(f"Binance cancel_order failed: {e}")
            return BinanceResult(success=False, error=str(e))

    async def get_open_orders(self, symbol: Optional[str] = None) -> BinanceResult:
        """List all open orders (optionally filtered by symbol)"""
        if not settings.binance_enabled:
            return BinanceResult(success=False, error="Binance integration not enabled")
        try:
            params: Dict[str, Any] = {"timestamp": int(time.time() * 1000)}
            if symbol:
                params["symbol"] = symbol.upper()
            params["signature"] = self._sign(params)
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/api/v3/openOrders",
                    headers=self._headers(),
                    params=params,
                    timeout=10.0,
                )
            if resp.status_code == 200:
                return BinanceResult(success=True, data=resp.json())
            return BinanceResult(success=False, error=resp.text)
        except Exception as e:
            logger.error(f"Binance get_open_orders failed: {e}")
            return BinanceResult(success=False, error=str(e))


# Global instance
binance = BinanceIntegration()
