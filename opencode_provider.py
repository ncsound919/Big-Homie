"""
opencode_provider.py
--------------------
Makes opencode (SST open-source coding agent) the DEFAULT LLM backend for
Big Homie. Falls back through the existing provider cascade when opencode is
unavailable or the task isn't code-related.

Opencode exposes an OpenAI-compatible /v1/chat/completions endpoint on
localhost:4111 by default.  We wire it in front of the existing llm_gateway
routing so every coding/scaffolding task hits opencode first.

Usage:
    from opencode_provider import opencode_chat, is_opencode_available
"""

import os
import logging
from typing import Optional

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────────────────
OPENCODE_ENABLED: bool = os.getenv("OPENCODE_ENABLED", "true").lower() == "true"
OPENCODE_URL: str = os.getenv("OPENCODE_URL", "http://localhost:4111/v1")
OPENCODE_MODEL: str = os.getenv("OPENCODE_MODEL", "opencode")  # or any model opencode proxies
OPENCODE_TIMEOUT: int = int(os.getenv("OPENCODE_TIMEOUT", "120"))

# Task types that should always route through opencode
CODE_TASK_TYPES = {
    "code", "scaffold", "debug", "refactor", "review",
    "generate_file", "write_script", "build_endpoint",
    "saas_scaffold", "maas_scaffold",
}


def is_opencode_available() -> bool:
    """Probe the opencode health endpoint.  Returns False if unreachable."""
    if not OPENCODE_ENABLED or httpx is None:
        return False
    try:
        r = httpx.get(f"{OPENCODE_URL.rstrip('/v1')}/health", timeout=3)
        return r.status_code < 400
    except Exception:
        try:
            # Fallback: hit the models endpoint instead
            r = httpx.get(f"{OPENCODE_URL}/models", timeout=3)
            return r.status_code < 400
        except Exception:
            return False


def opencode_chat(
    messages: list[dict],
    model: str = OPENCODE_MODEL,
    temperature: float = 0.2,
    max_tokens: int = 4096,
    system: Optional[str] = None,
) -> Optional[str]:
    """
    Send a chat completion request to the local opencode server.
    Returns the assistant message text, or None on failure.
    """
    if httpx is None:
        logger.error("httpx not installed — cannot call opencode")
        return None

    payload = {
        "model": model,
        "messages": messages if not system else [{"role": "system", "content": system}] + messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        with httpx.Client(timeout=OPENCODE_TIMEOUT) as client:
            resp = client.post(f"{OPENCODE_URL}/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as exc:
        logger.warning(f"opencode_chat failed: {exc}")
        return None


def route_to_opencode(task_type: str, messages: list[dict], **kwargs) -> Optional[str]:
    """
    Route a task to opencode if the task type is code-related AND opencode is up.
    Returns the response text or None (caller falls back to llm_gateway).
    """
    if task_type not in CODE_TASK_TYPES:
        return None
    if not is_opencode_available():
        logger.info("opencode unavailable — falling back to llm_gateway")
        return None
    logger.info(f"Routing task '{task_type}' to opencode @ {OPENCODE_URL}")
    return opencode_chat(messages, **kwargs)


# ── Router integration patch ─────────────────────────────────────────────────
# Call this once at startup to monkey-patch the existing router so opencode
# sits at the front of the coding model cascade.
def install_opencode_as_default() -> bool:
    """
    Attempt to register opencode as the primary coding model in router.py.
    Returns True if successful.
    """
    try:
        import router  # type: ignore
        original_route = getattr(router, "route_coding_task", None)

        if original_route is None:
            logger.warning("router.route_coding_task not found — skipping patch")
            return False

        def patched_route_coding_task(messages, task_type="code", **kw):
            result = route_to_opencode(task_type, messages, **kw)
            if result is not None:
                return result
            return original_route(messages, task_type=task_type, **kw)

        router.route_coding_task = patched_route_coding_task
        logger.info("✅ opencode installed as default coding model")
        return True
    except ImportError:
        logger.warning("router.py not importable — opencode patch skipped")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(f"opencode available: {is_opencode_available()}")
    install_opencode_as_default()
