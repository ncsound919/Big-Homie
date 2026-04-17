"""
PrizePicks Integration
Provides fantasy sports data and player prop analysis
NOTE: This integration is for data retrieval only, not for placing entries
"""

from dataclasses import dataclass
from typing import Any, Optional

import httpx
from loguru import logger

from config import settings


@dataclass
class PrizePicksResult:
    """Result of a PrizePicks operation"""

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class PrizePicksIntegration:
    """
    PrizePicks API integration (Read-only)

    Capabilities:
    - Player projections retrieval
    - Contest data fetching
    - Historical performance data
    - Lineup analysis

    NOTE: This integration does NOT support automated entry submissions
    """

    def __init__(self):
        # PrizePicks API (may require authentication for some endpoints)
        self.base_url = "https://api.prizepicks.com"
        self.headers = {"User-Agent": "Big-Homie-Agent/1.0", "Accept": "application/json"}
        if settings.prizepicks_api_key:
            self.headers["Authorization"] = f"Bearer {settings.prizepicks_api_key}"

    async def health_check(self) -> bool:
        """Check if PrizePicks API is accessible"""
        if not settings.prizepicks_enabled:
            return False

        try:
            # Test with a public endpoint
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/projections", headers=self.headers, timeout=10.0
                )
                return response.status_code in [200, 401]  # 401 means API is up but needs auth
        except Exception as e:
            logger.error(f"PrizePicks health check failed: {e}")
            return False

    async def get_projections(
        self, league: Optional[str] = None, per_page: int = 100
    ) -> PrizePicksResult:
        """
        Get player projections

        Args:
            league: Filter by league (e.g., NBA, NFL, MLB)
            per_page: Number of projections per page
        """
        if not settings.prizepicks_enabled:
            return PrizePicksResult(success=False, error="PrizePicks integration not enabled")

        try:
            url = f"{self.base_url}/projections"
            params = {"per_page": per_page}

            if league:
                params["league_id"] = league

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params, timeout=10.0)

                if response.status_code == 200:
                    data = response.json()
                    return PrizePicksResult(success=True, data=data)
                else:
                    return PrizePicksResult(
                        success=False, error=f"Failed to get projections: {response.text}"
                    )
        except Exception as e:
            logger.error(f"Get projections failed: {e}")
            return PrizePicksResult(success=False, error=str(e))

    async def get_players(self, league: Optional[str] = None) -> PrizePicksResult:
        """Get available players"""
        if not settings.prizepicks_enabled:
            return PrizePicksResult(success=False, error="PrizePicks integration not enabled")

        try:
            url = f"{self.base_url}/players"
            params = {}

            if league:
                params["league_id"] = league

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params, timeout=10.0)

                if response.status_code == 200:
                    data = response.json()
                    return PrizePicksResult(success=True, data=data)
                else:
                    return PrizePicksResult(
                        success=False, error=f"Failed to get players: {response.text}"
                    )
        except Exception as e:
            logger.error(f"Get players failed: {e}")
            return PrizePicksResult(success=False, error=str(e))

    async def get_leagues(self) -> PrizePicksResult:
        """Get available leagues"""
        if not settings.prizepicks_enabled:
            return PrizePicksResult(success=False, error="PrizePicks integration not enabled")

        try:
            url = f"{self.base_url}/leagues"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, timeout=10.0)

                if response.status_code == 200:
                    data = response.json()
                    return PrizePicksResult(success=True, data=data)
                else:
                    return PrizePicksResult(
                        success=False, error=f"Failed to get leagues: {response.text}"
                    )
        except Exception as e:
            logger.error(f"Get leagues failed: {e}")
            return PrizePicksResult(success=False, error=str(e))

    async def analyze_projection(self, player_id: str, stat_type: str) -> PrizePicksResult:
        """
        Analyze a specific player projection

        Args:
            player_id: Player ID
            stat_type: Type of stat (e.g., points, rebounds, assists)
        """
        if not settings.prizepicks_enabled:
            return PrizePicksResult(success=False, error="PrizePicks integration not enabled")

        try:
            # Get player's recent projections
            url = f"{self.base_url}/projections"
            params = {"player_id": player_id, "stat_type": stat_type}

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params, timeout=10.0)

                if response.status_code == 200:
                    data = response.json()
                    return PrizePicksResult(success=True, data=data)
                else:
                    return PrizePicksResult(
                        success=False, error=f"Failed to analyze projection: {response.text}"
                    )
        except Exception as e:
            logger.error(f"Analyze projection failed: {e}")
            return PrizePicksResult(success=False, error=str(e))


# Global instance
prizepicks = PrizePicksIntegration()
