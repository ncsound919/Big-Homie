"""content_factory.py — Big Homie Content Factory Vertical
Generates multi-platform content packages from a single topic.
Revenue stream: RevenueStream.SAAS  (subscription content packs)
"""
from __future__ import annotations
import asyncio, json, uuid, os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from loguru import logger


class Platform(str, Enum):
    BLOG         = "blog"
    X_THREAD     = "x_thread"
    TIKTOK       = "tiktok"
    YOUTUBE      = "youtube"
    INSTAGRAM    = "instagram"
    LINKEDIN     = "linkedin"
    EMAIL        = "email"


class ContentTone(str, Enum):
    HYPE           = "hype"
    PROFESSIONAL   = "professional"
    CONVERSATIONAL = "conversational"
    EDUCATIONAL    = "educational"


@dataclass
class ContentJob:
    id: str
    topic: str
    brand_voice: str
    tone: ContentTone
    platforms: List[Platform]
    keywords: List[str]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"
    outputs: Dict[str, str] = field(default_factory=dict)
    cost_usd: float = 0.0
    error: Optional[str] = None


# ── Platform prompt specs ─────────────────────────────────────────────────
PLATFORM_SPECS: Dict[Platform, Dict] = {
    Platform.BLOG: {
        "title": "Blog Post",
        "format": "1,200-1,500 word SEO blog post with H2/H3 headings, intro hook, 5-7 sections, CTA at end.",
        "output_key": "blog_post",
    },
    Platform.X_THREAD: {
        "title": "X (Twitter) Thread",
        "format": "15-tweet thread. Tweet 1 = bold hook. Tweets 2-14 = punchy insights (max 280 chars each). Tweet 15 = CTA + follow ask.",
        "output_key": "x_thread",
    },
    Platform.TIKTOK: {
        "title": "TikTok Script",
        "format": "60-90 second script. Opening hook (0-3s), 5-7 quick tips or story beats, strong ending CTA. Include [VISUAL] stage directions.",
        "output_key": "tiktok_script",
    },
    Platform.YOUTUBE: {
        "title": "YouTube Video Script",
        "format": "8-12 minute script. Intro hook (30s), problem setup, 5-7 main segments with B-roll cues [B-ROLL: ...], outro CTA, subscribe ask.",
        "output_key": "youtube_script",
    },
    Platform.INSTAGRAM: {
        "title": "Instagram Caption",
        "format": "Instagram caption: 3-4 punchy sentences, emotional hook, 2-3 line breaks, 10-15 relevant hashtags at end.",
        "output_key": "instagram_caption",
    },
    Platform.LINKEDIN: {
        "title": "LinkedIn Post",
        "format": "LinkedIn post: first line = scroll-stopping hook, 150-300 words, short paragraphs (1-2 lines), value-driven, subtle CTA.",
        "output_key": "linkedin_post",
    },
    Platform.EMAIL: {
        "title": "Email Newsletter",
        "format": "Email newsletter: subject line + preview text + 300-500 word body with clear sections, one primary CTA button.",
        "output_key": "email_newsletter",
    },
}


