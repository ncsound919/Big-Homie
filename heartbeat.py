"""
Autonomous Heartbeat System
Periodic wake-up for proactive task execution and self-improvement
"""
import asyncio
import threading
from datetime import datetime, time, timedelta
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
from config import settings
from memory import memory
from router import router, AgentRole
from log_review import log_reviewer

class HeartbeatState(str, Enum):
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"

@dataclass
class HeartbeatConfig:
    """Configuration for heartbeat system"""
    enabled: bool = True
    interval_minutes: int = 45
    quiet_hours_start: time = time(23, 0)
    quiet_hours_end: time = time(6, 0)
    max_autonomous_cost: float = 5.0  # USD per day
    active_hours_only: bool = True
    notification_callback: Optional[Callable] = None

@dataclass
class HeartbeatResult:
    """Result of a heartbeat cycle"""
    timestamp: datetime
    duration_seconds: float
    system_health: Dict[str, Any]
    action_items_found: List[Dict]
    autonomous_actions: List[Dict]
    notifications: List[str]
    cost_incurred: float
    errors: List[str] = field(default_factory=list)

class HeartbeatSystem:
    """
    Autonomous heartbeat system that wakes up periodically to:
    - Check system health
    - Scan for action items
    - Execute autonomous tasks
    - Review logs and self-improve
    - Notify user of important updates
    """

    def __init__(self, config: Optional[HeartbeatConfig] = None):
        self.config = config or HeartbeatConfig()
        self.state = HeartbeatState.STOPPED
        self.heartbeat_count = 0
        self.daily_cost = 0.0
        self.last_reset = datetime.now().date()
        self.thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        # Load SOUL and HEARTBEAT configuration
        self.load_soul()

    def load_soul(self):
        """Load SOUL.md for persistent identity"""
        try:
            from pathlib import Path
            soul_path = Path(__file__).parent / "SOUL.md"
            if soul_path.exists():
                with open(soul_path) as f:
                    self.soul = f.read()
                    logger.info("SOUL loaded successfully")
            else:
                self.soul = "Big Homie - Autonomous AI Agent"
        except Exception as e:
            logger.error(f"Failed to load SOUL: {e}")
            self.soul = "Big Homie - Autonomous AI Agent"

    def start(self):
        """Start the heartbeat system in background thread"""
        if self.state == HeartbeatState.RUNNING:
            logger.warning("Heartbeat already running")
            return

        self.state = HeartbeatState.RUNNING
        self.stop_event.clear()

        self.thread = threading.Thread(target=self._run_heartbeat_loop, daemon=True)
        self.thread.start()

        logger.info(f"🫀 Heartbeat started (interval: {self.config.interval_minutes} minutes)")

    def pause(self):
        """Pause heartbeat temporarily"""
        self.state = HeartbeatState.PAUSED
        logger.info("Heartbeat paused")

    def resume(self):
        """Resume paused heartbeat"""
        if self.state == HeartbeatState.PAUSED:
            self.state = HeartbeatState.RUNNING
            logger.info("Heartbeat resumed")

    def stop(self):
        """Stop heartbeat completely"""
        self.state = HeartbeatState.STOPPED
        self.stop_event.set()

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)

        logger.info("Heartbeat stopped")

    def _run_heartbeat_loop(self):
        """Main heartbeat loop running in background thread"""
        while not self.stop_event.is_set():
            try:
                # Check if should run this heartbeat
                if self.state == HeartbeatState.RUNNING and self._should_run_now():
                    # Execute heartbeat
                    asyncio.run(self._execute_heartbeat())

                # Sleep until next check (check every minute)
                self.stop_event.wait(60)

            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                # Continue running despite errors

    def _should_run_now(self) -> bool:
        """Determine if heartbeat should run now"""
        now = datetime.now()

        # Reset daily cost counter if new day
        if now.date() > self.last_reset:
            self.daily_cost = 0.0
            self.last_reset = now.date()

        # Check cost limit
        if self.daily_cost >= self.config.max_autonomous_cost:
            logger.warning(f"Daily autonomous cost limit reached: ${self.daily_cost:.2f}")
            return False

        # Check quiet hours
        if self.config.active_hours_only:
            current_time = now.time()
            if self._is_quiet_hours(current_time):
                return False

        # Check interval (simple version - could be more sophisticated)
        # For now, just check if we haven't run recently
        last_heartbeat = memory.get_preference("last_heartbeat_time")
        if last_heartbeat:
            last_time = datetime.fromisoformat(last_heartbeat)
            elapsed = (now - last_time).total_seconds() / 60
            if elapsed < self.config.interval_minutes:
                return False

        return True

    def _is_quiet_hours(self, current_time: time) -> bool:
        """Check if current time is in quiet hours"""
        start = self.config.quiet_hours_start
        end = self.config.quiet_hours_end

        if start < end:
            return start <= current_time < end
        else:  # Crosses midnight
            return current_time >= start or current_time < end

    async def _execute_heartbeat(self) -> HeartbeatResult:
        """Execute one heartbeat cycle"""
        start_time = datetime.now()
        self.heartbeat_count += 1

        logger.info(f"🫀 Heartbeat #{self.heartbeat_count} starting...")

        result = HeartbeatResult(
            timestamp=start_time,
            duration_seconds=0,
            system_health={},
            action_items_found=[],
            autonomous_actions=[],
            notifications=[],
            cost_incurred=0
        )

        try:
            # 1. System Health Check
            result.system_health = await self._check_system_health()

            # 2. Scan for Action Items
            result.action_items_found = await self._scan_action_items()

            # 3. Execute Autonomous Tasks
            if result.action_items_found:
                result.autonomous_actions = await self._execute_autonomous_tasks(
                    result.action_items_found
                )
                # Sum actual costs incurred by autonomous task execution
                result.cost_incurred = sum(
                    action.get("cost", 0.0)
                    for action in result.autonomous_actions
                    if isinstance(action, dict)
                )

            # 4. Daily Log Review (if scheduled)
            if self._should_review_logs():
                await self._review_logs()

            # 5. Dream System — run overnight memory consolidation if conditions are right
            await self._check_dream_system()

            # 6. Notify KAIROS daemon that heartbeat ran (keeps activity timestamp fresh)
            await self._notify_kairos("heartbeat", {"count": self.heartbeat_count})

            # 7. Generate Notifications
            result.notifications = self._generate_notifications(result)

            # Update preferences
            memory.set_preference("last_heartbeat_time", start_time.isoformat())
            memory.set_preference("last_heartbeat_result", result.__dict__)
            # Record activity so dream system / KAIROS idle detection works correctly
            memory.set_preference("last_user_activity", start_time.isoformat())

        except Exception as e:
            logger.error(f"Heartbeat execution error: {e}")
            result.errors.append(str(e))

        # Calculate duration and cost
        result.duration_seconds = (datetime.now() - start_time).total_seconds()
        self.daily_cost += result.cost_incurred

        logger.info(
            f"🫀 Heartbeat #{self.heartbeat_count} complete "
            f"({result.duration_seconds:.1f}s, ${result.cost_incurred:.4f})"
        )

        # Send notifications if callback provided
        if self.config.notification_callback and result.notifications:
            for notification in result.notifications:
                self.config.notification_callback(notification)

        return result

    async def _check_system_health(self) -> Dict[str, Any]:
        """Check system health and return status"""
        health = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "memory_facts": 0,
            "active_skills": 0,
            "cost_budget_remaining": 0,
        }

        try:
            # Check memory system
            facts = memory.search_memory(limit=1)
            health["memory_facts"] = len(facts)

            skills = memory.list_skills()
            health["active_skills"] = len(skills)

            # Check cost budget
            health["cost_budget_remaining"] = (
                self.config.max_autonomous_cost - self.daily_cost
            )

            # All checks passed
            health["status"] = "healthy"

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health["status"] = "degraded"
            health["error"] = str(e)

        return health

    async def _scan_action_items(self) -> List[Dict]:
        """Scan for action items requiring attention"""
        action_items = []

        try:
            # Check for pending tasks in memory
            pending_tasks = memory.get_preference("pending_tasks", [])
            if pending_tasks:
                action_items.extend([
                    {"type": "pending_task", "data": task}
                    for task in pending_tasks
                ])

            # Check for high-priority memories
            important_memories = memory.search_memory(limit=5)
            for mem in important_memories:
                if mem.get("importance", 0) >= 8:
                    action_items.append({
                        "type": "important_memory",
                        "data": mem
                    })

            # Could add more sources:
            # - Email scanning (if configured)
            # - Market alerts (if configured)
            # - Scheduled reminders
            # - Error log patterns

        except Exception as e:
            logger.error(f"Action item scanning failed: {e}")

        return action_items

    async def _execute_autonomous_tasks(self, action_items: List[Dict]) -> List[Dict]:
        """Execute autonomous tasks based on action items"""
        actions_taken = []

        for item in action_items[:3]:  # Limit to 3 per heartbeat
            try:
                # Use router for intelligent task execution
                task_description = f"Process action item: {item['type']}"

                decision, result = await router.execute_with_routing(
                    task=task_description,
                    context={"autonomous": True, "action_item": item},
                    prefer_cost=True  # Prefer cheaper models for autonomous tasks
                )

                actions_taken.append({
                    "item": item,
                    "result": result.get("content", ""),
                    "cost": decision.estimated_cost,
                    "model": decision.model
                })

            except Exception as e:
                logger.error(f"Autonomous task execution failed: {e}")

                # Capture screenshot if enabled and this is a UI-related error
                screenshot_path = None
                if settings.auto_screenshot_on_error and settings.enable_vision:
                    try:
                        screenshot_path = await self._capture_error_screenshot(str(e))

                        # Analyze screenshot with vision if captured
                        if screenshot_path:
                            from vision_analysis import vision_analyzer
                            analysis = await vision_analyzer.analyze_screenshot_error(
                                screenshot_path=screenshot_path,
                                error_message=str(e),
                                context={"action_item": item}
                            )

                            if analysis.success:
                                logger.info(f"Vision analysis: {analysis.analysis[:200]}...")

                    except Exception as vision_error:
                        logger.warning(f"Screenshot/vision analysis failed: {vision_error}")

                actions_taken.append({
                    "item": item,
                    "error": str(e),
                    "screenshot": screenshot_path
                })

        return actions_taken

    async def _capture_error_screenshot(self, error_msg: str) -> Optional[str]:
        """Capture screenshot when error occurs"""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_dir = settings.data_dir / "screenshots"
            screenshot_dir.mkdir(exist_ok=True)

            screenshot_path = screenshot_dir / f"error_{timestamp}.png"

            # Try to capture browser screenshot if browser is active
            from browser_skill import browser_skill
            if browser_skill.page:
                path = await browser_skill.screenshot(str(screenshot_path))
                logger.info(f"Error screenshot saved: {path}")
                return path

        except Exception as e:
            logger.warning(f"Failed to capture screenshot: {e}")

        return None

    def _should_review_logs(self) -> bool:
        """Check if it's time for daily log review"""
        last_review = memory.get_preference("last_log_review")
        if not last_review:
            return True

        last_review_date = datetime.fromisoformat(last_review).date()
        return datetime.now().date() > last_review_date

    async def _review_logs(self):
        """Review error logs and suggest improvements using LogReviewSystem"""
        logger.info("🔍 Starting daily log review...")

        try:
            # Perform comprehensive log analysis
            analysis = log_reviewer.perform_daily_review()

            # Export analysis report
            report_path = log_reviewer.export_analysis(analysis)

            # If there are critical patterns, use Architect to propose fixes
            if analysis.error_patterns:
                critical_patterns = [p for p in analysis.error_patterns if p.severity == "critical"]

                if critical_patterns:
                    fix_task = f"""Review these critical error patterns and propose code fixes:

{[{"pattern": p.pattern, "count": p.count, "category": p.category} for p in critical_patterns[:3]]}

Provide specific code changes or configuration updates to resolve these issues."""

                    decision, result = await router.execute_with_routing(
                        task=fix_task,
                        context={"requires_reasoning": True}
                    )

                    # Store fix suggestions
                    memory.store(
                        key=f"critical_fixes_{datetime.now().date()}",
                        value=result.get("content", ""),
                        category="self_improvement",
                        importance=9
                    )

            # Store analysis summary
            memory.store(
                key=f"log_review_{datetime.now().date()}",
                value=f"Review complete. Errors: {analysis.total_errors}, Success Rate: {analysis.success_metrics['success_rate']}%",
                category="self_improvement",
                importance=7
            )

            memory.set_preference("last_log_review", datetime.now().isoformat())

        except Exception as e:
            logger.error(f"Log review failed: {e}")

    def _generate_notifications(self, result: HeartbeatResult) -> List[str]:
        """Generate user notifications based on heartbeat results"""
        notifications = []

        # System health alerts
        if result.system_health.get("status") != "healthy":
            notifications.append(
                f"⚠️ System health degraded: {result.system_health.get('error', 'Unknown')}"
            )

        # Action items found
        if len(result.action_items_found) > 0:
            notifications.append(
                f"📥 Found {len(result.action_items_found)} action items"
            )

        # Autonomous actions completed
        if len(result.autonomous_actions) > 0:
            successful = len([a for a in result.autonomous_actions if "error" not in a])
            if successful > 0:
                notifications.append(
                    f"✅ Completed {successful} autonomous tasks"
                )

        # Cost warnings
        remaining = self.config.max_autonomous_cost - self.daily_cost
        if remaining < 1.0:
            notifications.append(
                f"💰 Low autonomous budget: ${remaining:.2f} remaining"
            )

        return notifications

    async def _check_dream_system(self):
        """Check if dream system should run during heartbeat"""
        try:
            from dream_system import dream_system, should_dream

            if should_dream():
                logger.info("💤 Conditions right for dream cycle, initiating...")
                cycle = await dream_system.dream()
                return {
                    "dream_cycle_run": True,
                    "memories_processed": cycle.memories_processed,
                    "memories_consolidated": cycle.memories_consolidated
                }
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Dream system check failed: {e}")

        return {"dream_cycle_run": False}

    async def _notify_kairos(self, action: str, data: Optional[Dict] = None):
        """Notify KAIROS daemon of heartbeat events"""
        try:
            from kairos_daemon import kairos

            if kairos.state.value != "stopped":
                kairos.record_user_activity()  # Heartbeat counts as activity
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"KAIROS notification skipped: {e}")


# Global heartbeat instance
heartbeat = HeartbeatSystem()
