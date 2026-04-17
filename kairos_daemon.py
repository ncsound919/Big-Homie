"""
KAIROS - Persistent Always-On Autonomous Daemon Mode
A background agent that proactively performs tasks and memory consolidation
even when the user is idle.

KAIROS (Knowledge-Augmented Intelligent Responsive Operating System) operates
as a continuous background process that:
- Monitors system state and user context
- Proactively executes scheduled and triggered tasks
- Consolidates memory during idle periods
- Manages resource allocation for background operations
"""

import asyncio
import signal
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from datetime import time as time_of_day
from enum import Enum
from typing import Any, Callable, Optional

from loguru import logger

from config import settings
from memory import memory


class DaemonState(str, Enum):
    """State of the KAIROS daemon"""

    INITIALIZING = "initializing"
    RUNNING = "running"
    IDLE = "idle"
    PROCESSING = "processing"
    CONSOLIDATING = "consolidating"
    PAUSED = "paused"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"


class TaskPriority(str, Enum):
    """Priority levels for daemon tasks"""

    CRITICAL = "critical"  # Execute immediately
    HIGH = "high"  # Execute as soon as possible
    NORMAL = "normal"  # Standard scheduling
    LOW = "low"  # Execute when idle
    BACKGROUND = "background"  # Execute only during consolidation periods


@dataclass
class DaemonTask:
    """A task to be executed by the daemon"""

    id: str
    name: str
    description: str
    priority: TaskPriority
    handler: Optional[Callable] = None
    schedule_cron: Optional[str] = None  # Cron-like schedule
    interval_seconds: Optional[int] = None  # Interval-based schedule
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class DaemonMetrics:
    """Metrics for daemon performance tracking"""

    uptime_seconds: float = 0.0
    tasks_executed: int = 0
    tasks_failed: int = 0
    memory_consolidations: int = 0
    idle_time_seconds: float = 0.0
    active_time_seconds: float = 0.0
    total_cost: float = 0.0
    last_user_activity: Optional[datetime] = None
    current_state: DaemonState = DaemonState.STOPPED


def _get_kairos_setting(name: str, default: Any) -> Any:
    """Read a KAIROS setting from config, falling back to the existing default."""
    return getattr(settings, name, default)


def _get_kairos_time_setting(name: str, default: time_of_day) -> time_of_day:
    """Read a KAIROS time setting from config and coerce common string formats."""
    value = getattr(settings, name, default)

    if isinstance(value, time_of_day):
        return value

    if isinstance(value, str):
        try:
            return datetime.strptime(value.strip(), "%H:%M").time()
        except ValueError:
            return default

    return default


@dataclass
class KairosConfig:
    """Configuration for KAIROS daemon"""

    enabled: bool = field(default_factory=lambda: _get_kairos_setting("kairos_enabled", True))
    idle_threshold_seconds: int = field(
        default_factory=lambda: _get_kairos_setting("kairos_idle_threshold_seconds", 300)
    )  # 5 minutes of no activity = idle
    consolidation_interval_seconds: int = field(
        default_factory=lambda: _get_kairos_setting("kairos_consolidation_interval_seconds", 3600)
    )  # Consolidate every hour when idle
    max_background_cost_per_hour: float = field(
        default_factory=lambda: _get_kairos_setting("kairos_max_background_cost_per_hour", 1.0)
    )  # USD limit per hour
    max_concurrent_tasks: int = field(
        default_factory=lambda: _get_kairos_setting("kairos_max_concurrent_tasks", 3)
    )
    quiet_hours_enabled: bool = field(
        default_factory=lambda: _get_kairos_setting("kairos_quiet_hours_enabled", True)
    )
    quiet_hours_start: time_of_day = field(
        default_factory=lambda: _get_kairos_time_setting(
            "kairos_quiet_hours_start", time_of_day(23, 0)
        )
    )
    quiet_hours_end: time_of_day = field(
        default_factory=lambda: _get_kairos_time_setting(
            "kairos_quiet_hours_end", time_of_day(6, 0)
        )
    )
    priority_task_timeout: int = field(
        default_factory=lambda: _get_kairos_setting("kairos_priority_task_timeout", 300)
    )  # 5 min for critical tasks
    normal_task_timeout: int = field(
        default_factory=lambda: _get_kairos_setting("kairos_normal_task_timeout", 600)
    )  # 10 min for normal tasks
    enable_auto_consolidation: bool = field(
        default_factory=lambda: _get_kairos_setting("kairos_enable_auto_consolidation", True)
    )
    enable_proactive_tasks: bool = field(
        default_factory=lambda: _get_kairos_setting("kairos_enable_proactive_tasks", True)
    )