class ContentFactory:
    OUTPUT_DIR = Path.home() / ".big_homie" / "content_outputs"

    def __init__(self):
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── LLM helper ─────────────────────────────────────────────────────
    async def _llm(self, prompt: str, tier: str = "general") -> str:
        try:
            from llm_gateway import llm, TaskType
            tier_map = {"fast": TaskType.SIMPLE, "general": TaskType.GENERAL, "complex": TaskType.COMPLEX}
            resp = await llm.complete(
                messages=[{"role": "user", "content": prompt}],
                task_type=tier_map.get(tier, TaskType.GENERAL),
            )
            return resp.content if hasattr(resp, "content") else str(resp)
        except ImportError:
            await asyncio.sleep(0.05)
            return f"[STUB CONTENT for: {prompt[:80]}]"

    # ── Generate one platform ──────────────────────────────────────────
    async def _gen_platform(self, platform: Platform, topic: str,
                             brand_voice: str, tone: ContentTone,
                             keywords: List[str]) -> str:
        spec = PLATFORM_SPECS[platform]
        kw   = ", ".join(keywords) if keywords else "none specified"
        prompt = f"""You are an expert content strategist creating {spec['title']} content.

TOPIC: {topic}
BRAND VOICE: {brand_voice}
TONE: {tone.value}
KEYWORDS TO WEAVE IN: {kw}

FORMAT INSTRUCTIONS:
{spec['format']}

WRITE THE FULL {spec['title'].upper()} NOW. No preamble, no explanation. Start directly with the content:"""

        return await self._llm(prompt, "general")

    # ── Main pipeline ──────────────────────────────────────────────────
    async def create_content_package(
        self,
        topic: str,
        brand_voice: str = "authentic, direct, street-smart",
        tone: ContentTone = ContentTone.CONVERSATIONAL,
        platforms: Optional[List[Platform]] = None,
        keywords: Optional[List[str]] = None,
    ) -> ContentJob:
        """
        Generate content for all requested platforms in parallel.
        Returns a ContentJob with outputs dict keyed by platform output_key.
        """
        if platforms is None:
            platforms = [Platform.BLOG, Platform.X_THREAD, Platform.TIKTOK,
                         Platform.INSTAGRAM, Platform.LINKEDIN]
        if keywords is None:
            keywords = []

        job = ContentJob(
            id=uuid.uuid4().hex[:8],
            topic=topic,
            brand_voice=brand_voice,
            tone=tone,
            platforms=platforms,
            keywords=keywords,
            status="running",
        )
        logger.info(f"[ContentFactory] job={job.id} topic='{topic}' platforms={[p.value for p in platforms]}")

        try:
            tasks = [
                self._gen_platform(p, topic, brand_voice, tone, keywords)
                for p in platforms
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for platform, result in zip(platforms, results):
                key = PLATFORM_SPECS[platform]["output_key"]
                if isinstance(result, Exception):
                    logger.warning(f"[ContentFactory] {platform.value} failed: {result}")
                    job.outputs[key] = f"ERROR: {result}"
                else:
                    job.outputs[key] = result
                    job.cost_usd   += 0.005

            job.status   = "completed"
            job.cost_usd = round(job.cost_usd, 4)
            self._save(job)
            logger.success(f"[ContentFactory] job={job.id} done | {len(job.outputs)} pieces | cost=${job.cost_usd:.4f}")

        except Exception as e:
            job.status = "failed"
            job.error  = str(e)
            logger.error(f"[ContentFactory] job={job.id} FAILED: {e}")
            self._save(job)

        return job

    # ── Persistence ────────────────────────────────────────────────────
    def _save(self, job: ContentJob) -> Path:
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.OUTPUT_DIR / f"content_job_{ts}_{job.id}.json"
        path.write_text(json.dumps({
            "id": job.id, "created_at": job.created_at,
            "status": job.status,
            "topic": job.topic, "brand_voice": job.brand_voice,
            "tone": job.tone.value,
            "platforms": [p.value for p in job.platforms],
            "keywords": job.keywords,
            "outputs": job.outputs,
            "cost_usd": job.cost_usd,
            "error": job.error,
        }, indent=2))
        return path

    def list_jobs(self, limit: int = 20) -> List[Dict]:
        files = sorted(self.OUTPUT_DIR.glob("content_job_*.json"), reverse=True)[:limit]
        return [json.loads(f.read_text()) for f in files]

    # ── Revenue hook ───────────────────────────────────────────────────
    async def bill_pack(self, job: ContentJob, price_usd: float = 29.0):
        try:
            from revenue_engine import RevenueEngine, RevenueTask, RevenueStream, RiskLevel
            engine = RevenueEngine()
            task   = RevenueTask(
                id=job.id,
                stream=RevenueStream.SAAS,
                description=f"Content pack: {job.topic[:60]}",
                goal_usd=price_usd,
                risk=RiskLevel.LOW,
                status="completed",
                revenue_usd=price_usd,
                cost_usd=job.cost_usd,
            )
            task.completed_at = datetime.now()
            engine.tasks[task.id] = task
            logger.success(f"[ContentFactory] billed ${price_usd:.2f} for job {job.id}")
        except ImportError:
            pass


# ── Singleton ─────────────────────────────────────────────────────────────
content_factory = ContentFactory()


# ── GSD router entry point ────────────────────────────────────────────────
async def handle_content_request(task_text: str,
                                  platforms: Optional[List[str]] = None) -> Dict:
    """Called by gsd_router when context is @content."""
    p = [Platform(x) for x in platforms] if platforms else None
    job = await content_factory.create_content_package(
        topic=task_text,
        platforms=p,
    )
    return {
        "job_id":    job.id,
        "status":    job.status,
        "platforms": list(job.outputs.keys()),
        "cost_usd":  job.cost_usd,
    }


# ── Quick test ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    async def _run():
        topic = " ".join(sys.argv[1:]) or "AI is changing how musicians create beats"
        print(f"\n Generating content pack for: '{topic}'\n")
        job = await content_factory.create_content_package(
            topic=topic,
            brand_voice="bold, street-smart, future-focused",
            tone=ContentTone.HYPE,
            platforms=[
                Platform.X_THREAD,
                Platform.TIKTOK,
                Platform.INSTAGRAM,
                Platform.LINKEDIN,
            ],
            keywords=["AI", "music production", "Big Homie", "hustle"],
        )
        print(f"Job {job.id} | status={job.status} | cost=${job.cost_usd:.4f}")
        for key, content in job.outputs.items():
            print(f"\n{'='*60}\n{key.upper()}\n{'='*60}")
            print(content[:500] + "..." if len(content) > 500 else content)
    asyncio.run(_run())
