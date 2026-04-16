# Big Homie — Revenue Verticals Install Guide

Three production-ready verticals wired into the existing Big Homie stack:
**Content Factory** | **Rap Video Engine** | **Site Builder**

---

## 1. Files Added (this commit)

| File | Purpose |
|---|---|
| `content_factory.py` | Multi-platform content pack generator (blog, X thread, TikTok, YouTube, IG, LinkedIn, email) |
| `rap_video_engine.py` | Full 5-stage pipeline: lyrics → beat → vocals → video scenes → FFmpeg render |
| `site_builder.py` | HTML scaffold + hero image (ComfyUI) + Cloudflare Pages deploy |
| `gsd_router.py` | GSD context dispatcher — `@rap / @content / @site / @code / @research / @revenue` |
| `env.additions.txt` | New `.env` keys to append (opencode, MiniMax, ElevenLabs, CF R2, Resend, Brave, Stripe) |

---

## 2. Append Environment Variables

```bash
cat env.additions.txt >> .env
# Then fill in API keys in .env
```

---

## 3. Install New Dependencies

```bash
pip install httpx loguru
sudo apt install ffmpeg         # Ubuntu/Debian
# brew install ffmpeg           # macOS
# pip install bark-tts          # optional local TTS
```

---

## 4. Wire GSD Router into heartbeat.py

```python
# heartbeat.py — add import at top
from gsd_router import process_gsd_queue

# Inside the heartbeat execution block, after health checks:
from database_ops import get_pending_gsd_tasks   # or your queue method
queue = get_pending_gsd_tasks()
if queue:
    results = await process_gsd_queue(queue)
    logger.info(f"[Heartbeat] GSD processed {len(results)} tasks")
```

---

## 5. Wire GSD Router into cognitive_core.py

```python
# cognitive_core.py — add import
from gsd_router import gsd_router

# In your task execution method:
result = await gsd_router.dispatch(task_text, brief_dict=brief)
```

---

## 6. Register MCP Tools in mcp_integration.py

Add inside `_register_default_tools()`:

```python
# Content Factory
self.register_tool(ToolDefinition(
    name="content_generate_pack",
    type=ToolType.API,
    description="Generate multi-platform content package",
    parameters={
        "topic":       {"type": "string"},
        "brand_voice": {"type": "string"},
        "tone":        {"type": "string", "enum": ["hype","professional","conversational"]},
        "platforms":   {"type": "array", "items": {"type": "string"}},
        "keywords":    {"type": "array", "items": {"type": "string"}},
    },
    handler=self._handle_content_pack,
    requires_confirmation=False,
))

# Rap Video Engine
self.register_tool(ToolDefinition(
    name="rap_video_generate",
    type=ToolType.API,
    description="Generate a complete rap video: lyrics, beat, vocals, scenes, rendered MP4",
    parameters={
        "theme":          {"type": "string"},
        "style":          {"type": "string", "enum": ["trap","boom_bap","drill","lo_fi","phonk"]},
        "bars":           {"type": "integer", "default": 16},
        "artist_name":    {"type": "string"},
        "include_vocals": {"type": "boolean", "default": True},
    },
    handler=self._handle_rap_video,
    requires_confirmation=True,
))

# Site Builder
self.register_tool(ToolDefinition(
    name="site_build_deploy",
    type=ToolType.CLOUD,
    description="Build and deploy a full business website to Cloudflare Pages",
    parameters={
        "business_name":  {"type": "string"},
        "niche":          {"type": "string"},
        "tone":           {"type": "string"},
        "pages":          {"type": "array"},
        "primary_color":  {"type": "string"},
        "tagline":        {"type": "string"},
        "description":    {"type": "string"},
        "features":       {"type": "array"},
        "cta_text":       {"type": "string"},
    },
    handler=self._handle_site_build,
    requires_confirmation=True,
))
```

Add handler methods to the `MCPIntegration` class:

```python
async def _handle_content_pack(self, args: Dict) -> ToolResult:
    from content_factory import content_factory, ContentTone, Platform
    platforms = [Platform(p) for p in args.get("platforms", ["blog","x_thread","tiktok"])]
    tone = ContentTone(args.get("tone", "conversational"))
    job = await content_factory.create_content_package(
        topic=args["topic"],
        brand_voice=args.get("brand_voice", "authentic"),
        tone=tone, platforms=platforms,
        keywords=args.get("keywords", []),
    )
    return ToolResult(success=True, data={"job_id": job.id, "outputs": job.outputs})

async def _handle_rap_video(self, args: Dict) -> ToolResult:
    from rap_video_engine import rap_video_engine
    job = await rap_video_engine.generate_rap_video(**args)
    return ToolResult(success=job.status == "completed",
                      data={"job_id": job.id, "output_path": job.output_path},
                      error=job.error)

async def _handle_site_build(self, args: Dict) -> ToolResult:
    from site_builder import site_builder, SiteBuilder
    brief = SiteBuilder.brief_from_dict(args)
    job = await site_builder.build_site(brief)
    return ToolResult(success=job.status == "completed",
                      data={"job_id": job.id, "deploy_url": job.deploy_url,
                            "html_path": job.html_path},
                      error=job.error)
```

---

## 7. Smoke Test

```bash
# Test content factory
python content_factory.py "AI is changing how musicians create beats"

# Test GSD router
python gsd_router.py "@content write a tiktok about hustle and AI"
python gsd_router.py "@rap make a trap video about building an empire"
python gsd_router.py "@site build a site for Big Homie Studios music production"
```

---

## 8. Monetization Activation

1. Create Stripe products at dashboard.stripe.com:
   - Content Pack: $29/mo recurring
   - Rap Video: $49 one-time
   - Site Build: $29 one-time / $99/mo managed

2. Add Price IDs to `.env`:
   ```
   STRIPE_CONTENT_PACK_PRICE_ID=price_xxx
   STRIPE_RAP_VIDEO_PRICE_ID=price_xxx
   STRIPE_SITE_BUILD_PRICE_ID=price_xxx
   ```

3. After each job, call the billing hook:
   ```python
   await content_factory.bill_pack(job, price_usd=29.0)
   await rap_video_engine.bill_video(job, price_usd=49.0)
   await site_builder.bill_site(job, price_usd=29.0)
   ```

---

## GSD Context Map

| Prefix | Routes To | Revenue Stream |
|---|---|---|
| `@rap` | `rap_video_engine` | MaaS — $49/video |
| `@content` | `content_factory` | SaaS — $29/mo pack |
| `@site` | `site_builder` | SaaS — $29 build / $99/mo |
| `@code` | `sub_agents` (opencode) | Internal |
| `@research` | `sub_agents` parallel | Internal |
| `@revenue` | `revenue_engine` report | Reporting |
| *(no prefix)* | `sub_agents` general | Internal |

---

## Output Directories

| Vertical | Output Location |
|---|---|
| Content packs | `~/.big_homie/content_outputs/` |
| Rap videos | `~/.big_homie/rap_video_outputs/` |
| Site HTML files | `~/.big_homie/site_outputs/` |
| Temp render files | `~/.big_homie/rap_video_temp/` |
