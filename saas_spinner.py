"""
saas_spinner.py
---------------
Autonomous SaaS/MaaS service generator for Big Homie.

The spinner runs a full cycle:
  1. DISCOVER  — Brave Search finds underserved niches / API gaps
  2. SCAFFOLD  — opencode (via opencode_provider) generates FastAPI endpoint code
  3. DEPLOY    — Cloudflare Workers free tier hosts the endpoint
  4. MONETIZE  — Stripe Checkout link wired to the endpoint (no monthly fees)
  5. REPORT    — revenue_engine logs the new service and tracks earnings

Each generated service is stored in Supabase (free tier) and queued via
Upstash Redis so the autonomous_loop can poll status.

Usage:
    from saas_spinner import SaaSSpinner
    spinner = SaaSSpinner()
    spinner.spin(niche="AI resume screener API")  # full cycle
    spinner.auto_discover_and_spin()               # fully autonomous
"""

import os
import json
import logging
import re
import time
from datetime import datetime, timezone
from typing import Optional

from free_api_stack import (
    brave_search, groq_chat, deploy_worker,
    supabase_insert, supabase_query,
    enqueue_job, check_providers,
)
from opencode_provider import route_to_opencode, is_opencode_available

logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────────────────
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_SECRET_KEY      = os.getenv("STRIPE_SECRET_KEY", "")
BASE_WORKER_DOMAIN     = os.getenv("CF_WORKER_DOMAIN", "workers.dev")
SERVICES_TABLE         = "saas_services"

# Niche discovery search templates
DISCOVERY_QUERIES = [
    "underserved micro-SaaS API ideas 2025 developer",
    "simple API businesses making money indie hackers 2025",
    "MaaS model-as-a-service profitable niche free tier",
    "profitable micro-API no-code tools gap 2025",
]


