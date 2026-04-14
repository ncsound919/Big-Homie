"""site_builder.py — Big Homie Website Builder Vertical
Pipeline: brief -> scaffold HTML -> hero image -> deploy to Cloudflare Pages
Revenue stream: RevenueStream.SAAS  ($29 build / $99/mo managed)
"""
from __future__ import annotations
import asyncio, json, uuid, os, re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from loguru import logger


@dataclass
class SiteBrief:
    business_name: str
    niche: str
    pages: List[str]
    primary_color: str
    secondary_color: str
    tone: str
    cta_text: str
    cta_link: str
    tagline: str
    description: str
    features: List[str]


@dataclass
class SiteBuildJob:
    id: str
    brief: SiteBrief
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"
    html_path: Optional[str] = None
    deploy_url: Optional[str] = None
    thumbnail_prompt: Optional[str] = None
    hero_image_path: Optional[str] = None
    cost_usd: float = 0.0
    error: Optional[str] = None
    stages_completed: List[str] = field(default_factory=list)


class SiteBuilder:
    OUTPUT_DIR = Path.home() / ".big_homie" / "site_outputs"

    def __init__(self):
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    async def _llm(self, prompt: str, tier: str = "complex") -> str:
        try:
            from llm_gateway import llm, TaskType
            tier_map = {"fast": TaskType.SIMPLE, "general": TaskType.GENERAL, "complex": TaskType.COMPLEX}
            resp = await llm.complete(
                messages=[{"role": "user", "content": prompt}],
                task_type=tier_map.get(tier, TaskType.COMPLEX),
            )
            return resp.content if hasattr(resp, "content") else str(resp)
        except ImportError:
            await asyncio.sleep(0.05)
            return f"<!-- STUB HTML for: {prompt[:80]} -->"

    async def _scaffold_site(self, brief: SiteBrief) -> str:
        pages_list = "\n".join(f"- {p.capitalize()}" for p in brief.pages)
        features   = "\n".join(f"- {f}" for f in brief.features)
        prompt = f"""You are an expert web developer. Build a complete, production-ready single-file HTML website.

BUSINESS: {brief.business_name}
NICHE: {brief.niche}
TAGLINE: {brief.tagline}
DESCRIPTION: {brief.description}
TONE: {brief.tone}
PRIMARY COLOR: {brief.primary_color}
SECONDARY COLOR: {brief.secondary_color}
CTA TEXT: {brief.cta_text}
CTA LINK: {brief.cta_link}

PAGES TO INCLUDE (as scroll sections):
{pages_list}

KEY FEATURES / SERVICES:
{features}

TECHNICAL REQUIREMENTS:
1. Single HTML file with all CSS and JS inline
2. Mobile-first responsive design (375px and 1440px)
3. Dark/light mode toggle with sun/moon icon in header
4. Smooth scroll navigation with active state highlighting
5. Hero section with gradient background, tagline, and CTA button
6. Services/features section with icon cards (inline SVG icons)
7. About section with description
8. Contact section with working mailto form
9. Footer with business name and copyright
10. CSS custom properties for colors, spacing, typography
11. Use Satoshi font via Fontshare CDN or Inter via Google Fonts
12. Subtle scroll animations using Intersection Observer
13. Professional, non-AI-looking design
14. WCAG AA contrast compliance
15. NO external image URLs — use CSS gradients and SVG only

DESIGN RULES:
- Left-align body text (never center everything)
- Use --primary-color for CTAs only, not backgrounds
- Cards use box-shadow for elevation, not colored side borders
- 4px spacing system via CSS variables
- Fluid typography with clamp()

After the HTML, write:
THUMBNAIL_PROMPT: [detailed image prompt for a website mockup preview]

OUTPUT ONLY the HTML (<!DOCTYPE html> ... </html>) then the THUMBNAIL_PROMPT line:"""
        return await self._llm(prompt, "complex")

    def _extract_html(self, raw: str) -> tuple[str, Optional[str]]:
        thumb = None
        if "THUMBNAIL_PROMPT:" in raw:
            parts = raw.split("THUMBNAIL_PROMPT:", 1)
            raw   = parts[0].strip()
            thumb = parts[1].strip()
        if "<!DOCTYPE" in raw:
            start = raw.index("<!DOCTYPE")
            if "</html>" in raw:
                end = raw.rindex("</html>") + len("</html>")
                raw = raw[start:end]
        return raw.strip(), thumb

    async def _gen_hero_image(self, thumb_prompt: str) -> Optional[str]:
        if not thumb_prompt:
            return None
        try:
            from media_generation import media_manager, MediaType
            result = await media_manager.generate_media(
                media_type=MediaType.IMAGE,
                prompt=thumb_prompt,
                provider="comfyui",
                width=1200, height=630,
            )
            if result.success:
                return result.file_path
        except ImportError:
            pass
        return None

    async def _deploy(self, job_id: str, html_content: str,
                       project_slug: str) -> Optional[str]:
        cf_token   = os.getenv("CLOUDFLARE_API_TOKEN")
        cf_account = os.getenv("CF_ACCOUNT_ID")
        if not cf_token or not cf_account:
            logger.warning("[SiteBuilder] Cloudflare credentials not set — skipping deploy")
            return None
        try:
            from mcp_integration import mcp
            result = await mcp.execute_tool(
                "cloudflare_pages_deploy",
                {"project_name": project_slug, "html_content": html_content, "account_id": cf_account},
                context={"confirmed": True},
            )
            if result.success:
                return result.data.get("url")
        except (ImportError, Exception) as e:
            logger.warning(f"[SiteBuilder] MCP deploy failed: {e}")
        logger.info(
            f"[SiteBuilder] Manual deploy:\n"
            f"  wrangler pages deploy {self.OUTPUT_DIR}/{project_slug}.html "
            f"--project-name {project_slug}"
        )
        return f"file://{self.OUTPUT_DIR}/{project_slug}.html"

    async def build_site(self, brief: SiteBrief) -> SiteBuildJob:
        job  = SiteBuildJob(id=uuid.uuid4().hex[:8], brief=brief, status="running")
        slug = re.sub(r"[^a-z0-9-]", "-", brief.business_name.lower())[:40]
        logger.info(f"[SiteBuilder] Starting job={job.id} biz='{brief.business_name}'")
        try:
            logger.info("[SiteBuilder] Stage 1/4 — scaffolding HTML")
            raw  = await self._scaffold_site(brief)
            html, thumb = self._extract_html(raw)
            job.thumbnail_prompt = thumb
            job.stages_completed.append("scaffold")
            job.cost_usd += 0.01
            html_path = self.OUTPUT_DIR / f"{slug}_{job.id}.html"
            html_path.write_text(html)
            job.html_path = str(html_path)
            job.stages_completed.append("html_saved")
            logger.info(f"[SiteBuilder] HTML saved -> {html_path}")
            if thumb:
                logger.info("[SiteBuilder] Stage 2/4 — generating hero image")
                job.hero_image_path = await self._gen_hero_image(thumb)
                job.cost_usd += 0.02
            job.stages_completed.append("hero_image")
            logger.info("[SiteBuilder] Stage 3/4 — deploying to Cloudflare Pages")
            job.deploy_url = await self._deploy(job.id, html, slug)
            job.stages_completed.append("deploy")
            job.status   = "completed"
            job.cost_usd = round(job.cost_usd, 4)
            self._save(job)
            logger.success(f"[SiteBuilder] job={job.id} done | url={job.deploy_url} | cost=${job.cost_usd:.4f}")
        except Exception as e:
            job.status = "failed"
            job.error  = str(e)
            logger.error(f"[SiteBuilder] job={job.id} FAILED: {e}")
            self._save(job)
        return job

    @staticmethod
    def brief_from_dict(d: Dict) -> SiteBrief:
        return SiteBrief(
            business_name  = d.get("business_name", "My Business"),
            niche          = d.get("niche", "professional services"),
            pages          = d.get("pages", ["home", "about", "services", "contact"]),
            primary_color  = d.get("primary_color", "#01696f"),
            secondary_color= d.get("secondary_color", "#171614"),
            tone           = d.get("tone", "professional"),
            cta_text       = d.get("cta_text", "Get Started"),
            cta_link       = d.get("cta_link", "#contact"),
            tagline        = d.get("tagline", "Built different."),
            description    = d.get("description", "We build solutions that work."),
            features       = d.get("features", ["Fast delivery", "Quality work", "Support"]),
        )

    def _save(self, job: SiteBuildJob) -> Path:
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.OUTPUT_DIR / f"site_job_{ts}_{job.id}.json"
        b    = job.brief
        path.write_text(json.dumps({
            "id": job.id, "created_at": job.created_at,
            "status": job.status,
            "brief": {
                "business_name": b.business_name, "niche": b.niche,
                "pages": b.pages, "tone": b.tone, "tagline": b.tagline,
                "description": b.description, "features": b.features,
                "primary_color": b.primary_color, "cta_text": b.cta_text,
            },
            "html_path": job.html_path,
            "deploy_url": job.deploy_url,
            "hero_image_path": job.hero_image_path,
            "cost_usd": job.cost_usd,
            "error": job.error,
            "stages_completed": job.stages_completed,
        }, indent=2))
        return path

    def list_jobs(self, limit: int = 20) -> List[Dict]:
        files = sorted(self.OUTPUT_DIR.glob("site_job_*.json"), reverse=True)[:limit]
        return [json.loads(f.read_text()) for f in files]

    async def bill_site(self, job: SiteBuildJob, price_usd: float = 29.0):
        try:
            from revenue_engine import RevenueEngine, RevenueTask, RevenueStream, RiskLevel
            engine = RevenueEngine()
            task   = RevenueTask(
                id=job.id,
                stream=RevenueStream.SAAS,
                description=f"Website build: {job.brief.business_name}",
                goal_usd=price_usd,
                risk=RiskLevel.LOW,
                status="completed",
                revenue_usd=price_usd,
                cost_usd=job.cost_usd,
            )
            task.completed_at = datetime.now()
            engine.tasks[task.id] = task
            logger.success(f"[SiteBuilder] billed ${price_usd:.2f} for job {job.id}")
        except ImportError:
            pass


