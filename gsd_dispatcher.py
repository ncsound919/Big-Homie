"""
gsd_dispatcher.py — Big Homie GSD (Get Shit Done) Task Dispatcher

Implements David Allen's GTD/GSD methodology as a task routing layer
over Big Homie's autonomous systems.

Five stages:
  CAPTURE  → Inbox: any input (heartbeat, user, web hook)
  CLARIFY  → Classify: actionable? which context?
  ORGANIZE → Route: @rap, @content, @site, @code, @research, @revenue
  REFLECT  → Log review + weekly summary (via log_review.py)
  ENGAGE   → Execute via sub_agents, cost_guards, heartbeat

Context map:
  @rap      → rap_video_engine.generate_rap_video
  @content  → content_factory.create_content_package
  @site     → site_builder.build_and_deploy_site
  @code     → llm_gateway (opencode routing)
  @research → sub_agents research workflow
  @revenue  → revenue_engine
  @dream    → dream_system (memory consolidation)

Usage:
  from gsd_dispatcher import GSDDispatcher
  gsd = GSDDispatcher()

  # Capture a task
  task_id = await gsd.capture("Generate a trap rap video about NC hustle culture")

  # Or run the full pipeline on a batch
  await gsd.process_inbox()
"""

import os
import asyncio
import uuid
import json
import logging
import sqlite3
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

GSD_DB_PATH = os.path.expanduser(
    os.getenv("GSD_DB_PATH", "~/.big_homie/gsd_inbox.db")
)


# ─── Enums & Dataclasses ──────────────────────────────────────────────────────

class GSDStage(str, Enum):
    INBOX     = "inbox"      # Just captured, not yet classified
    CLARIFIED = "clarified"  # Classified, not yet organized
    ORGANIZED = "organized"  # Routed to context, ready to engage
    ACTIVE    = "active"     # Currently being executed
    DONE      = "done"       # Completed
    SOMEDAY   = "someday"    # Deferred / low priority
    TRASH     = "trash"      # Discarded


class GSDContext(str, Enum):
    RAP      = "@rap"
    CONTENT  = "@content"
    SITE     = "@site"
    CODE     = "@code"
    RESEARCH = "@research"
    REVENUE  = "@revenue"
    DREAM    = "@dream"
    MISC     = "@misc"


@dataclass
class GSDTask:
    task_id: str
    raw_input: str
    stage: GSDStage = GSDStage.INBOX
    context: Optional[GSDContext] = None
    priority: int = 5          # 1=highest, 10=lowest
    actionable: bool = True
    result: dict = field(default_factory=dict)
    cost_usd: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    notes: str = ""
    tags: list = field(default_factory=list)


# ─── Context routing keywords ─────────────────────────────────────────────────

CONTEXT_KEYWORDS = {
    GSDContext.RAP: [
        "rap", "beat", "lyrics", "bars", "trap", "drill", "boom bap",
        "music video", "rap video", "hip hop", "verse", "freestyle",
    ],
    GSDContext.CONTENT: [
        "content", "blog", "article", "post", "tiktok", "instagram",
        "youtube", "twitter", "thread", "caption", "newsletter", "email campaign",
        "write", "script", "copy",
    ],
    GSDContext.SITE: [
        "website", "site", "landing page", "web page", "deploy",
        "build a site", "homepage", "portfolio site", "saas page",
    ],
    GSDContext.CODE: [
        "code", "script", "function", "api", "bug", "fix", "implement",
        "build", "develop", "debug", "refactor", "test", "opencode",
    ],
    GSDContext.RESEARCH: [
        "research", "find", "search", "analyze", "compare", "report",
        "trends", "market", "data", "statistics", "investigate",
    ],
    GSDContext.REVENUE: [
        "revenue", "money", "income", "profit", "sell", "price",
        "stripe", "payment", "subscription", "monetize", "earnings",
    ],
    GSDContext.DREAM: [
        "memory", "consolidate", "dream", "reflect", "summarize past",
        "knowledge graph", "remember",
    ],
}


# ─── Dispatcher ───────────────────────────────────────────────────────────────

