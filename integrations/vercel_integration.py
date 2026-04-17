"""
Vercel Integration
Provides tools for managing Vercel deployments and projects
"""

from dataclasses import dataclass
from typing import Any, Optional

import httpx
from loguru import logger

from config import settings


@dataclass
class VercelResult:
    """Result of a Vercel operation"""

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class VercelIntegration:
    """
    Vercel API integration

    Capabilities:
    - Project deployments
    - Environment variables management
    - Domain configuration
    - Deployment logs
    - Analytics
    """

    def __init__(self):
        self.base_url = "https://api.vercel.com"
        self.headers = {}
        if settings.vercel_api_token:
            self.headers = {
                "Authorization": f"Bearer {settings.vercel_api_token}",
                "Content-Type": "application/json",
            }

    async def health_check(self) -> bool:
        """Check if Vercel API is accessible"""
        if not settings.vercel_enabled or not settings.vercel_api_token:
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/v2/user", headers=self.headers, timeout=10.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Vercel health check failed: {e}")
            return False

    async def create_deployment(
        self, project_name: str, files: dict[str, str], env_vars: Optional[dict[str, str]] = None
    ) -> VercelResult:
        """Create a new deployment"""
        if not settings.vercel_enabled:
            return VercelResult(success=False, error="Vercel integration not enabled")
        if not settings.vercel_api_token:
            return VercelResult(success=False, error="VERCEL_API_TOKEN not configured")

        try:
            url = f"{self.base_url}/v13/deployments"

            # Prepare files for deployment
            deployment_files = []
            for file_path, content in files.items():
                deployment_files.append({"file": file_path, "data": content})

            payload = {
                "name": project_name,
                "files": deployment_files,
                "projectSettings": {"framework": None},
            }

            if env_vars:
                payload["env"] = env_vars

            if settings.vercel_team_id:
                payload["teamId"] = settings.vercel_team_id

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=payload, timeout=60.0)

                if response.status_code in [200, 201]:
                    data = response.json()
                    return VercelResult(success=True, data=data)
                else:
                    return VercelResult(success=False, error=f"Deployment failed: {response.text}")
        except Exception as e:
            logger.error(f"Vercel deployment failed: {e}")
            return VercelResult(success=False, error=str(e))

    async def get_deployment(self, deployment_id: str) -> VercelResult:
        """Get deployment details"""
        if not settings.vercel_enabled:
            return VercelResult(success=False, error="Vercel integration not enabled")
        if not settings.vercel_api_token:
            return VercelResult(success=False, error="VERCEL_API_TOKEN not configured")

        try:
            url = f"{self.base_url}/v13/deployments/{deployment_id}"
            params = {}
            if settings.vercel_team_id:
                params["teamId"] = settings.vercel_team_id

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params, timeout=10.0)

                if response.status_code == 200:
                    return VercelResult(success=True, data=response.json())
                else:
                    return VercelResult(
                        success=False, error=f"Failed to get deployment: {response.text}"
                    )
        except Exception as e:
            logger.error(f"Get deployment failed: {e}")
            return VercelResult(success=False, error=str(e))

    async def list_deployments(
        self, project_id: Optional[str] = None, limit: int = 20
    ) -> VercelResult:
        """List deployments"""
        if not settings.vercel_enabled:
            return VercelResult(success=False, error="Vercel integration not enabled")
        if not settings.vercel_api_token:
            return VercelResult(success=False, error="VERCEL_API_TOKEN not configured")

        try:
            url = f"{self.base_url}/v6/deployments"
            params = {"limit": limit}

            if settings.vercel_team_id:
                params["teamId"] = settings.vercel_team_id

            if project_id:
                params["projectId"] = project_id
            elif settings.vercel_project_id:
                params["projectId"] = settings.vercel_project_id

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params, timeout=10.0)

                if response.status_code == 200:
                    data = response.json()
                    return VercelResult(success=True, data=data.get("deployments", []))
                else:
                    return VercelResult(
                        success=False, error=f"Failed to list deployments: {response.text}"
                    )
        except Exception as e:
            logger.error(f"List deployments failed: {e}")
            return VercelResult(success=False, error=str(e))

    async def get_deployment_logs(self, deployment_id: str) -> VercelResult:
        """Get deployment logs"""
        if not settings.vercel_enabled:
            return VercelResult(success=False, error="Vercel integration not enabled")
        if not settings.vercel_api_token:
            return VercelResult(success=False, error="VERCEL_API_TOKEN not configured")

        try:
            url = f"{self.base_url}/v2/deployments/{deployment_id}/events"
            params = {}
            if settings.vercel_team_id:
                params["teamId"] = settings.vercel_team_id

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params, timeout=10.0)

                if response.status_code == 200:
                    return VercelResult(success=True, data=response.text)
                else:
                    return VercelResult(success=False, error=f"Failed to get logs: {response.text}")
        except Exception as e:
            logger.error(f"Get deployment logs failed: {e}")
            return VercelResult(success=False, error=str(e))

    async def set_env_variable(
        self, project_id: str, key: str, value: str, target: list[str] = None
    ) -> VercelResult:
        """Set an environment variable"""
        if not settings.vercel_enabled:
            return VercelResult(success=False, error="Vercel integration not enabled")
        if not settings.vercel_api_token:
            return VercelResult(success=False, error="VERCEL_API_TOKEN not configured")

        try:
            url = f"{self.base_url}/v9/projects/{project_id}/env"
            params = {}
            if settings.vercel_team_id:
                params["teamId"] = settings.vercel_team_id

            payload = {
                "key": key,
                "value": value,
                "type": "encrypted",
                "target": target or ["production", "preview", "development"],
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, headers=self.headers, params=params, json=payload, timeout=10.0
                )

                if response.status_code in [200, 201]:
                    return VercelResult(success=True, data=response.json())
                else:
                    return VercelResult(
                        success=False, error=f"Failed to set env variable: {response.text}"
                    )
        except Exception as e:
            logger.error(f"Set env variable failed: {e}")
            return VercelResult(success=False, error=str(e))

    async def list_projects(self) -> VercelResult:
        """List all projects"""
        if not settings.vercel_enabled:
            return VercelResult(success=False, error="Vercel integration not enabled")
        if not settings.vercel_api_token:
            return VercelResult(success=False, error="VERCEL_API_TOKEN not configured")

        try:
            url = f"{self.base_url}/v9/projects"
            params = {}
            if settings.vercel_team_id:
                params["teamId"] = settings.vercel_team_id

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params, timeout=10.0)

                if response.status_code == 200:
                    data = response.json()
                    return VercelResult(success=True, data=data.get("projects", []))
                else:
                    return VercelResult(
                        success=False, error=f"Failed to list projects: {response.text}"
                    )
        except Exception as e:
            logger.error(f"List projects failed: {e}")
            return VercelResult(success=False, error=str(e))


# Global instance
vercel = VercelIntegration()
