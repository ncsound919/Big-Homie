"""
Cloudflare Integration
Provides tools for managing Cloudflare services: Workers, KV, R2, DNS, and more
"""

import json
from dataclasses import dataclass
from typing import Any, Optional

import httpx
from loguru import logger

from config import settings


@dataclass
class CloudflareResult:
    """Result of a Cloudflare operation"""

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class CloudflareIntegration:
    """
    Cloudflare API integration

    Capabilities:
    - Workers deployment and management
    - KV namespace operations
    - R2 bucket operations
    - DNS record management
    - Zone analytics
    - Cache purging
    """

    def __init__(self):
        self.base_url = "https://api.cloudflare.com/client/v4"
        self.headers = {}
        if settings.cloudflare_api_token:
            self.headers = {
                "Authorization": f"Bearer {settings.cloudflare_api_token}",
                "Content-Type": "application/json",
            }

    async def health_check(self) -> bool:
        """Check if Cloudflare API is accessible"""
        if not settings.cloudflare_enabled or not settings.cloudflare_api_token:
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/user/tokens/verify", headers=self.headers, timeout=10.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Cloudflare health check failed: {e}")
            return False

    def _auth_headers(self) -> dict[str, str]:
        """Return headers with only the Authorization token (no Content-Type)."""
        if settings.cloudflare_api_token:
            return {"Authorization": f"Bearer {settings.cloudflare_api_token}"}
        return {}

    def _validate_account(self) -> Optional[CloudflareResult]:
        """Return an error result if account-level config is missing."""
        if not settings.cloudflare_enabled:
            return CloudflareResult(success=False, error="Cloudflare integration not enabled")
        if not settings.cloudflare_api_token:
            return CloudflareResult(success=False, error="CLOUDFLARE_API_TOKEN not configured")
        if not settings.cloudflare_account_id:
            return CloudflareResult(success=False, error="CLOUDFLARE_ACCOUNT_ID not configured")
        return None

    def _validate_zone(self) -> Optional[CloudflareResult]:
        """Return an error result if zone-level config is missing."""
        err = self._validate_account()
        if err:
            return err
        if not settings.cloudflare_zone_id:
            return CloudflareResult(success=False, error="CLOUDFLARE_ZONE_ID not configured")
        return None

    # Workers Management
    async def deploy_worker(
        self, script_name: str, script_content: str, bindings: Optional[list[dict]] = None
    ) -> CloudflareResult:
        """Deploy a Cloudflare Worker"""
        err = self._validate_account()
        if err:
            return err

        try:
            acct = settings.cloudflare_account_id
            url = (
                f"{self.base_url}/accounts/{acct}"
                f"/workers/scripts/{script_name}"
            )

            # Prepare metadata for the multipart upload
            metadata = {"body_part": "script", "bindings": bindings or []}

            # Use auth-only headers so httpx can set the correct multipart boundary
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    url,
                    headers=self._auth_headers(),
                    files={
                        "metadata": ("metadata.json", json.dumps(metadata), "application/json"),
                        "script": (script_name, script_content, "application/javascript"),
                    },
                    timeout=30.0,
                )

                if response.status_code in [200, 201]:
                    return CloudflareResult(success=True, data=response.json())
                else:
                    return CloudflareResult(
                        success=False, error=f"Deployment failed: {response.text}"
                    )
        except Exception as e:
            logger.error(f"Worker deployment failed: {e}")
            return CloudflareResult(success=False, error=str(e))

    async def list_workers(self) -> CloudflareResult:
        """List all Workers in the account"""
        err = self._validate_account()
        if err:
            return err

        try:
            url = f"{self.base_url}/accounts/{settings.cloudflare_account_id}/workers/scripts"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, timeout=10.0)

                if response.status_code == 200:
                    data = response.json()
                    return CloudflareResult(success=True, data=data.get("result", []))
                else:
                    return CloudflareResult(
                        success=False, error=f"Failed to list workers: {response.text}"
                    )
        except Exception as e:
            logger.error(f"List workers failed: {e}")
            return CloudflareResult(success=False, error=str(e))

    async def delete_worker(self, script_name: str) -> CloudflareResult:
        """Delete a Worker"""
        err = self._validate_account()
        if err:
            return err

        try:
            acct = settings.cloudflare_account_id
            url = (
                f"{self.base_url}/accounts/{acct}"
                f"/workers/scripts/{script_name}"
            )

            async with httpx.AsyncClient() as client:
                response = await client.delete(url, headers=self.headers, timeout=10.0)

                if response.status_code == 200:
                    return CloudflareResult(success=True, data={"deleted": script_name})
                else:
                    return CloudflareResult(
                        success=False, error=f"Deletion failed: {response.text}"
                    )
        except Exception as e:
            logger.error(f"Worker deletion failed: {e}")
            return CloudflareResult(success=False, error=str(e))

    # KV Namespace Operations
    async def kv_write(self, namespace_id: str, key: str, value: str) -> CloudflareResult:
        """Write a key-value pair to KV storage"""
        err = self._validate_account()
        if err:
            return err

        try:
            acct = settings.cloudflare_account_id
            url = (
                f"{self.base_url}/accounts/{acct}"
                f"/storage/kv/namespaces/{namespace_id}"
                f"/values/{key}"
            )

            async with httpx.AsyncClient() as client:
                response = await client.put(url, headers=self.headers, content=value, timeout=10.0)

                if response.status_code == 200:
                    return CloudflareResult(success=True, data={"key": key})
                else:
                    return CloudflareResult(
                        success=False, error=f"KV write failed: {response.text}"
                    )
        except Exception as e:
            logger.error(f"KV write failed: {e}")
            return CloudflareResult(success=False, error=str(e))

    async def kv_read(self, namespace_id: str, key: str) -> CloudflareResult:
        """Read a value from KV storage"""
        err = self._validate_account()
        if err:
            return err

        try:
            acct = settings.cloudflare_account_id
            url = (
                f"{self.base_url}/accounts/{acct}"
                f"/storage/kv/namespaces/{namespace_id}"
                f"/values/{key}"
            )

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, timeout=10.0)

                if response.status_code == 200:
                    return CloudflareResult(success=True, data=response.text)
                elif response.status_code == 404:
                    return CloudflareResult(success=False, error="Key not found")
                else:
                    return CloudflareResult(success=False, error=f"KV read failed: {response.text}")
        except Exception as e:
            logger.error(f"KV read failed: {e}")
            return CloudflareResult(success=False, error=str(e))

    async def kv_delete(self, namespace_id: str, key: str) -> CloudflareResult:
        """Delete a key from KV storage"""
        err = self._validate_account()
        if err:
            return err

        try:
            acct = settings.cloudflare_account_id
            url = (
                f"{self.base_url}/accounts/{acct}"
                f"/storage/kv/namespaces/{namespace_id}"
                f"/values/{key}"
            )

            async with httpx.AsyncClient() as client:
                response = await client.delete(url, headers=self.headers, timeout=10.0)

                if response.status_code == 200:
                    return CloudflareResult(success=True, data={"deleted": key})
                else:
                    return CloudflareResult(
                        success=False, error=f"KV delete failed: {response.text}"
                    )
        except Exception as e:
            logger.error(f"KV delete failed: {e}")
            return CloudflareResult(success=False, error=str(e))

    # DNS Management
    async def create_dns_record(
        self, record_type: str, name: str, content: str, ttl: int = 1, proxied: bool = False
    ) -> CloudflareResult:
        """Create a DNS record"""
        err = self._validate_zone()
        if err:
            return err

        try:
            url = f"{self.base_url}/zones/{settings.cloudflare_zone_id}/dns_records"

            payload = {
                "type": record_type,
                "name": name,
                "content": content,
                "ttl": ttl,
                "proxied": proxied,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=payload, timeout=10.0)

                if response.status_code == 200:
                    return CloudflareResult(success=True, data=response.json().get("result"))
                else:
                    return CloudflareResult(
                        success=False, error=f"DNS record creation failed: {response.text}"
                    )
        except Exception as e:
            logger.error(f"DNS record creation failed: {e}")
            return CloudflareResult(success=False, error=str(e))

    async def list_dns_records(self, record_type: Optional[str] = None) -> CloudflareResult:
        """List DNS records"""
        err = self._validate_zone()
        if err:
            return err

        try:
            url = f"{self.base_url}/zones/{settings.cloudflare_zone_id}/dns_records"
            params = {}
            if record_type:
                params["type"] = record_type

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params, timeout=10.0)

                if response.status_code == 200:
                    data = response.json()
                    return CloudflareResult(success=True, data=data.get("result", []))
                else:
                    return CloudflareResult(
                        success=False, error=f"Failed to list DNS records: {response.text}"
                    )
        except Exception as e:
            logger.error(f"List DNS records failed: {e}")
            return CloudflareResult(success=False, error=str(e))

    async def purge_cache(
        self, purge_everything: bool = False, files: Optional[list[str]] = None
    ) -> CloudflareResult:
        """Purge cache"""
        err = self._validate_zone()
        if err:
            return err

        try:
            url = f"{self.base_url}/zones/{settings.cloudflare_zone_id}/purge_cache"

            if purge_everything:
                payload = {"purge_everything": True}
            elif files:
                payload = {"files": files}
            else:
                return CloudflareResult(
                    success=False, error="Must specify purge_everything or files"
                )

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=payload, timeout=10.0)

                if response.status_code == 200:
                    return CloudflareResult(success=True, data=response.json().get("result"))
                else:
                    return CloudflareResult(
                        success=False, error=f"Cache purge failed: {response.text}"
                    )
        except Exception as e:
            logger.error(f"Cache purge failed: {e}")
            return CloudflareResult(success=False, error=str(e))


# Global instance
cloudflare = CloudflareIntegration()
