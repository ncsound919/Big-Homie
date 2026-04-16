"""
free_api_stack.py
-----------------
Zero-cost API integrations for Big Homie SaaS/MaaS income generation.

Providers wired here (all free tiers):
  • Groq          — fast Llama 3 inference (sub-agent compute, chatbot APIs)
  • HuggingFace   — image generation, text, embeddings
  • Brave Search  — web search-as-a-service (2k free req/mo)
  • Resend        — transactional email (3k free/mo)
  • Upstash Redis — async job queue (10k req/day free)
  • Supabase      — multi-tenant SaaS DB + auth
  • Cloudflare    — Workers deploy + KV (already in repo)

All clients are lazy-loaded so missing keys don't crash startup.

Usage:
    from free_api_stack import groq_chat, hf_generate_image, brave_search
    from free_api_stack import send_email, enqueue_job, dequeue_job
    from free_api_stack import supabase_insert, deploy_worker
"""

import os
import json
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# 1. GROQ — Fast free Llama 3 inference
# ═══════════════════════════════════════════════════════════════════════════
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama3-70b-8192")  # or llama3-8b-8192

def groq_chat(messages: list[dict], model: str = GROQ_MODEL,
              temperature: float = 0.3, max_tokens: int = 2048) -> Optional[str]:
    """Chat completion via Groq free tier (very fast Llama 3)."""
    if not GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not set")
        return None
    try:
        import httpx
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {"model": model, "messages": messages,
                   "temperature": temperature, "max_tokens": max_tokens}
        r = httpx.post("https://api.groq.com/openai/v1/chat/completions",
                       headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        logger.error(f"groq_chat error: {exc}")
        return None


# ═══════════════════════════════════════════════════════════════════════════
# 2. HUGGING FACE — Free inference (image gen, text, embeddings)
# ═══════════════════════════════════════════════════════════════════════════
HF_API_KEY    = os.getenv("HF_API_KEY", "")
HF_IMAGE_MODEL = os.getenv("HF_IMAGE_MODEL", "stabilityai/stable-diffusion-xl-base-1.0")
HF_TEXT_MODEL  = os.getenv("HF_TEXT_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")

def hf_generate_image(prompt: str, model: str = HF_IMAGE_MODEL) -> Optional[bytes]:
    """Generate an image via HuggingFace Inference API. Returns raw bytes."""
    if not HF_API_KEY:
        logger.warning("HF_API_KEY not set")
        return None
    try:
        import httpx
        url = f"https://api-inference.huggingface.co/models/{model}"
        r = httpx.post(url, headers={"Authorization": f"Bearer {HF_API_KEY}"},
                       json={"inputs": prompt}, timeout=120)
        r.raise_for_status()
        return r.content
    except Exception as exc:
        logger.error(f"hf_generate_image error: {exc}")
        return None

def hf_text(prompt: str, model: str = HF_TEXT_MODEL, max_tokens: int = 512) -> Optional[str]:
    """Text generation via HuggingFace free inference."""
    if not HF_API_KEY:
        return None
    try:
        import httpx
        url = f"https://api-inference.huggingface.co/models/{model}"
        r = httpx.post(url, headers={"Authorization": f"Bearer {HF_API_KEY}"},
                       json={"inputs": prompt, "parameters": {"max_new_tokens": max_tokens}},
                       timeout=60)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list):
            return data[0].get("generated_text", "")
        return str(data)
    except Exception as exc:
        logger.error(f"hf_text error: {exc}")
        return None


# ═══════════════════════════════════════════════════════════════════════════
# 3. BRAVE SEARCH — Web search (2k free req/mo)
# ═══════════════════════════════════════════════════════════════════════════
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY", "")

def brave_search(query: str, count: int = 10) -> list[dict]:
    """Search the web via Brave Search API. Returns list of {title, url, description}."""
    if not BRAVE_API_KEY:
        logger.warning("BRAVE_API_KEY not set")
        return []
    try:
        import httpx
        r = httpx.get("https://api.search.brave.com/res/v1/web/search",
                      headers={"Accept": "application/json",
                               "Accept-Encoding": "gzip",
                               "X-Subscription-Token": BRAVE_API_KEY},
                      params={"q": query, "count": count},
                      timeout=30)
        r.raise_for_status()
        results = r.json().get("web", {}).get("results", [])
        return [{"title": x.get("title"), "url": x.get("url"),
                 "description": x.get("description")} for x in results]
    except Exception as exc:
        logger.error(f"brave_search error: {exc}")
        return []


# ═══════════════════════════════════════════════════════════════════════════
# 4. RESEND — Transactional email (3k free/mo)
# ═══════════════════════════════════════════════════════════════════════════
RESEND_API_KEY   = os.getenv("RESEND_API_KEY", "")
RESEND_FROM      = os.getenv("RESEND_FROM", "Big Homie <noreply@yourdomain.com>")