class KairosDaemon:
    """
    KAIROS - Persistent Autonomous Daemon

    Operates as a background agent that:
    1. Runs continuously in the background
    2. Monitors for tasks to execute proactively
    3. Consolidates memory during idle periods
    4. Manages resource allocation intelligently
    5. Integrates with heartbeat for periodic checks
    """

    def __init__(self, config: Optional[KairosConfig] = None):
        self.config = config or KairosConfig()
        self.state = DaemonState.STOPPED
        self.metrics = DaemonMetrics()
        self.start_time: Optional[datetime] = None

        # Task management
        self.scheduled_tasks: dict[str, DaemonTask] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.running_tasks: set[str] = set()

        # Threading
        self.daemon_thread: Optional[threading.Thread] = None
        self.event_loop: Optional[asyncio.AbstractEventLoop] = None
        self.stop_event = threading.Event()

        # Callbacks
        self.on_state_change: Optional[Callable[[DaemonState], None]] = None
        self.on_task_complete: Optional[Callable[[DaemonTask, Any], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None

        # Cost tracking
        self.hourly_cost = 0.0
        self.hourly_cost_reset_time = datetime.now()

        # Initialize built-in tasks
        self._register_builtin_tasks()

        logger.info("KAIROS daemon initialized")

    def _register_builtin_tasks(self):
        """Register built-in daemon tasks"""
        # Memory consolidation task
        self.register_task(
            DaemonTask(
                id="memory_consolidation",
                name="Memory Consolidation",
                description="Consolidate and optimize memory storage",
                priority=TaskPriority.BACKGROUND,
                interval_seconds=3600,  # Every hour
            )
        )

        # System health check
        self.register_task(
            DaemonTask(
                id="system_health_check",
                name="System Health Check",
                description="Verify system health and resource availability",
                priority=TaskPriority.NORMAL,
                interval_seconds=300,  # Every 5 minutes
            )
        )

        # Skill optimization
        self.register_task(
            DaemonTask(
                id="skill_optimization",
                name="Skill Optimization",
                description="Optimize learned skills based on usage patterns",
                priority=TaskPriority.LOW,
                interval_seconds=7200,  # Every 2 hours
            )
        )

    def register_task(self, task: DaemonTask):
        """Register a task with the daemon"""
        self.scheduled_tasks[task.id] = task

        # Calculate next run time
        if task.interval_seconds:
            task.next_run = datetime.now() + timedelta(seconds=task.interval_seconds)

        logger.info(f"Task registered: {task.name} ({task.id})")

    def unregister_task(self, task_id: str):
        """Unregister a task from the daemon"""
        if task_id in self.scheduled_tasks:
            del self.scheduled_tasks[task_id]
            logger.info(f"Task unregistered: {task_id}")

    def start(self):
        """Start the KAIROS daemon"""
        if self.state in [DaemonState.RUNNING, DaemonState.IDLE, DaemonState.PROCESSING]:
            logger.warning("KAIROS daemon already running")
            return

        self._set_state(DaemonState.INITIALIZING)
        self.stop_event.clear()
        self.start_time = datetime.now()

        # Start daemon thread
        self.daemon_thread = threading.Thread(
            target=self._daemon_main_loop, name="KAIROS-Daemon", daemon=True
        )
        self.daemon_thread.start()

        logger.info("🔮 KAIROS daemon started - always-on autonomous mode active")

    def stop(self):
        """Stop the KAIROS daemon gracefully"""
        if self.state == DaemonState.STOPPED:
            return

        self._set_state(DaemonState.SHUTTING_DOWN)
        self.stop_event.set()

        # Wait for daemon thread to finish
        if self.daemon_thread and self.daemon_thread.is_alive():
            self.daemon_thread.join(timeout=10)

        self._set_state(DaemonState.STOPPED)
        self._update_metrics()

        logger.info("🔮 KAIROS daemon stopped")

    def pause(self):
        """Pause daemon processing"""
        if self.state in [DaemonState.RUNNING, DaemonState.IDLE]:
            self._set_state(DaemonState.PAUSED)
            logger.info("KAIROS daemon paused")

    def resume(self):
        """Resume daemon processing"""
        if self.state == DaemonState.PAUSED:
            self._set_state(DaemonState.RUNNING)
            logger.info("KAIROS daemon resumed")

    def record_user_activity(self):
        """Record user activity to track idle time"""
        self.metrics.last_user_activity = datetime.now()

    def queue_task(self, task_id: str, priority_override: Optional[TaskPriority] = None):
        """Queue a task for immediate execution"""
        if task_id not in self.scheduled_tasks:
            logger.warning(f"Unknown task: {task_id}")
            return

        task = self.scheduled_tasks[task_id]
        if priority_override:
            task = DaemonTask(**{**task.__dict__, "priority": priority_override})

        if self.event_loop:
            asyncio.run_coroutine_threadsafe(self.task_queue.put(task), self.event_loop)
            logger.info(f"Task queued: {task.name}")

    def get_status(self) -> dict[str, Any]:
        """Get current daemon status"""
        self._update_metrics()
        return {
            "state": self.state.value,
            "uptime_seconds": self.metrics.uptime_seconds,
            "tasks_executed": self.metrics.tasks_executed,
            "tasks_failed": self.metrics.tasks_failed,
            "memory_consolidations": self.metrics.memory_consolidations,
            "idle_time_seconds": self.metrics.idle_time_seconds,
            "hourly_cost": self.hourly_cost,
            "scheduled_tasks": len(self.scheduled_tasks),
            "running_tasks": len(self.running_tasks),
            "last_user_activity": self.metrics.last_user_activity.isoformat()
            if self.metrics.last_user_activity
            else None,
        }

    def _set_state(self, new_state: DaemonState):
        """Set daemon state and trigger callback"""
        old_state = self.state
        self.state = new_state
        self.metrics.current_state = new_state

        if self.on_state_change and old_state != new_state:
            try:
                self.on_state_change(new_state)
            except Exception as e:
                logger.error(f"State change callback error: {e}")

    def _update_metrics(self):
        """Update daemon metrics"""
        if self.start_time:
            self.metrics.uptime_seconds = (datetime.now() - self.start_time).total_seconds()

    def _is_idle(self) -> bool:
        """Check if user is idle"""
        if not self.metrics.last_user_activity:
            return True

        idle_seconds = (datetime.now() - self.metrics.last_user_activity).total_seconds()
        return idle_seconds > self.config.idle_threshold_seconds

    def _is_quiet_hours(self) -> bool:
        """Check if current time is in quiet hours"""
        if not self.config.quiet_hours_enabled:
            return False

        current_time = datetime.now().time()
        start = self.config.quiet_hours_start
        end = self.config.quiet_hours_end

        if start < end:
            return start <= current_time < end
        else:  # Crosses midnight
            return current_time >= start or current_time < end

    def _check_cost_limit(self, estimated_cost: float = 0.0) -> bool:
        """Check if within hourly cost limit"""
        # Reset hourly cost if hour has passed
        if (datetime.now() - self.hourly_cost_reset_time).total_seconds() >= 3600:
            self.hourly_cost = 0.0
            self.hourly_cost_reset_time = datetime.now()

        return (self.hourly_cost + estimated_cost) <= self.config.max_background_cost_per_hour

    def _daemon_main_loop(self):
        """Main daemon loop running in background thread"""
        # Create event loop for this thread
        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)

        try:
            self.event_loop.run_until_complete(self._async_daemon_loop())
        except Exception as e:
            logger.error(f"KAIROS daemon error: {e}")
            if self.on_error:
                self.on_error(e)
        finally:
            self.event_loop.close()
            self.event_loop = None

    async def _async_daemon_loop(self):
        """Async main loop for the daemon"""
        self._set_state(DaemonState.RUNNING)

        while not self.stop_event.is_set():
            try:
                # Determine current mode based on activity
                is_idle = self._is_idle()
                is_quiet = self._is_quiet_hours()

                if self.state == DaemonState.PAUSED:
                    await asyncio.sleep(1)
                    continue

                if is_idle and self.config.enable_auto_consolidation:
                    self._set_state(DaemonState.IDLE)

                    # Check for consolidation
                    await self._maybe_run_consolidation()

                # Process queued tasks
                await self._process_task_queue()

                # Check scheduled tasks
                await self._check_scheduled_tasks(is_idle, is_quiet)

                # Brief sleep before next iteration
                await asyncio.sleep(1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Daemon loop error: {e}")
                if self.on_error:
                    self.on_error(e)
                await asyncio.sleep(5)  # Back off on error

    async def _process_task_queue(self):
        """Process tasks from the queue"""
        while (
            not self.task_queue.empty()
            and len(self.running_tasks) < self.config.max_concurrent_tasks
        ):
            try:
                task = await asyncio.wait_for(self.task_queue.get(), timeout=0.1)
                asyncio.create_task(self._execute_task(task))
            except asyncio.TimeoutError:
                break
            except Exception as e:
                logger.error(f"Task queue processing error: {e}")

    async def _check_scheduled_tasks(self, is_idle: bool, is_quiet: bool):
        """Check and execute scheduled tasks"""
        now = datetime.now()

        for task in self.scheduled_tasks.values():
            if not task.enabled:
                continue

            # Skip if task is already running
            if task.id in self.running_tasks:
                continue

            # Check if it's time to run
            if task.next_run and now >= task.next_run:
                # Apply priority filters
                if task.priority == TaskPriority.BACKGROUND and not is_idle:
                    continue  # Background tasks only run when idle

                if is_quiet and task.priority not in [TaskPriority.CRITICAL]:
                    continue  # Skip non-critical during quiet hours

                # Check cost limit
                if not self._check_cost_limit():
                    logger.warning("Hourly cost limit reached, skipping task")
                    continue

                # Queue the task
                await self.task_queue.put(task)

    async def _execute_task(self, task: DaemonTask):
        """Execute a daemon task"""
        self.running_tasks.add(task.id)
        self._set_state(DaemonState.PROCESSING)

        try:
            logger.info(f"🔮 Executing task: {task.name}")

            # Determine timeout based on priority
            timeout = (
                self.config.priority_task_timeout
                if task.priority in [TaskPriority.CRITICAL, TaskPriority.HIGH]
                else self.config.normal_task_timeout
            )

            # Execute handler if provided
            result = None
            if task.handler:
                if asyncio.iscoroutinefunction(task.handler):
                    result = await asyncio.wait_for(task.handler(), timeout=timeout)
                else:
                    result = await asyncio.to_thread(task.handler)
            else:
                # Execute built-in task logic
                result = await self._execute_builtin_task(task)

            # Track per-task cost and update hourly budget
            task_cost = 0.0
            if isinstance(result, dict):
                task_cost = float(result.get("cost", 0.0) or 0.0)
            self.hourly_cost += task_cost
            self.metrics.total_cost += task_cost

            # Update task stats
            task.last_run = datetime.now()
            task.run_count += 1

            # Schedule next run
            if task.interval_seconds:
                task.next_run = datetime.now() + timedelta(seconds=task.interval_seconds)

            self.metrics.tasks_executed += 1

            # Trigger callback
            if self.on_task_complete:
                self.on_task_complete(task, result)

            logger.info(f"✅ Task completed: {task.name} (cost: ${task_cost:.4f})")

        except asyncio.TimeoutError:
            logger.warning(f"Task timed out: {task.name}")
            task.error_count += 1
            self.metrics.tasks_failed += 1

        except Exception as e:
            logger.error(f"Task execution error: {task.name} - {e}")
            task.error_count += 1
            self.metrics.tasks_failed += 1

            if self.on_error:
                self.on_error(e)

        finally:
            self.running_tasks.discard(task.id)
            if not self.running_tasks:
                self._set_state(DaemonState.IDLE if self._is_idle() else DaemonState.RUNNING)

    async def _execute_builtin_task(self, task: DaemonTask) -> Any:
        """Execute built-in task logic"""
        if task.id == "memory_consolidation":
            return await self._run_memory_consolidation()

        elif task.id == "system_health_check":
            return await self._run_health_check()

        elif task.id == "skill_optimization":
            return await self._run_skill_optimization()

        else:
            logger.warning(f"No handler for task: {task.id}")
            return None

    async def _run_memory_consolidation(self) -> dict[str, Any]:
        """Run memory consolidation process"""
        logger.info("🧠 Starting memory consolidation...")

        results = {
            "timestamp": datetime.now().isoformat(),
            "facts_processed": 0,
            "facts_consolidated": 0,
            "skills_optimized": 0,
        }

        try:
            # Get all memory facts
            all_facts = memory.search_memory(limit=100)
            results["facts_processed"] = len(all_facts)

            # Analyze access patterns and importance
            for fact in all_facts:
                # Decay importance for unused memories
                if fact.get("access_count", 0) < 2:
                    importance = fact.get("importance", 5)
                    if importance > 1:
                        memory.store(
                            key=fact["key"],
                            value=fact["value"],
                            category=fact["category"],
                            importance=importance - 1,
                        )
                        results["facts_consolidated"] += 1

            # Optimize skills based on usage
            skills = memory.list_skills()
            for skill in skills:
                if skill.get("success_count", 0) > 5:
                    results["skills_optimized"] += 1

            self.metrics.memory_consolidations += 1
            logger.info(f"Memory consolidation complete: {results}")

        except Exception as e:
            logger.error(f"Memory consolidation error: {e}")
            results["error"] = str(e)

        return results

    async def _run_health_check(self) -> dict[str, Any]:
        """Run system health check"""
        health = {"timestamp": datetime.now().isoformat(), "status": "healthy", "checks": {}}

        try:
            # Check memory system
            memory.search_memory(limit=1)
            health["checks"]["memory"] = "ok"

            # Check skills
            skills = memory.list_skills()
            health["checks"]["skills"] = f"{len(skills)} skills available"

            # Check cost budget
            remaining_budget = max(0, self.config.max_background_cost_per_hour - self.hourly_cost)
            health["checks"]["cost_budget"] = f"${remaining_budget:.2f} remaining this hour"

        except Exception as e:
            health["status"] = "degraded"
            health["error"] = str(e)

        return health

    async def _run_skill_optimization(self) -> dict[str, Any]:
        """Optimize skills based on usage patterns"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "skills_analyzed": 0,
            "skills_optimized": 0,
        }

        try:
            skills = memory.list_skills()
            results["skills_analyzed"] = len(skills)

            for skill in skills:
                # Identify high-performing skills
                success_count = skill.get("success_count", 0)
                failure_count = skill.get("failure_count", 0)
                total = success_count + failure_count
                success_rate = success_count / max(total, 1)

                if success_rate > 0.8:
                    # Mark as optimized/reliable
                    results["skills_optimized"] += 1

        except Exception as e:
            logger.error(f"Skill optimization error: {e}")
            results["error"] = str(e)

        return results

    async def _maybe_run_consolidation(self):
        """Check if memory consolidation should run"""
        consolidation_task = self.scheduled_tasks.get("memory_consolidation")
        if not consolidation_task:
            return

        if consolidation_task.id not in self.running_tasks:
            now = datetime.now()
            if consolidation_task.next_run and now >= consolidation_task.next_run:
                await self.task_queue.put(consolidation_task)


# Global KAIROS daemon instance
kairos = KairosDaemon()


def start_kairos():
    """
    Convenience function to start KAIROS daemon.

    Also registers OS signal handlers (SIGTERM/SIGINT) for graceful shutdown,
    but only when called from the main thread, because Python's signal module
    raises ValueError when used from a non-main thread.
    """
    # Register signal handlers only from the main thread to avoid ValueError
    if threading.current_thread() is threading.main_thread():
        signal.signal(signal.SIGTERM, _signal_handler)
        signal.signal(signal.SIGINT, _signal_handler)

    kairos.start()


def stop_kairos():
    """Convenience function to stop KAIROS daemon"""
    kairos.stop()


# Signal handler for graceful shutdown — registered by start_kairos() only
# from the main thread to prevent ValueError in non-main threads.
def _signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down KAIROS...")
    kairos.stop()