class GSDDispatcher:
    """
    GSD-methodology task router for Big Homie.
    Persists tasks to SQLite, classifies via LLM + keyword matching,
    routes to appropriate vertical engine.
    """

    def __init__(self):
        self._init_db()
        self._executors: dict[GSDContext, Callable] = {}
        self._register_defaults()

    # ── DB Init ───────────────────────────────────────────────────────────────

    def _init_db(self):
        os.makedirs(os.path.dirname(GSD_DB_PATH), exist_ok=True)
        conn = sqlite3.connect(GSD_DB_PATH)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS gsd_tasks (
                task_id    TEXT PRIMARY KEY,
                raw_input  TEXT,
                stage      TEXT,
                context    TEXT,
                priority   INTEGER,
                actionable BOOLEAN,
                result     TEXT,
                cost_usd   REAL,
                created_at TEXT,
                updated_at TEXT,
                notes      TEXT,
                tags       TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _save_task(self, task: GSDTask):
        task.updated_at = datetime.utcnow().isoformat()
        conn = sqlite3.connect(GSD_DB_PATH)
        conn.execute("""
            INSERT OR REPLACE INTO gsd_tasks VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            task.task_id, task.raw_input, task.stage.value,
            task.context.value if task.context else None,
            task.priority, task.actionable,
            json.dumps(task.result), task.cost_usd,
            task.created_at, task.updated_at, task.notes,
            json.dumps(task.tags),
        ))
        conn.commit()
        conn.close()

    def _load_by_stage(self, stage: GSDStage) -> list[GSDTask]:
        conn = sqlite3.connect(GSD_DB_PATH)
        rows = conn.execute(
            "SELECT * FROM gsd_tasks WHERE stage = ? ORDER BY priority ASC, created_at ASC",
            (stage.value,)
        ).fetchall()
        conn.close()
        tasks = []
        for row in rows:
            t = GSDTask(
                task_id=row[0], raw_input=row[1],
                stage=GSDStage(row[2]),
                context=GSDContext(row[3]) if row[3] else None,
                priority=row[4], actionable=bool(row[5]),
                result=json.loads(row[6]) if row[6] else {},
                cost_usd=row[7], created_at=row[8], updated_at=row[9],
                notes=row[10], tags=json.loads(row[11]) if row[11] else [],
            )
            tasks.append(t)
        return tasks

    # ── Register executors ────────────────────────────────────────────────────

    def _register_defaults(self):
        """Register all vertical engines as executors."""
        try:
            from rap_video_engine import generate_rap_video
            self.register(GSDContext.RAP, lambda task: generate_rap_video(
                theme=task.raw_input, style="trap"
            ))
        except ImportError:
            pass

        try:
            from content_factory import create_content_package
            self.register(GSDContext.CONTENT, lambda task: create_content_package(
                topic=task.raw_input
            ))
        except ImportError:
            pass

        try:
            from site_builder import build_and_deploy_site
            self.register(GSDContext.SITE, lambda task: build_and_deploy_site(
                name=task.raw_input, niche=task.notes or "business"
            ))
        except ImportError:
            pass

        try:
            from llm_gateway import llm, TaskType
            async def code_executor(task):
                return await llm.complete(
                    messages=[{"role": "user", "content": task.raw_input}],
                    task_type=TaskType.CODING,
                )
            self.register(GSDContext.CODE, code_executor)
        except ImportError:
            pass

    def register(self, context: GSDContext, executor: Callable):
        """Register a custom executor for a context."""
        self._executors[context] = executor
        logger.info(f"[GSD] Registered executor for {context.value}")

    # ── Five GSD Stages ───────────────────────────────────────────────────────

    async def capture(self, raw_input: str, priority: int = 5, tags: Optional[list] = None) -> str:
        """Stage 1: Capture — add anything to the inbox."""
        task = GSDTask(
            task_id=str(uuid.uuid4())[:8],
            raw_input=raw_input,
            stage=GSDStage.INBOX,
            priority=priority,
            tags=tags or [],
        )
        self._save_task(task)
        logger.info(f"[GSD:CAPTURE] {task.task_id} → '{raw_input[:60]}...'" if len(raw_input) > 60 else f"[GSD:CAPTURE] {task.task_id} → '{raw_input}'")
        return task.task_id

    async def clarify(self, task: GSDTask) -> GSDTask:
        """Stage 2: Clarify — is it actionable? What context?"""
        text = task.raw_input.lower()

        # Check for explicit @context tags in input
        for ctx in GSDContext:
            if ctx.value in text:
                task.context = ctx
                task.actionable = True
                task.stage = GSDStage.CLARIFIED
                self._save_task(task)
                return task

        # Keyword matching
        scores = {ctx: 0 for ctx in GSDContext}
        for ctx, keywords in CONTEXT_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    scores[ctx] += 1

        best_ctx = max(scores, key=scores.get)
        if scores[best_ctx] > 0:
            task.context = best_ctx
        else:
            # LLM fallback classification
            task.context = await self._llm_classify(task.raw_input)

        task.actionable = True
        task.stage = GSDStage.CLARIFIED
        self._save_task(task)
        logger.info(f"[GSD:CLARIFY] {task.task_id} → context={task.context.value}")
        return task

    async def organize(self, task: GSDTask) -> GSDTask:
        """Stage 3: Organize — set priority and mark ready to engage."""
        if not task.actionable:
            task.stage = GSDStage.SOMEDAY
        else:
            task.stage = GSDStage.ORGANIZED
        self._save_task(task)
        logger.info(f"[GSD:ORGANIZE] {task.task_id} → stage={task.stage.value}")
        return task

    async def engage(self, task: GSDTask) -> GSDTask:
        """Stage 5: Engage — execute the task via its registered executor."""
        if task.context not in self._executors:
            logger.warning(f"[GSD:ENGAGE] No executor for {task.context} — skipping")
            task.notes = f"No executor registered for {task.context}"
            task.stage = GSDStage.SOMEDAY
            self._save_task(task)
            return task

        task.stage = GSDStage.ACTIVE
        self._save_task(task)

        try:
            executor = self._executors[task.context]
            result = await executor(task)
            task.result = result.__dict__ if hasattr(result, "__dict__") else {"output": str(result)}
            task.cost_usd = task.result.get("cost_usd", task.result.get("total_cost_usd", 0.0))
            task.stage = GSDStage.DONE
            logger.info(f"[GSD:ENGAGE] {task.task_id} DONE — cost=${task.cost_usd:.4f}")
        except Exception as e:
            task.notes = f"Execution error: {e}"
            task.stage = GSDStage.ORGANIZED  # Retry next cycle
            logger.error(f"[GSD:ENGAGE] {task.task_id} failed: {e}")

        self._save_task(task)
        return task

    # ── Full pipeline ─────────────────────────────────────────────────────────

    async def process_inbox(self, max_tasks: int = 10) -> list[GSDTask]:
        """
        Run the full GSD pipeline on inbox items.
        Called by heartbeat.py every 45 minutes.
        """
        inbox = self._load_by_stage(GSDStage.INBOX)[:max_tasks]
        organized_queue = self._load_by_stage(GSDStage.ORGANIZED)[:max_tasks]

        logger.info(f"[GSD] Processing {len(inbox)} inbox + {len(organized_queue)} organized tasks")

        # Process inbox → clarify → organize
        clarified = await asyncio.gather(*[self.clarify(t) for t in inbox], return_exceptions=True)
        organized = await asyncio.gather(
            *[self.organize(t) for t in clarified if isinstance(t, GSDTask)],
            return_exceptions=True
        )

        # Engage all organized tasks (including pre-existing queue)
        to_engage = [
            t for t in organized if isinstance(t, GSDTask) and t.stage == GSDStage.ORGANIZED
        ] + organized_queue

        results = await asyncio.gather(
            *[self.engage(t) for t in to_engage],
            return_exceptions=True
        )

        done = [t for t in results if isinstance(t, GSDTask) and t.stage == GSDStage.DONE]
        logger.info(f"[GSD] Cycle complete — {len(done)} tasks done")
        return done

    async def _llm_classify(self, text: str) -> GSDContext:
        """Fallback: use LLM to classify task context."""
        try:
            from llm_gateway import llm, TaskType
            contexts = ", ".join(f"{c.value}" for c in GSDContext)
            prompt = f"""Classify this task into one context: {contexts}
Task: {text}
Respond with ONLY the context label (e.g. @content). No explanation."""
            resp = await llm.complete(
                messages=[{"role": "user", "content": prompt}],
                task_type=TaskType.FAST,
            )
            raw = (resp.content if hasattr(resp, "content") else str(resp)).strip()
            for ctx in GSDContext:
                if ctx.value in raw:
                    return ctx
        except Exception:
            pass
        return GSDContext.MISC

    # ── Reflect (weekly review) ───────────────────────────────────────────────

    async def reflect(self) -> dict:
        """Stage 4: Reflect — weekly summary of completed + pending tasks."""
        from datetime import datetime, timedelta
        conn = sqlite3.connect(GSD_DB_PATH)
        one_week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        done_rows = conn.execute(
            "SELECT context, COUNT(*), SUM(cost_usd) FROM gsd_tasks WHERE stage='done' AND updated_at > ? GROUP BY context",
            (one_week_ago,)
        ).fetchall()
        pending = conn.execute(
            "SELECT COUNT(*) FROM gsd_tasks WHERE stage IN ('inbox','organized','active')"
        ).fetchone()[0]
        conn.close()

        summary = {
            "period": "last_7_days",
            "completed_by_context": {row[0]: {"count": row[1], "cost_usd": row[2]} for row in done_rows},
            "pending_tasks": pending,
            "total_completed": sum(r[1] for r in done_rows),
            "total_cost_usd": sum(r[2] for r in done_rows),
        }
        logger.info(f"[GSD:REFLECT] Weekly summary: {summary['total_completed']} done, ${summary['total_cost_usd']:.4f} spent")
        return summary


# ─── Module-level instance ────────────────────────────────────────────────────

gsd = GSDDispatcher()

async def capture(text: str, priority: int = 5) -> str:
    """Shortcut: capture a task directly from anywhere in Big Homie."""
    return await gsd.capture(text, priority)
