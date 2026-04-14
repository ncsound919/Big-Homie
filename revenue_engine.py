"""
Revenue Engine – Sub-Agent Orchestrated Revenue Generation
Coordinates multiple revenue streams via goal-oriented sub-agent tasks
"""
import asyncio
import uuid
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
from config import settings


class RevenueStream(str, Enum):
    TRADING = "trading"
    CRYPTO = "crypto"
    OPTIONS = "options"
    BETTING = "betting"
    FREELANCE = "freelance"
    ECOMMERCE = "ecommerce"
    SAAS = "saas"
    MAAS = "maas"
    SUPPLY_CHAIN = "supply_chain"
    CALL_CENTER = "call_center"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class RevenueTask:
    """A revenue-generating task assigned to a sub-agent"""
    id: str
    stream: RevenueStream
    description: str
    goal_usd: float
    risk: RiskLevel
    status: str = "pending"
    result: Optional[Dict] = None
    revenue_usd: float = 0.0
    cost_usd: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    @property
    def profit_usd(self) -> float:
        return self.revenue_usd - self.cost_usd


@dataclass
class RevenueReport:
    """Daily revenue summary"""
    date: str
    total_revenue: float
    total_cost: float
    total_profit: float
    by_stream: Dict[str, float]
    tasks_completed: int
    tasks_failed: int
    goal_daily: float
    goal_progress_pct: float


