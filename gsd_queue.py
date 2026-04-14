"""
gsd_queue.py
------------
Get Shit Done (GSD / GTD) task pipeline for Big Homie.

Five stages:
  1. CAPTURE  — anything lands here first (from heartbeat, user, swarm scan)
  2. CLARIFY  — cognitive_core classifies: actionable / reference / someday / trash
  3. ORGANIZE — router assigns context: @code @research @revenue @deploy @comms
  4. REFLECT  — log_review daily sweep; marks stale items
  5. ENGAGE   — sub_agents executes next action; cost_guards keeps spend lean

Persistence: SQLite via database_ops (no extra deps).

Usage:
    from gsd_queue import GSDQueue
    q = GSDQueue()
    q.capture("Build Stripe webhook endpoint for saas_spinner", source="user")
    q.run_pipeline()   # clarify → organize → engage next item
"""

import os
import json
import time
import logging
import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("GSD_DB", "data/gsd_queue.db")


class Stage(str, Enum):
    CAPTURE  = "capture"
    CLARIFY  = "clarify"
    ORGANIZE = "organize"
    REFLECT  = "reflect"
    ENGAGE   = "engage"
    DONE     = "done"
    TRASH    = "trash"


class Context(str, Enum):
    CODE     = "@code"
    RESEARCH = "@research"
    REVENUE  = "@revenue"
    DEPLOY   = "@deploy"
    COMMS    = "@comms"
    SOMEDAY  = "@someday"
    NONE     = "@none"


@dataclass
class GSDItem:
    id: Optional[int] = None
    title: str = ""
    body: str = ""
    source: str = "user"          # heartbeat | user | swarm | revenue_engine
    stage: str = Stage.CAPTURE
    context: str = Context.NONE
    priority: int = 5             # 1 (highest) – 10 (lowest)
    actionable: Optional[bool] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    meta: str = "{}"              # JSON blob for extra data


