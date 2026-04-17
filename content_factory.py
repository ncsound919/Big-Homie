"""
content_factory.py — Big Homie Vertical: Content Creation Automation SaaS

Produces content packages across platforms in parallel:
  - TikTok/Reels scripts (15–60s hook + body)
  - YouTube scripts + SEO-optimized titles + thumbnail prompts
  - Long-form blog articles (1500–2500 words, SEO)
  - X (Twitter) threads (8–12 tweets)
  - Instagram captions + hashtag sets
  - LinkedIn thought-leadership posts

All jobs are queued via GSD inbox (SQLite), processed autonomously by heartbeat,
and delivered via Resend email or returned directly.

Usage:
  from content_factory import ContentFactory
  factory = ContentFactory()
  package = await factory.create_package(
      topic="AI changing the music industry",
      brand_voice="bold, entrepreneurial, street-smart",
      platforms=["tiktok", "youtube", "blog", "x_thread"]
  )
"""

import asyncio
import logging
import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Platform Specs ───────────────────────────────────────────────────────────

PLATFORM_SPECS = {
    "tiktok": {
        "name": "TikTok / Reels",
        "format": "30-60 second hook-driven script with pattern interrupt opening",
        "word_count": "80-150 words",
        "model_tier": "fast",
        "output_keys": ["hook", "body", "cta", "hashtags"],
    },
    "youtube": {
        "name": "YouTube",
        "format": "8-12 minute video script with intro hook, 3 key points, outro CTA",
        "word_count": "1200-2000 words",
        "model_tier": "general",
        "output_keys": ["title", "description", "script", "thumbnail_prompt", "tags"],
    },
    "blog": {
        "name": "Blog / Article",
        "format": "SEO-optimized long-form article with H2/H3 structure",
        "word_count": "1500-2500 words",
        "model_tier": "general",
        "output_keys": ["title", "meta_description", "body", "internal_link_suggestions"],
    },
    "x_thread": {
        "name": "X (Twitter) Thread",
        "format": "10-tweet thread, tweet 1 is banger hook, tweets 2-9 are value, tweet 10 is CTA",
        "word_count": "300-500 words total",
        "model_tier": "fast",
        "output_keys": ["tweets", "hook_tweet", "cta_tweet"],
    },
    "instagram": {
        "name": "Instagram",
        "format": "Engaging caption with line breaks, story-style opening, CTA, 15-20 hashtags",
        "word_count": "150-300 words",
        "model_tier": "fast",
        "output_keys": ["caption", "hashtags", "alt_text"],
    },
    "linkedin": {
        "name": "LinkedIn",
        "format": (
            "Thought leadership post, first line hook,"
            " 5-7 short paragraphs,"
            " professional insights"
        ),
        "word_count": "400-800 words",
        "model_tier": "general",
        "output_keys": ["post", "hook_line", "hashtags"],
    },
    "email": {
        "name": "Email Newsletter",
        "format": "Subject line + preview text + HTML-safe email body with CTA button text",
        "word_count": "300-600 words",
        "model_tier": "general",
        "output_keys": ["subject", "preview_text", "body", "cta_text"],
    },
}


@dataclass
class ContentPiece:
    platform: str
    topic: str
    brand_voice: str
    content: dict = field(default_factory=dict)
    thumbnail_path: str = ""
    cost_usd: float = 0.0
    success: bool = False
    error: str = ""


@dataclass
class ContentPackage:
    job_id: str
    topic: str
    brand_voice: str
    pieces: list = field(default_factory=list)
    total_cost_usd: float = 0.0
    success: bool = False
    delivered_via: str = ""  # 'email', 'return', 'webhook'


