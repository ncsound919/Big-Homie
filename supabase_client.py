"""
supabase_client.py — Draymond backend connection
Singleton client for the Draymond Supabase project at gkxmehoarrxzwrhjsezt.supabase.co
"""
from __future__ import annotations

from typing import Optional

from supabase import Client, create_client

from config import settings


def _resolve_key() -> str:
    """Return the best available Supabase key (anon > legacy key field)."""
    anon = getattr(settings, "supabase_anon_key", "")
    if anon:
        return anon
    # Fall back to the legacy supabase_key field
    if settings.supabase_key:
        return settings.supabase_key
    # Last-resort published anon key (read-only, RLS enforced)
    return "sb_publishable_Ysm568aFGilsd-nUZN8a6w_eW5vc9uq"


def _resolve_url() -> str:
    if settings.supabase_url:
        return settings.supabase_url
    return "https://gkxmehoarrxzwrhjsezt.supabase.co"


_client: Optional[Client] = None


def get_supabase() -> Client:
    """Return the shared Supabase client, creating it on first call."""
    global _client
    if _client is None:
        _client = create_client(_resolve_url(), _resolve_key())
    return _client
