"""
Environment Sensing - Tier 3 Perception
Monitor system state, file changes, API responses, and runtime errors
"""

import asyncio
import platform
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional

from loguru import logger

from config import settings


@dataclass
class SystemMetrics:
    """Current system metrics snapshot"""

    timestamp: str
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    memory_used_mb: Optional[float] = None
    memory_total_mb: Optional[float] = None
    disk_percent: Optional[float] = None
    disk_free_gb: Optional[float] = None
    python_version: str = ""
    platform: str = ""
    uptime_seconds: float = 0.0


@dataclass
class FileEvent:
    """A file system change event"""

    event_type: str  # created, modified, deleted, moved
    path: str
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EnvironmentAlert:
    """An alert from the environment sensor"""

    level: str  # info, warning, critical
    source: str
    message: str
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)


class EnvironmentSensor:
    """
    Monitors system state, file changes, API health, and runtime errors.

    Capabilities:
    - System metrics (CPU, memory, disk)
    - File system monitoring
    - API health checking
    - Runtime error tracking
    - Proactive alerting
    """

    def __init__(self):
        self.start_time = time.time()
        self.alerts: list[EnvironmentAlert] = []
        self.file_events: list[FileEvent] = []
        self.api_health: dict[str, dict] = {}
        self._watchers: dict[str, Any] = {}
        self._alert_callbacks: list[Callable] = []
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None

    # ===== System Metrics =====

    def get_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        metrics = SystemMetrics(
            timestamp=datetime.now().isoformat(),
            python_version=sys.version.split()[0],
            platform=f"{platform.system()} {platform.release()}",
            uptime_seconds=time.time() - self.start_time,
        )

        try:
            import psutil

            metrics.cpu_percent = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            metrics.memory_percent = mem.percent
            metrics.memory_used_mb = mem.used / (1024 * 1024)
            metrics.memory_total_mb = mem.total / (1024 * 1024)
            disk = psutil.disk_usage("/")
            metrics.disk_percent = disk.percent
            metrics.disk_free_gb = disk.free / (1024 * 1024 * 1024)
        except ImportError:
            # psutil not available, use basic OS methods
            metrics.platform = f"{platform.system()} {platform.release()} (limited metrics)"

        return metrics

    def check_system_health(self) -> dict[str, Any]:
        """Comprehensive system health check"""
        metrics = self.get_system_metrics()

        health = {
            "status": "healthy",
            "timestamp": metrics.timestamp,
            "metrics": {
                "cpu_percent": metrics.cpu_percent,
                "memory_percent": metrics.memory_percent,
                "disk_percent": metrics.disk_percent,
                "uptime_seconds": metrics.uptime_seconds,
            },
            "warnings": [],
            "errors": [],
        }

        # Check thresholds
        if metrics.memory_percent and metrics.memory_percent > 90:
            health["warnings"].append(f"High memory usage: {metrics.memory_percent}%")
            health["status"] = "warning"

        if metrics.disk_percent and metrics.disk_percent > 90:
            health["warnings"].append(f"Low disk space: {metrics.disk_free_gb:.1f}GB free")
            health["status"] = "warning"

        if metrics.cpu_percent and metrics.cpu_percent > 95:
            health["warnings"].append(f"High CPU usage: {metrics.cpu_percent}%")
            health["status"] = "warning"

        # Check critical services
        service_checks = self._check_critical_services()
        health["services"] = service_checks

        if any(not s["available"] for s in service_checks.values()):
            health["errors"].append("One or more critical services unavailable")
            health["status"] = "degraded"

        return health

    def _check_critical_services(self) -> dict[str, dict]:
        """Check availability of critical services"""
        services = {}

        # Check database
        try:
            from memory import memory

            memory.search_memory(limit=1)
            services["database"] = {"available": True, "latency_ms": 0}
        except Exception as e:
            services["database"] = {"available": False, "error": str(e)}

        # Check data directory
        try:
            data_dir = settings.data_dir
            if data_dir.exists():
                services["storage"] = {"available": True, "path": str(data_dir)}
            else:
                services["storage"] = {"available": False, "error": "Data directory missing"}
        except Exception as e:
            services["storage"] = {"available": False, "error": str(e)}

        return services

    # ===== File System Monitoring =====

    def watch_directory(self, path: str, callback: Optional[Callable] = None):
        """
        Start watching a directory for changes.

        Args:
            path: Directory path to watch
            callback: Optional callback for file events
        """
        try:
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer

            class EventHandler(FileSystemEventHandler):
                def __init__(self, sensor):
                    self.sensor = sensor

                def on_any_event(self, event):
                    if event.is_directory:
                        return

                    file_event = FileEvent(
                        event_type=event.event_type,
                        path=event.src_path,
                        timestamp=datetime.now().isoformat(),
                    )

                    self.sensor.file_events.append(file_event)

                    # Keep only last 1000 events
                    if len(self.sensor.file_events) > 1000:
                        self.sensor.file_events = self.sensor.file_events[-500:]

                    if callback:
                        callback(file_event)

            observer = Observer()
            observer.schedule(EventHandler(self), path, recursive=True)
            observer.start()

            self._watchers[path] = observer
            logger.info(f"Watching directory: {path}")

        except ImportError:
            logger.warning(
                "watchdog not installed - file monitoring"
                " unavailable. Install with:"
                " pip install watchdog"
            )

    def stop_watching(self, path: Optional[str] = None):
        """Stop watching a directory (or all directories)"""
        if path:
            observer = self._watchers.pop(path, None)
            if observer:
                observer.stop()
                observer.join()
        else:
            for _obs_path, observer in self._watchers.items():
                observer.stop()
                observer.join()
            self._watchers.clear()

    def get_recent_file_events(self, limit: int = 50) -> list[FileEvent]:
        """Get recent file system events"""
        return self.file_events[-limit:]

    # ===== API Health Monitoring =====

    async def check_api_health(self, name: str, url: str, timeout: float = 5.0) -> dict:
        """
        Check health of an external API endpoint.

        Args:
            name: Service name
            url: Health check URL
            timeout: Request timeout

        Returns:
            Health check result
        """
        import httpx

        result = {
            "name": name,
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "available": False,
            "latency_ms": 0,
            "status_code": None,
            "error": None,
        }

        try:
            start = time.time()
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=timeout)
                latency = (time.time() - start) * 1000

                result["available"] = response.status_code < 500
                result["latency_ms"] = round(latency, 2)
                result["status_code"] = response.status_code

        except Exception as e:
            result["error"] = str(e)

        self.api_health[name] = result

        # Create alert if service is down
        if not result["available"]:
            self._create_alert(
                "warning",
                f"api_health:{name}",
                f"Service '{name}' is unavailable: {result.get('error', 'unknown error')}",
            )

        return result

    async def check_all_apis(self) -> dict[str, dict]:
        """Check health of all configured API endpoints"""
        endpoints = []

        # Check configured providers
        if settings.anthropic_api_key:
            endpoints.append(("Anthropic", "https://api.anthropic.com/v1/messages"))
        if settings.openai_api_key:
            endpoints.append(("OpenAI", "https://api.openai.com/v1/models"))
        if settings.ollama_enabled:
            endpoints.append(("Ollama", f"{settings.ollama_base_url}/api/tags"))

        tasks = [self.check_api_health(name, url) for name, url in endpoints]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        return self.api_health

    # ===== Alert System =====

    def _create_alert(self, level: str, source: str, message: str, metadata: Optional[dict] = None):
        """Create an environment alert"""
        alert = EnvironmentAlert(
            level=level,
            source=source,
            message=message,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {},
        )

        self.alerts.append(alert)

        # Keep only last 500 alerts
        if len(self.alerts) > 500:
            self.alerts = self.alerts[-250:]

        # Notify callbacks
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")

        # Log the alert
        log_func = {"info": logger.info, "warning": logger.warning, "critical": logger.error}.get(
            level, logger.info
        )

        log_func(f"🔔 [{source}] {message}")

    def on_alert(self, callback: Callable):
        """Register an alert callback"""
        self._alert_callbacks.append(callback)

    def get_recent_alerts(
        self, limit: int = 20, level: Optional[str] = None
    ) -> list[EnvironmentAlert]:
        """Get recent alerts, optionally filtered by level"""
        alerts = self.alerts
        if level:
            alerts = [a for a in alerts if a.level == level]
        return alerts[-limit:]

    # ===== Runtime Error Tracking =====

    def track_error(self, error: Exception, context: Optional[dict] = None):
        """Track a runtime error"""
        self._create_alert(
            "warning",
            f"runtime_error:{type(error).__name__}",
            str(error),
            metadata={"error_type": type(error).__name__, "context": context or {}},
        )

    # ===== Continuous Monitoring =====

    def start_monitoring(self, interval_seconds: int = 60):
        """Start continuous system monitoring in background"""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop, args=(interval_seconds,), daemon=True
        )
        self._monitor_thread.start()
        logger.info(f"Environment monitoring started (interval: {interval_seconds}s)")

    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        self.stop_watching()
        logger.info("Environment monitoring stopped")

    def _monitoring_loop(self, interval: int):
        """Background monitoring loop"""
        while self._monitoring:
            try:
                health = self.check_system_health()

                if health["status"] != "healthy":
                    for warning in health.get("warnings", []):
                        self._create_alert("warning", "system_monitor", warning)
                    for error in health.get("errors", []):
                        self._create_alert("critical", "system_monitor", error)

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")

            time.sleep(interval)

    # ===== Environment Summary =====

    def get_environment_summary(self) -> dict[str, Any]:
        """Get comprehensive environment summary"""
        metrics = self.get_system_metrics()

        return {
            "system": {
                "platform": metrics.platform,
                "python_version": metrics.python_version,
                "cpu_percent": metrics.cpu_percent,
                "memory_percent": metrics.memory_percent,
                "disk_percent": metrics.disk_percent,
                "uptime_hours": round(metrics.uptime_seconds / 3600, 2),
            },
            "monitoring": {
                "active": self._monitoring,
                "watched_directories": list(self._watchers.keys()),
                "recent_file_events": len(self.file_events),
                "api_health_checks": len(self.api_health),
            },
            "alerts": {
                "total": len(self.alerts),
                "critical": len([a for a in self.alerts if a.level == "critical"]),
                "warnings": len([a for a in self.alerts if a.level == "warning"]),
                "recent": [
                    {"level": a.level, "message": a.message, "time": a.timestamp}
                    for a in self.alerts[-5:]
                ],
            },
        }


# Global environment sensor instance
env_sensor = EnvironmentSensor()