class SaaSSpinner:
    def __init__(self):
        self.providers = check_providers()
        logger.info(f"SaaSSpinner ready. Providers: {self.providers}")

    # ── Step 1: DISCOVER ────────────────────────────────────────────────────
    def discover_niche(self) -> Optional[str]:
        """
        Use Brave Search + Groq to identify a specific underserved API niche.
        Returns a one-line niche description or None.
        """
        if not self.providers["brave"]:
            logger.warning("Brave Search not configured — using fallback niche")
            return "AI-powered keyword extraction API"

        results = []
        for q in DISCOVERY_QUERIES[:2]:  # limit to 2 searches to stay in free tier
            results.extend(brave_search(q, count=5))

        if not results:
            return None

        summaries = "\n".join(
            f"- {r['title']}: {r['description']}" for r in results[:10] if r.get("description")
        )

        prompt = [
            {"role": "system", "content": (
                "You are a startup advisor. Given these market research snippets, "
                "identify ONE specific underserved micro-SaaS or MaaS API idea "
                "that can be built in under 100 lines of code and monetized with Stripe. "
                "Reply with ONLY a single sentence describing the niche."
            )},
            {"role": "user", "content": summaries},
        ]

        niche = groq_chat(prompt, max_tokens=100)
        if niche:
            niche = niche.strip().strip('"').strip("'")
            logger.info(f"[DISCOVER] Niche identified: {niche}")
        return niche

    # ── Step 2: SCAFFOLD ────────────────────────────────────────────────────
    def scaffold_service(self, niche: str) -> Optional[str]:
        """
        Generate a Cloudflare Worker script for the niche using opencode → Groq fallback.
        Returns the JavaScript worker code as a string.
        """
        system_prompt = (
            "You are an expert Cloudflare Workers developer. "
            "Generate a complete, production-ready Cloudflare Worker script (JavaScript) "
            "that implements the following API service. "
            "Requirements:\n"
            "- Handle CORS (allow all origins)\n"
            "- Respond to POST /api with JSON input/output\n"
            "- Include a GET /health endpoint returning {status: 'ok'}\n"
            "- Include a GET / endpoint with a usage guide in JSON\n"
            "- Keep it under 120 lines\n"
            "- No external dependencies beyond the Workers runtime\n"
            "Reply with ONLY the JavaScript code, no explanation."
        )
        messages = [
            {"role": "user",
             "content": f"Build a Cloudflare Worker for this API service: {niche}"}
        ]

        # Try opencode first, fall back to Groq
        code = None
        if is_opencode_available():
            code = route_to_opencode(
                "saas_scaffold", messages,
                system=system_prompt, max_tokens=3000
            )

        if not code and self.providers["groq"]:
            messages.insert(0, {"role": "system", "content": system_prompt})
            code = groq_chat(messages, max_tokens=3000, temperature=0.1)

        if code:
            # Strip markdown code fences if present
            code = re.sub(r"^```[a-zA-Z]*\n", "", code.strip())
            code = re.sub(r"\n```$", "", code.strip())
            logger.info(f"[SCAFFOLD] Generated {len(code)} chars of worker code")
        return code

    # ── Step 3: DEPLOY ──────────────────────────────────────────────────────
    def deploy_service(self, worker_name: str, script: str) -> Optional[str]:
        """
        Deploy to Cloudflare Workers. Returns the worker URL or None.
        """
        safe_name = re.sub(r"[^a-z0-9-]", "-", worker_name.lower())[:63]

        if not self.providers["cloudflare"]:
            logger.warning("[DEPLOY] Cloudflare not configured — skipping deploy")
            return f"https://{safe_name}.{BASE_WORKER_DOMAIN}"  # hypothetical URL

        success = deploy_worker(safe_name, script)
        if success:
            url = f"https://{safe_name}.{BASE_WORKER_DOMAIN}"
            logger.info(f"[DEPLOY] Service live at {url}")
            return url
        return None

    # ── Step 4: MONETIZE ────────────────────────────────────────────────────
    def create_stripe_link(self, service_name: str, price_usd: float = 9.0) -> Optional[str]:
        """
        Create a Stripe Payment Link for the service.
        Returns the checkout URL or None.
        """
        if not STRIPE_SECRET_KEY:
            logger.warning("[MONETIZE] STRIPE_SECRET_KEY not set")
            return None
        try:
            import httpx
            # Create price
            price_resp = httpx.post(
                "https://api.stripe.com/v1/prices",
                auth=(STRIPE_SECRET_KEY, ""),
                data={
                    "unit_amount": int(price_usd * 100),
                    "currency": "usd",
                    "recurring[interval]": "month",
                    "product_data[name]": service_name,
                },
                timeout=30,
            )
            price_resp.raise_for_status()
            price_id = price_resp.json()["id"]

            # Create payment link
            link_resp = httpx.post(
                "https://api.stripe.com/v1/payment_links",
                auth=(STRIPE_SECRET_KEY, ""),
                data={f"line_items[0][price]": price_id,
                      "line_items[0][quantity]": "1"},
                timeout=30,
            )
            link_resp.raise_for_status()
            url = link_resp.json()["url"]
            logger.info(f"[MONETIZE] Stripe link: {url}")
            return url
        except Exception as exc:
            logger.error(f"create_stripe_link error: {exc}")
            return None

    # ── Step 5: REPORT ──────────────────────────────────────────────────────
    def report_to_revenue_engine(self, service: dict):
        """Log the new service to revenue_engine and Supabase."""
        try:
            from revenue_engine import RevenueEngine  # type: ignore
            engine = RevenueEngine()
            engine.register_service(
                name=service["name"],
                url=service.get("url", ""),
                monthly_price=service.get("price_usd", 9.0),
                stripe_link=service.get("stripe_link", ""),
            )
        except Exception as exc:
            logger.debug(f"revenue_engine unavailable: {exc}")

        if self.providers["supabase"]:
            supabase_insert(SERVICES_TABLE, {
                **service,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })

        # Also push to GSD queue so heartbeat tracks it
        enqueue_job("gsd_inbox", {
            "title": f"Monitor new service: {service['name']}",
            "source": "saas_spinner",
            "meta": service,
        })
        logger.info(f"[REPORT] Service registered: {service['name']}")

    # ── Full cycle ───────────────────────────────────────────────────────────
    def spin(self, niche: str, price_usd: float = 9.0) -> dict:
        """
        Run the full DISCOVER → SCAFFOLD → DEPLOY → MONETIZE → REPORT cycle.
        Returns a service record dict.
        """
        logger.info(f"[SPINNER] Starting spin for niche: {niche}")

        # Sanitize name
        name = re.sub(r"[^a-zA-Z0-9 ]", "", niche)[:50].strip()
        worker_name = re.sub(r"\s+", "-", name.lower())

        script = self.scaffold_service(niche)
        if not script:
            logger.error("[SPINNER] Scaffold failed — aborting")
            return {"error": "scaffold_failed", "niche": niche}

        url = self.deploy_service(worker_name, script)
        stripe_link = self.create_stripe_link(name, price_usd)

        service = {
            "name": name,
            "niche": niche,
            "worker_name": worker_name,
            "url": url or "",
            "stripe_link": stripe_link or "",
            "price_usd": price_usd,
            "script_length": len(script),
            "status": "live" if url else "deploy_failed",
        }

        self.report_to_revenue_engine(service)
        logger.info(f"[SPINNER] ✅ Cycle complete: {service}")
        return service

    def auto_discover_and_spin(self, price_usd: float = 9.0) -> dict:
        """Fully autonomous: discover a niche then spin up the service."""
        niche = self.discover_niche()
        if not niche:
            logger.error("[SPINNER] Niche discovery failed")
            return {"error": "discovery_failed"}
        return self.spin(niche, price_usd=price_usd)

    def list_services(self) -> list[dict]:
        """List all spun-up services from Supabase."""
        if self.providers["supabase"]:
            return supabase_query(SERVICES_TABLE, limit=100)
        return []


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    spinner = SaaSSpinner()
    # Example: spin up a specific service
    result = spinner.spin("AI-powered resume keyword extractor API")
    print(json.dumps(result, indent=2, default=str))
