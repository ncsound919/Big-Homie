"""
Progress Tracker for Big Homie
Provides visual feedback during long-running operations
"""
import time
from typing import Optional, Callable
from enum import Enum
from datetime import datetime
from loguru import logger

class ProgressState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ProgressTracker:
    """Tracks and displays progress for long-running tasks"""

    def __init__(self):
        self.current_task: Optional[str] = None
        self.progress: int = 0  # 0-100
        self.state: ProgressState = ProgressState.IDLE
        self.start_time: Optional[float] = None
        self.subtask: Optional[str] = None
        self.callback: Optional[Callable] = None

    def start(self, task: str, callback: Optional[Callable] = None):
        """Start tracking a new task"""
        self.current_task = task
        self.progress = 0
        self.state = ProgressState.RUNNING
        self.start_time = time.time()
        self.subtask = None
        self.callback = callback
        self._update_display()
        logger.info(f"Progress tracker started: {task}")

    def update(self, progress: int, subtask: Optional[str] = None):
        """Update progress (0-100)"""
        if self.state != ProgressState.RUNNING:
            return

        self.progress = min(100, max(0, progress))
        if subtask:
            self.subtask = subtask
        self._update_display()

    def complete(self):
        """Mark task as completed"""
        self.progress = 100
        self.state = ProgressState.COMPLETED
        self._update_display()
        elapsed = time.time() - self.start_time if self.start_time else 0
        logger.info(f"Progress tracker completed: {self.current_task} ({elapsed:.2f}s)")

    def fail(self, error: str):
        """Mark task as failed"""
        self.state = ProgressState.FAILED
        self._update_display()
        logger.error(f"Progress tracker failed: {self.current_task} - {error}")

    def _update_display(self):
        """Update the progress display"""
        if self.callback:
            self.callback(self.get_status_message())

    def get_status_message(self) -> str:
        """Generate status message with progress bar"""
        if self.state == ProgressState.IDLE:
            return "Ready"

        if self.state == ProgressState.COMPLETED:
            return f"✓ {self.current_task} - Completed"

        if self.state == ProgressState.FAILED:
            return f"✗ {self.current_task} - Failed"

        # Running state - show progress bar
        bar = self._generate_progress_bar()
        subtask_text = f" - {self.subtask}" if self.subtask else ""
        return f"{self.current_task}... [{bar}] {self.progress}%{subtask_text}"

    def _generate_progress_bar(self, width: int = 10) -> str:
        """Generate ASCII progress bar"""
        filled = int((self.progress / 100) * width)
        empty = width - filled
        return "|" * filled + "-" * empty

    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds"""
        if not self.start_time:
            return 0.0
        return time.time() - self.start_time

# Global progress tracker instance
progress_tracker = ProgressTracker()