class ContentFactory:
    """
    Parallel content generation engine.
    Spawns one sub-agent per platform, generates thumbnails via ComfyUI,
    delivers via Resend or returns directly.
    """

    def __init__(self):
        self.resend_enabled = bool(os.getenv("RESEND_API_KEY"))
        self.image_enabled = os.getenv("COMFYUI_ENABLED", "false").lower() == "true"
        self.pexels_key = os.getenv("PEXELS_API_KEY", "")
        self.unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY", "")
        self.output_dir = Path(
            os.getenv("MEDIA_OUTPUT_DIR", "~/.big_homie/media_outputs")
        ).expanduser()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def create_package(
        self,
        topic: str,
        brand_voice: str,
        platforms: Optional[list] = None,
        deliver_to_email: Optional[str] = None,
        generate_thumbnails: bool = True,
        research_first: bool = True,
    ) -> ContentPackage:
        """
        Generate a full content package across platforms in parallel.

        Args:
            topic: Content topic / idea
            brand_voice: Tone descriptor (e.g. "bold, entrepreneurial, street-smart")
            platforms: List of platform keys; defaults to all platforms
            deliver_to_email: If set, sends package via Resend
            generate_thumbnails: Whether to generate thumbnail images for YouTube/blog
            research_first: Whether to run a research pass first for current data

        Returns:
            ContentPackage with all pieces
        """
        if platforms is None:
            platforms = list(PLATFORM_SPECS.keys())

        job_id = str(uuid.uuid4())[:8]
        logger.info(
            f"[ContentFactory:{job_id}] Starting package — topic='{topic}' platforms={platforms}"
        )

        # ── Optional: Research pass ──────────────────────────────────────────
        research_context = ""
        if research_first:
            research_context = await self._research_topic(topic)
            logger.info(
                f"[ContentFactory:{job_id}] Research complete ({len(research_context)} chars)"
            )

        # ── Generate all platforms in parallel ───────────────────────────────
        tasks = [
            self._generate_piece(job_id, topic, brand_voice, platform, research_context)
            for platform in platforms
            if platform in PLATFORM_SPECS
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        pieces = []
        total_cost = 0.0
        for r in results:
            if isinstance(r, Exception):
                logger.warning(f"[ContentFactory:{job_id}] Piece failed: {r}")
                continue
            pieces.append(r)
            total_cost += r.cost_usd

        # ── Generate thumbnails for visual platforms ─────────────────────────
        if generate_thumbnails and self.image_enabled:
            for piece in pieces:
                if piece.platform in ["youtube", "blog", "instagram"] and piece.success:
                    piece.thumbnail_path = await self._generate_thumbnail(job_id, topic, piece)

        package = ContentPackage(
            job_id=job_id,
            topic=topic,
            brand_voice=brand_voice,
            pieces=pieces,
            total_cost_usd=total_cost,
            success=len([p for p in pieces if p.success]) > 0,
        )

        # ── Deliver ──────────────────────────────────────────────────────────
        if deliver_to_email and self.resend_enabled:
            await self._deliver_via_email(package, deliver_to_email)
            package.delivered_via = f"email:{deliver_to_email}"
        else:
            package.delivered_via = "return"

        logger.info(
            f"[ContentFactory:{job_id}] Package complete — "
            f"{len([p for p in pieces if p.success])}/{len(pieces)} pieces, "
            f"${total_cost:.4f}"
        )
        return package

    async def _research_topic(self, topic: str) -> str:
        """Run a research pass on the topic using Brave Search or Perplexity."""
        try:
            import httpx

            brave_key = os.getenv("BRAVE_API_KEY", "")
            if brave_key:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        "https://api.search.brave.com/res/v1/web/search",
                        params={"q": topic, "count": 5},
                        headers={"Accept": "application/json", "X-Subscription-Token": brave_key},
                        timeout=10,
                    )
                    if resp.status_code == 200:
                        results = resp.json().get("web", {}).get("results", [])
                        snippets = [r.get("description", "") for r in results[:5]]
                        return "\n".join(snippets)
        except Exception as e:
            logger.warning(f"Research pass failed: {e}")
        return ""

    async def _generate_piece(
        self, job_id: str, topic: str, brand_voice: str, platform: str, research_context: str
    ) -> ContentPiece:
        """Generate content for a single platform."""
        spec = PLATFORM_SPECS[platform]
        piece = ContentPiece(platform=platform, topic=topic, brand_voice=brand_voice)

        try:
            from llm_gateway import TaskType, llm

            task_type = TaskType.FAST if spec["model_tier"] == "fast" else TaskType.GENERAL

            research_block = (
                f"\n\nRecent context about this topic:\n{research_context}"
                if research_context
                else ""
            )

            prompt = f"""Generate {spec["name"]} content.

Topic: {topic}
Brand Voice: {brand_voice}
Format: {spec["format"]}
Target length: {spec["word_count"]}
Required output keys: {", ".join(spec["output_keys"])}
{research_block}

Return a JSON object with keys: {spec["output_keys"]}.
Write as if you ARE the brand — not describing what they should say.
Be specific, vivid, and authentic. No filler. No generic phrases."""

            response = await llm.complete(
                messages=[{"role": "user", "content": prompt}],
                task_type=task_type,
            )

            # Parse JSON response
            import json
            import re

            raw = response.content if hasattr(response, "content") else str(response)
            # Extract JSON block if wrapped in markdown
            json_match = re.search(r"```(?:json)?\s*({[\s\S]+?})\s*```", raw)
            if json_match:
                raw = json_match.group(1)
            try:
                content_dict = json.loads(raw)
            except json.JSONDecodeError:
                content_dict = {"raw": raw}

            piece.content = content_dict
            piece.cost_usd = getattr(response, "cost_usd", 0.002)
            piece.success = True

        except Exception as e:
            piece.error = str(e)
            piece.success = False
            logger.warning(f"[ContentFactory:{job_id}] {platform} generation failed: {e}")

        return piece

    async def _generate_thumbnail(self, job_id: str, topic: str, piece: ContentPiece) -> str:
        """Generate thumbnail image via ComfyUI."""
        try:
            from media_generation import MediaType, media_manager

            title = piece.content.get("title", topic)
            prompt = (
                piece.content.get("thumbnail_prompt")
                or f"Professional {piece.platform} thumbnail for: {title}. "
                f"Eye-catching, high contrast, bold typography space."
            )

            result = await media_manager.generate_media(
                media_type=MediaType.IMAGE,
                prompt=prompt,
                provider="comfyui",
                width=1280,
                height=720,
            )
            return result.file_path if result.success else ""
        except Exception as e:
            logger.warning(f"[ContentFactory:{job_id}] Thumbnail generation failed: {e}")
            return ""

    async def _deliver_via_email(self, package: ContentPackage, recipient: str):
        """Send the content package via Resend."""
        try:
            import httpx

            # Build HTML summary
            html_parts = [f"<h1>Content Package: {package.topic}</h1>"]
            for piece in package.pieces:
                if piece.success:
                    html_parts.append(f"<h2>{PLATFORM_SPECS[piece.platform]['name']}</h2>")
                    for key, val in piece.content.items():
                        if isinstance(val, list):
                            val = "<br>".join(str(v) for v in val)
                        html_parts.append(f"<p><strong>{key}:</strong> {val}</p>")
                    html_parts.append("<hr>")

            html = "".join(html_parts)

            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {os.getenv('RESEND_API_KEY')}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": os.getenv("RESEND_FROM_EMAIL", "bigHomie@yourdomain.com"),
                        "to": [recipient],
                        "subject": f"[Big Homie] Content Package: {package.topic}",
                        "html": html,
                    },
                    timeout=15,
                )
                if resp.status_code in (200, 201):
                    logger.info(f"Content package delivered to {recipient}")
                else:
                    logger.warning(f"Resend delivery failed: {resp.status_code} {resp.text}")
        except Exception as e:
            logger.warning(f"Email delivery failed: {e}")


# ─── Convenience wrapper ──────────────────────────────────────────────────────

_factory = ContentFactory()


async def create_content_package(
    topic: str,
    brand_voice: str = "bold, authentic, direct",
    platforms: Optional[list] = None,
    deliver_to_email: Optional[str] = None,
) -> ContentPackage:
    """Top-level wrapper for direct import."""
    return await _factory.create_package(
        topic=topic,
        brand_voice=brand_voice,
        platforms=platforms,
        deliver_to_email=deliver_to_email,
    )