class GSDQueue:
    def __init__(self, db_path: str = DB_PATH):
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        self.db_path = db_path
        self._init_db()

    # ── DB ────────────────────────────────────────────────────────────────────
    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._conn() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS gsd_items (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    title      TEXT NOT NULL,
                    body       TEXT DEFAULT '',
                    source     TEXT DEFAULT 'user',
                    stage      TEXT DEFAULT 'capture',
                    context    TEXT DEFAULT '@none',
                    priority   INTEGER DEFAULT 5,
                    actionable INTEGER,
                    created_at TEXT,
                    updated_at TEXT,
                    meta       TEXT DEFAULT '{}'
                )
            """)
            c.commit()

    def _save(self, item: GSDItem) -> int:
        item.updated_at = datetime.now(timezone.utc).isoformat()
        with self._conn() as c:
            if item.id is None:
                cur = c.execute(
                    "INSERT INTO gsd_items (title,body,source,stage,context,priority,actionable,created_at,updated_at,meta) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (item.title, item.body, item.source, item.stage, item.context,
                     item.priority, item.actionable, item.created_at, item.updated_at, item.meta),
                )
                item.id = cur.lastrowid
            else:
                c.execute(
                    "UPDATE gsd_items SET title=?,body=?,source=?,stage=?,context=?,priority=?,"
                    "actionable=?,updated_at=?,meta=? WHERE id=?",
                    (item.title, item.body, item.source, item.stage, item.context,
                     item.priority, item.actionable, item.updated_at, item.meta, item.id),
                )
            c.commit()
        return item.id

    def _load(self, stage: Optional[str] = None, limit: int = 50) -> list[GSDItem]:
        with self._conn() as c:
            if stage:
                rows = c.execute("SELECT * FROM gsd_items WHERE stage=? ORDER BY priority,created_at LIMIT ?",
                                 (stage, limit)).fetchall()
            else:
                rows = c.execute("SELECT * FROM gsd_items ORDER BY priority,created_at LIMIT ?",
                                 (limit,)).fetchall()
        return [GSDItem(**dict(r)) for r in rows]

    # ── Stage 1: CAPTURE ─────────────────────────────────────────────────────
    def capture(self, title: str, body: str = "", source: str = "user",
                priority: int = 5, meta: dict | None = None) -> GSDItem:
        """Drop anything into the inbox. Fast — no classification yet."""
        item = GSDItem(
            title=title, body=body, source=source,
            stage=Stage.CAPTURE, priority=priority,
            meta=json.dumps(meta or {}),
        )
        self._save(item)
        logger.info(f"[GSD CAPTURE] #{item.id} — {title}")
        return item

    # ── Stage 2: CLARIFY ─────────────────────────────────────────────────────
    def clarify(self, item: GSDItem) -> GSDItem:
        """
        Use cognitive_core to decide if the item is actionable.
        Falls back to keyword heuristics if cognitive_core unavailable.
        """
        try:
            from cognitive_core import CognitiveCore  # type: ignore
            core = CognitiveCore()
            result = core.classify_task(item.title + " " + item.body)
            item.actionable = result.get("actionable", True)
            if result.get("trash"):
                item.stage = Stage.TRASH
                logger.info(f"[GSD CLARIFY] #{item.id} → TRASH")
                self._save(item)
                return item
        except Exception as exc:
            logger.debug(f"cognitive_core unavailable: {exc} — using heuristics")
            trash_keywords = {"spam", "ignore", "discard", "unsubscribe"}
            item.actionable = not any(k in item.title.lower() for k in trash_keywords)

        if not item.actionable:
            item.stage = Stage.REFLECT  # park as someday/reference
        else:
            item.stage = Stage.ORGANIZE
        self._save(item)
        logger.info(f"[GSD CLARIFY] #{item.id} actionable={item.actionable} → {item.stage}")
        return item

    # ── Stage 3: ORGANIZE ────────────────────────────────────────────────────
    def organize(self, item: GSDItem) -> GSDItem:
        """
        Assign a context tag via router.py task classification.
        Falls back to keyword matching.
        """
        context_map = {
            "code":     Context.CODE,
            "scaffold": Context.CODE,
            "debug":    Context.CODE,
            "research": Context.RESEARCH,
            "search":   Context.RESEARCH,
            "revenue":  Context.REVENUE,
            "stripe":   Context.REVENUE,
            "income":   Context.REVENUE,
            "deploy":   Context.DEPLOY,
            "cloudflare": Context.DEPLOY,
            "email":    Context.COMMS,
            "message":  Context.COMMS,
        }
        text = (item.title + " " + item.body).lower()
        assigned = Context.NONE
        try:
            from router import classify_task_context  # type: ignore
            assigned_str = classify_task_context(text)
            assigned = Context(assigned_str) if assigned_str in Context._value2member_map_ else Context.NONE
        except Exception:
            for keyword, ctx in context_map.items():
                if keyword in text:
                    assigned = ctx
                    break

        item.context = assigned
        item.stage = Stage.ENGAGE
        self._save(item)
        logger.info(f"[GSD ORGANIZE] #{item.id} → context={item.context}")
        return item

    # ── Stage 4: REFLECT ─────────────────────────────────────────────────────
    def reflect(self, stale_hours: int = 24) -> list[GSDItem]:
        """
        Daily review pass. Flags items stuck in ENGAGE > stale_hours as needing review.
        Returns list of stale items.
        """
        stale = []
        with self._conn() as c:
            rows = c.execute("SELECT * FROM gsd_items WHERE stage=?", (Stage.ENGAGE,)).fetchall()
        for r in rows:
            item = GSDItem(**dict(r))
            updated = datetime.fromisoformat(item.updated_at)
            age_hours = (datetime.now(timezone.utc) - updated.replace(tzinfo=timezone.utc)).total_seconds() / 3600
            if age_hours > stale_hours:
                stale.append(item)
                logger.info(f"[GSD REFLECT] #{item.id} stale ({age_hours:.0f}h) — needs review")
        return stale

    # ── Stage 5: ENGAGE ──────────────────────────────────────────────────────
    def engage_next(self) -> Optional[GSDItem]:
        """
        Pop the highest-priority ENGAGE item and dispatch to sub_agents.
        """
        items = self._load(stage=Stage.ENGAGE, limit=1)
        if not items:
            logger.info("[GSD ENGAGE] inbox empty — nothing to do")
            return None
        item = items[0]
        logger.info(f"[GSD ENGAGE] executing #{item.id} [{item.context}] — {item.title}")
        try:
            from sub_agents import SubAgentManager  # type: ignore
            mgr = SubAgentManager()
            mgr.execute_task(
                task_type=item.context.lstrip("@"),
                task_description=item.title + "\n" + item.body,
                metadata=json.loads(item.meta),
            )
            item.stage = Stage.DONE
        except Exception as exc:
            logger.error(f"[GSD ENGAGE] sub_agent error: {exc}")
            meta = json.loads(item.meta)
            meta["last_error"] = str(exc)
            item.meta = json.dumps(meta)
        self._save(item)
        return item

    # ── Full pipeline ────────────────────────────────────────────────────────
    def run_pipeline(self, batch: int = 10):
        """Process up to `batch` captured items through CLARIFY → ORGANIZE → ENGAGE."""
        captured = self._load(stage=Stage.CAPTURE, limit=batch)
        for item in captured:
            item = self.clarify(item)
            if item.stage == Stage.ORGANIZE:
                item = self.organize(item)
        self.engage_next()
        stale = self.reflect()
        if stale:
            logger.warning(f"[GSD REFLECT] {len(stale)} stale items need attention")

    # ── Convenience ──────────────────────────────────────────────────────────
    def inbox_count(self) -> dict:
        with self._conn() as c:
            rows = c.execute("SELECT stage, COUNT(*) as n FROM gsd_items GROUP BY stage").fetchall()
        return {r["stage"]: r["n"] for r in rows}


async def push_gsd_step(
    objective_id: str,
    order: int,
    action: str,
    tool: str,
    params: dict,
):
    """
    Persist a single GSD task step to the Draymond ``bm_mission_steps`` table.

    Args:
        objective_id: Parent objective/goal UUID in Draymond.
        order: Step sequence number within the objective.
        action: Human-readable action description.
        tool: Tool name to invoke for this step.
        params: Tool parameters as a dict (stored as JSONB).
    """
    try:
        from supabase_client import get_supabase
        db = get_supabase()
        db.table("bm_mission_steps").insert({
            "objective_id": objective_id,
            "step_order": order,
            "action": action,
            "tool": tool,
            "params": params,
            "status": "pending",
        }).execute()
    except Exception as e:
        logger.error(f"push_gsd_step failed for objective '{objective_id}' step {order}: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    q = GSDQueue()
    q.capture("Test item from CLI", source="cli")
    q.run_pipeline()
    print(q.inbox_count())