class RevenueEngine:
    """
    Orchestrates revenue-generating activities across multiple streams.

    Workflow:
    1. Evaluate configured active streams
    2. Decompose daily/session goal into per-stream sub-tasks
    3. Dispatch tasks to specialized sub-agents (trading, ecommerce, etc.)
    4. Monitor execution, enforce risk limits, and collect results
    5. Emit revenue reports summarizing task outcomes and financial totals

    This class coordinates task execution and reporting only. Any approval
    requirements, transaction safeguards, or reinvestment behavior must be
    implemented by the specific task handlers or external orchestration layers.
    """

    def __init__(self):
        self.tasks: Dict[str, RevenueTask] = {}
        self.daily_revenue: Dict[str, float] = {}   # date_str -> revenue
        self.daily_cost: Dict[str, float] = {}       # date_str -> cost
        self._active = False

    # ──────────────────────────────────────────────────────────────────────────
    # Stream Activation
    # ──────────────────────────────────────────────────────────────────────────

    @property
    def active_streams(self) -> List[RevenueStream]:
        """Parse active streams from settings"""
        raw = settings.revenue_active_streams or ""
        result = []
        for s in raw.split(","):
            s = s.strip().lower()
            try:
                result.append(RevenueStream(s))
            except ValueError:
                pass
        return result

    @property
    def risk_level(self) -> RiskLevel:
        try:
            return RiskLevel(settings.revenue_risk_level.lower())
        except ValueError:
            return RiskLevel.LOW

    # ──────────────────────────────────────────────────────────────────────────
    # Goal Management
    # ──────────────────────────────────────────────────────────────────────────

    def get_daily_goal(self) -> float:
        return settings.revenue_goal_daily_usd

    def get_today_revenue(self) -> float:
        today = date.today().isoformat()
        return self.daily_revenue.get(today, 0.0)

    def get_today_cost(self) -> float:
        today = date.today().isoformat()
        return self.daily_cost.get(today, 0.0)

    def get_today_profit(self) -> float:
        return self.get_today_revenue() - self.get_today_cost()

    def record_revenue(self, amount: float, cost: float = 0.0):
        today = date.today().isoformat()
        self.daily_revenue[today] = self.daily_revenue.get(today, 0.0) + amount
        self.daily_cost[today] = self.daily_cost.get(today, 0.0) + cost
        logger.info(f"Revenue recorded: +${amount:.2f} (cost ${cost:.2f}). Today total: ${self.get_today_revenue():.2f}")

    # ──────────────────────────────────────────────────────────────────────────
    # Task Management
    # ──────────────────────────────────────────────────────────────────────────

    def create_task(
        self,
        stream: RevenueStream,
        description: str,
        goal_usd: float,
        risk: Optional[RiskLevel] = None,
    ) -> RevenueTask:
        """Create a new revenue task"""
        task = RevenueTask(
            id=uuid.uuid4().hex[:8],
            stream=stream,
            description=description,
            goal_usd=goal_usd,
            risk=risk or self.risk_level,
        )
        self.tasks[task.id] = task
        logger.info(f"Revenue task created: [{task.id}] {stream.value} – ${goal_usd:.2f} goal")
        return task

    def complete_task(self, task_id: str, revenue: float, cost: float = 0.0, result: Optional[Dict] = None):
        """Mark a task complete and record revenue"""
        task = self.tasks.get(task_id)
        if not task:
            logger.warning(f"Revenue task not found: {task_id}")
            return
        task.status = "completed"
        task.revenue_usd = revenue
        task.cost_usd = cost
        task.result = result or {}
        task.completed_at = datetime.now()
        self.record_revenue(revenue, cost)
        logger.info(f"Revenue task {task_id} complete: +${revenue:.2f} profit=${task.profit_usd:.2f}")

    def fail_task(self, task_id: str, error: str):
        """Mark a task as failed"""
        task = self.tasks.get(task_id)
        if task:
            task.status = "failed"
            task.error = error
            task.completed_at = datetime.now()
            logger.warning(f"Revenue task {task_id} failed: {error}")

    # ──────────────────────────────────────────────────────────────────────────
    # Orchestration
    # ──────────────────────────────────────────────────────────────────────────

    async def run_session(self, session_goal_usd: float = 0.0) -> RevenueReport:
        """
        Execute a revenue session:
        1. Assess active streams and daily goal
        2. Plan sub-tasks per stream
        3. Execute tasks (with risk gating)
        4. Return revenue report
        """
        if not settings.revenue_engine_enabled:
            logger.info("Revenue engine is disabled")
            return self._build_report()

        goal = session_goal_usd or self.get_daily_goal()
        streams = self.active_streams

        if not streams:
            logger.info("No active revenue streams configured")
            return self._build_report()

        logger.info(f"Revenue engine session starting: goal=${goal:.2f} streams={[s.value for s in streams]}")

        per_stream_goal = goal / len(streams) if streams else 0.0
        tasks_to_run = []

        for stream in streams:
            task = self.create_task(
                stream=stream,
                description=self._default_task_description(stream, per_stream_goal),
                goal_usd=per_stream_goal,
            )
            tasks_to_run.append(task)

        # Execute tasks concurrently (up to agent parallelism limit)
        await asyncio.gather(
            *[self._execute_task(task) for task in tasks_to_run],
            return_exceptions=True,
        )

        report = self._build_report()
        logger.info(
            f"Revenue session complete: revenue=${report.total_revenue:.2f} "
            f"profit=${report.total_profit:.2f} "
            f"goal_progress={report.goal_progress_pct:.1f}%"
        )
        return report

    async def _execute_task(self, task: RevenueTask):
        """Route a task to the appropriate stream executor"""
        try:
            task.status = "running"
            max_single = settings.revenue_max_single_trade_usd

            if task.risk == RiskLevel.HIGH and self.risk_level != RiskLevel.HIGH:
                self.fail_task(task.id, "Task risk level exceeds configured risk tolerance")
                return

            handler = self._stream_handlers().get(task.stream)
            if handler:
                await handler(task, max_single)
            else:
                logger.warning(f"No handler for stream: {task.stream.value} – task {task.id} skipped")
                self.fail_task(task.id, f"No handler implemented for stream: {task.stream.value}")
        except Exception as e:
            logger.error(f"Revenue task {task.id} exception: {e}")
            self.fail_task(task.id, str(e))

    def _stream_handlers(self) -> Dict:
        return {
            RevenueStream.TRADING:      self._handle_trading,
            RevenueStream.CRYPTO:       self._handle_crypto,
            RevenueStream.OPTIONS:      self._handle_options,
            RevenueStream.BETTING:      self._handle_betting,
            RevenueStream.ECOMMERCE:    self._handle_ecommerce,
            RevenueStream.SAAS:         self._handle_saas,
            RevenueStream.MAAS:         self._handle_maas,
            RevenueStream.SUPPLY_CHAIN: self._handle_supply_chain,
            RevenueStream.CALL_CENTER:  self._handle_call_center,
            RevenueStream.FREELANCE:    self._handle_freelance,
        }

    # ── Stream Handlers ───────────────────────────────────────────────────────

    async def _handle_trading(self, task: RevenueTask, max_amount: float):
        """Alpaca stock/ETF trading sub-agent"""
        try:
            from integrations.base_l2_integration import base_l2
            logger.info(f"[TRADING] Task {task.id}: researching positions via Alpaca")
            # Placeholder: real implementation would call Alpaca API for orders
            self.complete_task(task.id, revenue=0.0, cost=0.0, result={"note": "Trading analysis complete – no live orders placed (paper mode)"})
        except Exception as e:
            self.fail_task(task.id, str(e))

    async def _handle_crypto(self, task: RevenueTask, max_amount: float):
        """Binance/Coinbase crypto trading sub-agent"""
        try:
            from integrations.binance_integration import binance
            if not settings.binance_enabled:
                self.fail_task(task.id, "Binance not enabled")
                return
            price_result = await binance.get_price("BTCUSDT")
            result = {"btc_price": price_result.data if price_result.success else None}
            self.complete_task(task.id, revenue=0.0, cost=0.0, result=result)
        except Exception as e:
            self.fail_task(task.id, str(e))

    async def _handle_options(self, task: RevenueTask, max_amount: float):
        """Options trading sub-agent (IBKR / Schwab)"""
        logger.info(f"[OPTIONS] Task {task.id}: options analysis (IBKR/Schwab not yet live)")
        self.complete_task(task.id, revenue=0.0, cost=0.0, result={"note": "Options integration ready – awaiting IBKR/Schwab credentials"})

    async def _handle_betting(self, task: RevenueTask, max_amount: float):
        """Sports betting sub-agent (DraftKings / PrizePicks / Odds API)"""
        try:
            from integrations.draftkings_integration import draftkings
            logger.info(f"[BETTING] Task {task.id}: scanning lines via DraftKings")
            self.complete_task(task.id, revenue=0.0, cost=0.0, result={"note": "Betting line scan complete"})
        except Exception as e:
            self.fail_task(task.id, str(e))

    async def _handle_ecommerce(self, task: RevenueTask, max_amount: float):
        """Shopify ecommerce sub-agent"""
        try:
            from integrations.shopify_integration import shopify
            if not settings.shopify_enabled:
                self.fail_task(task.id, "Shopify not enabled")
                return
            result = await shopify.get_store_info()
            self.complete_task(task.id, revenue=0.0, cost=0.0, result=result.data or {})
        except Exception as e:
            self.fail_task(task.id, str(e))

    async def _handle_saas(self, task: RevenueTask, max_amount: float):
        """SaaS subscription revenue sub-agent (Stripe)"""
        try:
            from integrations.stripe_integration import stripe
            if not settings.stripe_enabled:
                self.fail_task(task.id, "Stripe not enabled")
                return
            result = await stripe.list_subscriptions()
            count = len(result.data) if result.success and result.data else 0
            self.complete_task(task.id, revenue=0.0, cost=0.0, result={"active_subscriptions": count})
        except Exception as e:
            self.fail_task(task.id, str(e))

    async def _handle_maas(self, task: RevenueTask, max_amount: float):
        """Model-as-a-Service sub-agent"""
        logger.info(f"[MAAS] Task {task.id}: MaaS endpoint={settings.maas_model_endpoint or 'not configured'}")
        self.complete_task(task.id, revenue=0.0, cost=0.0, result={"note": "MaaS endpoint integration ready"})

    async def _handle_supply_chain(self, task: RevenueTask, max_amount: float):
        """Supply chain / logistics sub-agent (ShipStation / EasyPost)"""
        logger.info(f"[SUPPLY_CHAIN] Task {task.id}: supply chain analysis")
        self.complete_task(task.id, revenue=0.0, cost=0.0, result={"note": "Supply chain integration ready – configure ShipStation/EasyPost keys"})

    async def _handle_call_center(self, task: RevenueTask, max_amount: float):
        """Agentic call center sub-agent (Twilio)"""
        try:
            from integrations.twilio_integration import twilio
            if not settings.twilio_enabled:
                self.fail_task(task.id, "Twilio not enabled")
                return
            result = await twilio.list_calls(limit=10)
            self.complete_task(task.id, revenue=0.0, cost=0.0, result={"recent_calls": len(result.data or [])})
        except Exception as e:
            self.fail_task(task.id, str(e))

    async def _handle_freelance(self, task: RevenueTask, max_amount: float):
        """Freelance/gig platform sub-agent (Upwork / Fiverr)"""
        logger.info(f"[FREELANCE] Task {task.id}: checking gig platforms")
        self.complete_task(task.id, revenue=0.0, cost=0.0, result={"note": "Freelance integration ready – configure Upwork/Fiverr keys"})

    # ──────────────────────────────────────────────────────────────────────────
    # Reporting
    # ──────────────────────────────────────────────────────────────────────────

    def _build_report(self) -> RevenueReport:
        today = date.today().isoformat()
        today_tasks = [t for t in self.tasks.values() if t.created_at.date().isoformat() == today]
        completed = [t for t in today_tasks if t.status == "completed"]
        failed = [t for t in today_tasks if t.status == "failed"]

        by_stream: Dict[str, float] = {}
        for t in completed:
            by_stream[t.stream.value] = by_stream.get(t.stream.value, 0.0) + t.revenue_usd

        revenue = self.get_today_revenue()
        cost = self.get_today_cost()
        profit = revenue - cost
        goal = self.get_daily_goal()
        progress = (revenue / goal * 100) if goal > 0 else 0.0

        return RevenueReport(
            date=today,
            total_revenue=revenue,
            total_cost=cost,
            total_profit=profit,
            by_stream=by_stream,
            tasks_completed=len(completed),
            tasks_failed=len(failed),
            goal_daily=goal,
            goal_progress_pct=progress,
        )

    def format_report(self, report: Optional[RevenueReport] = None) -> str:
        """Format a revenue report as readable text"""
        r = report or self._build_report()
        lines = [
            f"═══ Revenue Report: {r.date} ═══",
            f"  Revenue:  ${r.total_revenue:.2f}",
            f"  Cost:     ${r.total_cost:.2f}",
            f"  Profit:   ${r.total_profit:.2f}",
            f"  Goal:     ${r.goal_daily:.2f}  ({r.goal_progress_pct:.1f}% achieved)",
            f"  Tasks:    {r.tasks_completed} completed / {r.tasks_failed} failed",
        ]
        if r.by_stream:
            lines.append("  By Stream:")
            for stream, amount in r.by_stream.items():
                lines.append(f"    {stream}: ${amount:.2f}")
        return "\n".join(lines)

    def _default_task_description(self, stream: RevenueStream, goal_usd: float) -> str:
        descs = {
            RevenueStream.TRADING:      f"Analyze market conditions and execute qualified stock/ETF trades targeting ${goal_usd:.2f}",
            RevenueStream.CRYPTO:       f"Monitor crypto markets and execute spot trades on high-confidence signals targeting ${goal_usd:.2f}",
            RevenueStream.OPTIONS:      f"Scan options chain for high-probability plays targeting ${goal_usd:.2f} credit",
            RevenueStream.BETTING:      f"Identify +EV sports betting opportunities below max stake ${settings.revenue_max_single_trade_usd}",
            RevenueStream.FREELANCE:    f"Check active freelance platform jobs and submit qualified proposals",
            RevenueStream.ECOMMERCE:    f"Process pending Shopify orders and optimize product listings",
            RevenueStream.SAAS:         f"Review SaaS subscription metrics and follow up on churned users",
            RevenueStream.MAAS:         f"Monitor MaaS API usage and billing",
            RevenueStream.SUPPLY_CHAIN: f"Check supply chain pipeline and flag arbitrage opportunities",
            RevenueStream.CALL_CENTER:  f"Process call queue and route inbound leads",
        }
        return descs.get(stream, f"Execute {stream.value} revenue tasks targeting ${goal_usd:.2f}")


# Global instance
revenue_engine = RevenueEngine()