site_builder = SiteBuilder()


async def handle_site_request(task_text: str, brief_dict: Optional[Dict] = None) -> Dict:
    """Called by gsd_router when context is @site."""
    if brief_dict:
        brief = SiteBuilder.brief_from_dict(brief_dict)
    else:
        brief = SiteBuilder.brief_from_dict({
            "business_name": task_text[:40],
            "niche": task_text,
            "tagline": f"The best {task_text} you'll find.",
            "description": f"We specialise in {task_text}.",
            "features": ["Quality", "Speed", "Support"],
        })
    job = await site_builder.build_site(brief)
    return {
        "job_id":     job.id,
        "status":     job.status,
        "html_path":  job.html_path,
        "deploy_url": job.deploy_url,
        "cost_usd":   job.cost_usd,
    }


if __name__ == "__main__":
    async def _run():
        brief = SiteBuilder.brief_from_dict({
            "business_name":   "Big Homie Studios",
            "niche":           "AI-powered music and content production",
            "pages":           ["home", "services", "portfolio", "pricing", "contact"],
            "primary_color":   "#01696f",
            "secondary_color": "#171614",
            "tone":            "bold",
            "cta_text":        "Start Creating",
            "cta_link":        "#contact",
            "tagline":         "AI-powered. Street approved.",
            "description":     "Big Homie Studios uses AI to produce rap videos, content packs, and custom websites — fast, affordable, built different.",
            "features": [
                "Rap Video Generation",
                "Weekly Content Packs",
                "AI Website Builder",
                "Beat Production",
                "Social Media Automation",
            ],
        })
        print(f"\n Building site for: '{brief.business_name}'\n")
        job = await site_builder.build_site(brief)
        print(f"Job {job.id} | status={job.status} | cost=${job.cost_usd:.4f}")
        print(f"HTML  -> {job.html_path}")
        print(f"URL   -> {job.deploy_url or 'not deployed (set CF credentials)'}")
    asyncio.run(_run())
