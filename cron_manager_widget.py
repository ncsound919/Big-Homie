"""
Cron Manager Widget
UI for creating, viewing, and managing scheduled tasks (KAIROS daemon integration).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from loguru import logger


class AddCronDialog(QDialog):
    """Dialog for adding a new cron task."""

    def __init__(self, skill_names: list[str], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Add Scheduled Task")
        self.setMinimumWidth(440)
        self._build_ui(skill_names)

    def _build_ui(self, skill_names: list[str]):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("E.g. Daily Market Check")
        form.addRow("Task Name:", self._name_edit)

        self._desc_edit = QLineEdit()
        self._desc_edit.setPlaceholderText("Short description")
        form.addRow("Description:", self._desc_edit)

        # Interval
        interval_row = QHBoxLayout()
        self._interval_spin = QSpinBox()
        self._interval_spin.setRange(1, 86400)
        self._interval_spin.setValue(60)
        self._interval_unit = QComboBox()
        self._interval_unit.addItems(["minutes", "hours", "seconds"])
        self._interval_unit.setCurrentIndex(1)  # hours default
        interval_row.addWidget(self._interval_spin)
        interval_row.addWidget(self._interval_unit)
        form.addRow("Interval:", interval_row)

        # Priority
        self._priority_combo = QComboBox()
        self._priority_combo.addItems(["background", "low", "normal", "high", "critical"])
        self._priority_combo.setCurrentIndex(2)
        form.addRow("Priority:", self._priority_combo)

        # Skill (optional)
        self._skill_combo = QComboBox()
        self._skill_combo.addItem("— none —")
        for name in skill_names:
            self._skill_combo.addItem(name)
        form.addRow("Linked Skill:", self._skill_combo)

        self._enabled_cb = QCheckBox("Enabled")
        self._enabled_cb.setChecked(True)
        form.addRow("", self._enabled_cb)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate_and_accept(self):
        if not self._name_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Task name is required.")
            return
        self.accept()

    def get_values(self) -> dict:
        unit_multiplier = {"seconds": 1, "minutes": 60, "hours": 3600}
        unit = self._interval_unit.currentText()
        interval_seconds = self._interval_spin.value() * unit_multiplier[unit]

        skill_text = self._skill_combo.currentText()
        linked_skill = None if skill_text.startswith("—") else skill_text

        return {
            "name": self._name_edit.text().strip(),
            "description": self._desc_edit.text().strip(),
            "interval_seconds": interval_seconds,
            "priority": self._priority_combo.currentText(),
            "linked_skill": linked_skill,
            "enabled": self._enabled_cb.isChecked(),
        }


class CronManagerWidget(QWidget):
    """
    Widget for managing scheduled daemon tasks.

    Displays all tasks registered with the KAIROS daemon, lets the user:
    - Add new interval-based tasks (optionally linked to a skill)
    - Enable / disable tasks
    - Run a task immediately
    - Remove custom tasks
    """

    task_run_requested = pyqtSignal(str)  # task_id

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._daemon = None
        self._skill_registry = None
        self._build_ui()
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_table)
        self._refresh_timer.start(5000)  # refresh every 5 s
        self._refresh_table()

    # ── lazy imports ──────────────────────────────────────────────────────────

    def _get_daemon(self):
        if self._daemon is None:
            try:
                from kairos_daemon import KairosDaemon
                self._daemon = KairosDaemon()
                self._daemon.start()
            except Exception as e:
                logger.warning(f"Could not start KAIROS daemon: {e}")
        return self._daemon

    def _get_skill_registry(self):
        if self._skill_registry is None:
            try:
                from skill_acquisition import skill_registry
                self._skill_registry = skill_registry
            except Exception as e:
                logger.warning(f"Could not load skill registry: {e}")
        return self._skill_registry

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("⏰  Scheduled Tasks (Cron Jobs)")
        title.setFont(QFont("", 13, QFont.Weight.Bold))
        hdr.addWidget(title)
        hdr.addStretch()

        # Daemon status badge
        self._status_label = QLabel("Daemon: unknown")
        self._status_label.setStyleSheet("color: #FFC107; font-weight: bold;")
        hdr.addWidget(self._status_label)

        self._start_btn = QPushButton("▶ Start Daemon")
        self._start_btn.setToolTip("Start the KAIROS background daemon")
        self._start_btn.clicked.connect(self._start_daemon)
        hdr.addWidget(self._start_btn)

        self._pause_btn = QPushButton("⏸ Pause")
        self._pause_btn.clicked.connect(self._toggle_pause)
        hdr.addWidget(self._pause_btn)

        root.addLayout(hdr)

        # Daemon metrics
        metrics_box = QGroupBox("Daemon Metrics")
        metrics_layout = QHBoxLayout(metrics_box)
        self._uptime_label = QLabel("Uptime: —")
        self._executed_label = QLabel("Executed: 0")
        self._failed_label = QLabel("Failed: 0")
        self._cost_label = QLabel("Hourly cost: $0.00")
        for lbl in [self._uptime_label, self._executed_label,
                    self._failed_label, self._cost_label]:
            metrics_layout.addWidget(lbl)
        metrics_layout.addStretch()
        root.addWidget(metrics_box)

        # Toolbar
        toolbar = QHBoxLayout()
        add_btn = QPushButton("➕ Add Task")
        add_btn.clicked.connect(self._add_task)
        toolbar.addWidget(add_btn)

        self._run_now_btn = QPushButton("▶ Run Now")
        self._run_now_btn.setEnabled(False)
        self._run_now_btn.clicked.connect(self._run_selected)
        toolbar.addWidget(self._run_now_btn)

        self._toggle_btn = QPushButton("⏸ Disable")
        self._toggle_btn.setEnabled(False)
        self._toggle_btn.clicked.connect(self._toggle_selected)
        toolbar.addWidget(self._toggle_btn)

        self._remove_btn = QPushButton("🗑 Remove")
        self._remove_btn.setEnabled(False)
        self._remove_btn.clicked.connect(self._remove_selected)
        toolbar.addWidget(self._remove_btn)

        toolbar.addStretch()

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._refresh_table)
        toolbar.addWidget(refresh_btn)
        root.addLayout(toolbar)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            ["Name", "Priority", "Interval", "Next Run", "Last Run", "Runs / Errors", "Enabled"]
        )
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        root.addWidget(self._table)

        # Log
        log_box = QGroupBox("Task Log")
        log_layout = QVBoxLayout(log_box)
        self._log_view = QTextEdit()
        self._log_view.setReadOnly(True)
        self._log_view.setMaximumHeight(120)
        self._log_view.setFont(QFont("Courier New", 9))
        log_layout.addWidget(self._log_view)
        root.addWidget(log_box)

    # ── Daemon control ────────────────────────────────────────────────────────

    def _start_daemon(self):
        daemon = self._get_daemon()
        if daemon:
            try:
                daemon.start()
                self._log("KAIROS daemon started.")
                self._refresh_table()
            except Exception as e:
                self._log(f"Error starting daemon: {e}")

    def _toggle_pause(self):
        daemon = self._get_daemon()
        if not daemon:
            return
        try:
            from kairos_daemon import DaemonState
            if daemon.state == DaemonState.PAUSED:
                daemon.resume()
                self._pause_btn.setText("⏸ Pause")
                self._log("Daemon resumed.")
            else:
                daemon.pause()
                self._pause_btn.setText("▶ Resume")
                self._log("Daemon paused.")
            self._refresh_table()
        except Exception as e:
            self._log(f"Error toggling pause: {e}")

    # ── Table management ──────────────────────────────────────────────────────

    def _refresh_table(self):
        daemon = self._get_daemon()
        if not daemon:
            self._status_label.setText("Daemon: unavailable")
            return

        # Update status
        try:
            status = daemon.get_status()
            state = status.get("state", "unknown")
            color = {"running": "#4CAF50", "idle": "#2196F3", "processing": "#FFC107",
                     "paused": "#FF9800", "stopped": "#F44336"}.get(state, "#D4D4D4")
            self._status_label.setText(f"Daemon: {state}")
            self._status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

            uptime = status.get("uptime_seconds", 0)
            h, m = divmod(int(uptime), 3600)
            m, s = divmod(m, 60)
            self._uptime_label.setText(f"Uptime: {h:02d}:{m:02d}:{s:02d}")
            self._executed_label.setText(f"Executed: {status.get('tasks_executed', 0)}")
            self._failed_label.setText(f"Failed: {status.get('tasks_failed', 0)}")
            self._cost_label.setText(f"Hourly cost: ${status.get('hourly_cost', 0.0):.4f}")
        except Exception as e:
            logger.debug(f"Could not read daemon status: {e}")

        # Populate table
        tasks = list(daemon.scheduled_tasks.values())
        self._table.setRowCount(len(tasks))
        for row, task in enumerate(tasks):
            self._table.setItem(row, 0, QTableWidgetItem(task.name))
            priority_str = task.priority.value if hasattr(task.priority, "value") else str(task.priority)
            self._table.setItem(row, 1, QTableWidgetItem(priority_str))

            interval_str = "—"
            if task.interval_seconds:
                h, rem = divmod(task.interval_seconds, 3600)
                m, s = divmod(rem, 60)
                parts = []
                if h:
                    parts.append(f"{h}h")
                if m:
                    parts.append(f"{m}m")
                if s:
                    parts.append(f"{s}s")
                interval_str = " ".join(parts) or "—"
            self._table.setItem(row, 2, QTableWidgetItem(interval_str))

            next_run = task.next_run.strftime("%H:%M:%S") if task.next_run else "—"
            self._table.setItem(row, 3, QTableWidgetItem(next_run))

            last_run = task.last_run.strftime("%H:%M:%S") if task.last_run else "never"
            self._table.setItem(row, 4, QTableWidgetItem(last_run))

            self._table.setItem(row, 5, QTableWidgetItem(f"{task.run_count} / {task.error_count}"))

            enabled_item = QTableWidgetItem("✅" if task.enabled else "❌")
            enabled_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 6, enabled_item)

            # Store task id for actions
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, task.id)

    def _on_selection_changed(self):
        has_sel = bool(self._table.selectionModel().selectedRows())
        self._run_now_btn.setEnabled(has_sel)
        self._toggle_btn.setEnabled(has_sel)
        self._remove_btn.setEnabled(has_sel)

        # Update toggle button label
        daemon = self._get_daemon()
        if has_sel and daemon:
            row = self._table.currentRow()
            task_id = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole) if self._table.item(row, 0) else None
            if task_id and task_id in daemon.scheduled_tasks:
                task = daemon.scheduled_tasks[task_id]
                self._toggle_btn.setText("▶ Enable" if not task.enabled else "⏸ Disable")

    def _selected_task_id(self) -> Optional[str]:
        row = self._table.currentRow()
        if row < 0:
            return None
        item = self._table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _add_task(self):
        skill_names: list[str] = []
        reg = self._get_skill_registry()
        if reg:
            skill_names = [s.name for s in reg.skills.values()]

        dlg = AddCronDialog(skill_names, parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        vals = dlg.get_values()
        daemon = self._get_daemon()
        if not daemon:
            QMessageBox.warning(self, "No Daemon", "KAIROS daemon is not available.")
            return

        try:
            from kairos_daemon import DaemonTask, TaskPriority
            priority_map = {
                "critical": TaskPriority.CRITICAL,
                "high": TaskPriority.HIGH,
                "normal": TaskPriority.NORMAL,
                "low": TaskPriority.LOW,
                "background": TaskPriority.BACKGROUND,
            }
            task = DaemonTask(
                id=f"custom_{uuid.uuid4().hex[:8]}",
                name=vals["name"],
                description=vals["description"],
                priority=priority_map.get(vals["priority"], TaskPriority.NORMAL),
                interval_seconds=vals["interval_seconds"],
                enabled=vals["enabled"],
                metadata={"linked_skill": vals["linked_skill"]},
            )
            daemon.register_task(task)
            self._log(f"Task added: {vals['name']}")
            self._refresh_table()
        except Exception as e:
            self._log(f"Error adding task: {e}")
            QMessageBox.critical(self, "Error", str(e))

    def _run_selected(self):
        task_id = self._selected_task_id()
        if not task_id:
            return
        daemon = self._get_daemon()
        if daemon:
            try:
                daemon.queue_task(task_id)
                self._log(f"Task queued for immediate execution: {task_id}")
                self.task_run_requested.emit(task_id)
            except Exception as e:
                self._log(f"Error running task: {e}")

    def _toggle_selected(self):
        task_id = self._selected_task_id()
        if not task_id:
            return
        daemon = self._get_daemon()
        if daemon and task_id in daemon.scheduled_tasks:
            task = daemon.scheduled_tasks[task_id]
            task.enabled = not task.enabled
            state = "enabled" if task.enabled else "disabled"
            self._log(f"Task {task.name} {state}.")
            self._refresh_table()

    def _remove_selected(self):
        task_id = self._selected_task_id()
        if not task_id:
            return
        daemon = self._get_daemon()
        if not daemon:
            return
        task = daemon.scheduled_tasks.get(task_id)
        if not task:
            return
        reply = QMessageBox.question(
            self, "Remove Task",
            f"Remove task '{task.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            daemon.unregister_task(task_id)
            self._log(f"Task removed: {task.name}")
            self._refresh_table()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self._log_view.append(f"[{ts}] {msg}")