def send_email(to: str, subject: str, html: str,
               from_addr: str = RESEND_FROM) -> bool:
    """Send transactional email via Resend free tier."""
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set")
        return False
    try:
        import httpx
        r = httpx.post("https://api.resend.com/emails",
                       headers={"Authorization": f"Bearer {RESEND_API_KEY}",
                                "Content-Type": "application/json"},
                       json={"from": from_addr, "to": [to],
                             "subject": subject, "html": html},
                       timeout=30)
        r.raise_for_status()
        logger.info(f"Email sent to {to} via Resend")
        return True
    except Exception as exc:
        logger.error(f"send_email error: {exc}")
        return False


# ═══════════════════════════════════════════════════════════════════════════
# 5. UPSTASH REDIS — Async job queue (10k req/day free)
# ═══════════════════════════════════════════════════════════════════════════
UPSTASH_REDIS_URL   = os.getenv("UPSTASH_REDIS_URL", "")
UPSTASH_REDIS_TOKEN = os.getenv("UPSTASH_REDIS_TOKEN", "")

def _upstash(cmd: list) -> Any:
    if not UPSTASH_REDIS_URL or not UPSTASH_REDIS_TOKEN:
        return None
    try:
        import httpx
        r = httpx.post(UPSTASH_REDIS_URL,
                       headers={"Authorization": f"Bearer {UPSTASH_REDIS_TOKEN}"},
                       json=cmd, timeout=15)
        r.raise_for_status()
        return r.json().get("result")
    except Exception as exc:
        logger.error(f"upstash error {cmd[0]}: {exc}")
        return None

def enqueue_job(queue: str, payload: dict) -> bool:
    """Push a job dict onto an Upstash Redis list."""
    result = _upstash(["RPUSH", queue, json.dumps(payload)])
    return result is not None

def dequeue_job(queue: str, timeout: int = 5) -> Optional[dict]:
    """Blocking-pop a job from an Upstash Redis list."""
    result = _upstash(["BLPOP", queue, str(timeout)])
    if result and isinstance(result, list) and len(result) > 1:
        try:
            return json.loads(result[1])
        except Exception:
            return None
    return None

def queue_length(queue: str) -> int:
    result = _upstash(["LLEN", queue])
    return int(result) if result is not None else 0


# ═══════════════════════════════════════════════════════════════════════════
# 6. SUPABASE — Multi-tenant SaaS DB + auth (free tier)
# ═══════════════════════════════════════════════════════════════════════════
SUPABASE_URL      = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

def _sb_headers() -> dict:
    return {"apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"}

def supabase_insert(table: str, row: dict) -> Optional[dict]:
    """Insert a row into a Supabase table."""
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return None
    try:
        import httpx
        r = httpx.post(f"{SUPABASE_URL}/rest/v1/{table}",
                       headers=_sb_headers(), json=row, timeout=30)
        r.raise_for_status()
        data = r.json()
        return data[0] if isinstance(data, list) else data
    except Exception as exc:
        logger.error(f"supabase_insert error: {exc}")
        return None

def supabase_query(table: str, filters: str = "", limit: int = 100) -> list[dict]:
    """Query rows from Supabase. filters is a PostgREST query string."""
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return []
    try:
        import httpx
        url = f"{SUPABASE_URL}/rest/v1/{table}?{filters}&limit={limit}"
        r = httpx.get(url, headers=_sb_headers(), timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        logger.error(f"supabase_query error: {exc}")
        return []


# ═══════════════════════════════════════════════════════════════════════════
# 7. CLOUDFLARE WORKERS — Deploy micro-SaaS endpoints (free plan)
# ═══════════════════════════════════════════════════════════════════════════
CF_API_TOKEN   = os.getenv("CLOUDFLARE_API_TOKEN", "")
CF_ACCOUNT_ID  = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")

def deploy_worker(worker_name: str, script: str,
                  routes: Optional[list[str]] = None) -> bool:
    """
    Deploy a Cloudflare Worker script.
    script: the JavaScript/TypeScript worker code as a string.
    """
    if not CF_API_TOKEN or not CF_ACCOUNT_ID:
        logger.warning("CLOUDFLARE_API_TOKEN or CLOUDFLARE_ACCOUNT_ID not set")
        return False
    try:
        import httpx
        url = (f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}"
               f"/workers/scripts/{worker_name}")
        headers = {"Authorization": f"Bearer {CF_API_TOKEN}"}
        files = {"script": ("worker.js", script, "application/javascript")}
        r = httpx.put(url, headers=headers, files=files, timeout=60)
        r.raise_for_status()
        logger.info(f"Worker '{worker_name}' deployed successfully")
        return True
    except Exception as exc:
        logger.error(f"deploy_worker error: {exc}")
        return False


# ═══════════════════════════════════════════════════════════════════════════
# Health check — verify which providers are configured
# ═══════════════════════════════════════════════════════════════════════════
def check_providers() -> dict[str, bool]:
    return {
        "groq":      bool(GROQ_API_KEY),
        "huggingface": bool(HF_API_KEY),
        "brave":     bool(BRAVE_API_KEY),
        "resend":    bool(RESEND_API_KEY),
        "upstash":   bool(UPSTASH_REDIS_URL and UPSTASH_REDIS_TOKEN),
        "supabase":  bool(SUPABASE_URL and SUPABASE_ANON_KEY),
        "cloudflare": bool(CF_API_TOKEN and CF_ACCOUNT_ID),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(json.dumps(check_providers(), indent=2))
