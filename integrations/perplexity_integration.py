"""
Perplexity AI Integration
Provides advanced AI search and research capabilities with citations
"""

from dataclasses import dataclass
from typing import Any, Optional

import httpx
from loguru import logger

from config import settings


@dataclass
class PerplexityResult:
    """Result of a Perplexity operation"""

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class PerplexityIntegration:
    """
    Perplexity AI API integration

    Capabilities:
    - Research queries with citations
    - Multi-step reasoning searches
    - Real-time data retrieval
    - Domain-specific searches
    """

    def __init__(self):
        self.base_url = "https://api.perplexity.ai"
        self.headers = {}
        if settings.perplexity_api_key:
            self.headers = {
                "Authorization": f"Bearer {settings.perplexity_api_key}",
                "Content-Type": "application/json",
            }

    async def health_check(self) -> bool:
        """Check if Perplexity API is accessible"""
        if not settings.perplexity_enabled or not settings.perplexity_api_key:
            return False
        # Perplexity doesn't have a dedicated health check endpoint
        # Return True if configured
        return True

    async def search(
        self,
        query: str,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> PerplexityResult:
        """
        Perform a search query with Perplexity AI

        Args:
            query: The search query
            model: Model to use (default from settings)
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
        """
        if not settings.perplexity_enabled:
            return PerplexityResult(success=False, error="Perplexity integration not enabled")

        try:
            url = f"{self.base_url}/chat/completions"

            payload = {
                "model": model or settings.perplexity_model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful research assistant. Provide accurate, well-cited information.",
                    },
                    {"role": "user", "content": query},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "return_citations": True,
                "return_images": False,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=payload, timeout=60.0)

                if response.status_code == 200:
                    data = response.json()
                    return PerplexityResult(success=True, data=data)
                else:
                    return PerplexityResult(success=False, error=f"Search failed: {response.text}")
        except Exception as e:
            logger.error(f"Perplexity search failed: {e}")
            return PerplexityResult(success=False, error=str(e))

    async def research(
        self, topic: str, focus_areas: Optional[list[str]] = None
    ) -> PerplexityResult:
        """
        Perform comprehensive research on a topic

        Args:
            topic: The research topic
            focus_areas: Specific areas to focus on
        """
        if not settings.perplexity_enabled:
            return PerplexityResult(success=False, error="Perplexity integration not enabled")

        query = f"Provide a comprehensive research summary on: {topic}"
        if focus_areas:
            query += f"\n\nFocus on these specific areas: {', '.join(focus_areas)}"

        return await self.search(query, max_tokens=8192)


# Global instance
perplexity = PerplexityIntegration()
