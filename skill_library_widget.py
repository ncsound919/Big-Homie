"""
Skill Library Widget
Browse, execute, create, and schedule skills from the SkillRegistry.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime
from typing import Optional

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QSplitter,
)
from loguru import logger


class CreateSkillDialog(QDialog):
    """Dialog for creating a new skill."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Create New Skill")
        self.setMinimumWidth(500)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self._name = QLineEdit()
        self._name.setPlaceholderText("E.g. Email Drip Campaign")
        form.addRow("Name:", self._name)

        self._category = QComboBox()
        self._category.setEditable(True)
        self._category.addItems([
            "research", "coding", "analytics", "writing", "automation",
            "finance", "marketing", "outreach", "data",
        ])
        form.addRow("Category:", self._category)

        self._description = QLineEdit()
        self._description.setPlaceholderText("What this skill does")
        form.addRow("Description:", self._description)

        self._tags = QLineEdit()
        self._tags.setPlaceholderText("comma-separated tags")
        form.addRow("Tags:", self._tags)

        layout.addLayout(form)

        layout.addWidget(QLabel("Workflow Steps (one JSON object per line):"))
        self._workflow = QTextEdit()
        self._workflow.setPlaceholderText(
            '{"step": 1, "action": "search", "description": "Search for topic"}\n'
            '{"step": 2, "action": "analyze", "description": "Analyze results"}'
        )
        self._workflow.setMinimumHeight(140)
        layout.addWidget(self._workflow)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate_and_accept(self):
        if not self._name.text().strip():
            QMessageBox.warning(self, "Validation", "Name is required.")
            return
        if not self._description.text().strip():
            QMessageBox.warning(self, "Validation", "Description is required.")
            return
        try:
            self._parse_workflow()
        except ValueError as e:
            QMessageBox.warning(self, "Invalid workflow", str(e))
            return
        self.accept()

    def _parse_workflow(self) -> list:
        lines = [l.strip() for l in self._workflow.toPlainText().splitlines() if l.strip()]
        if not lines:
            raise ValueError("At least one workflow step is required.")
        steps = []
        for i, line in enumerate(lines, start=1):
            try:
                obj = json.loads(line)
                if "step" not in obj:
                    obj["step"] = i
                steps.append(obj)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Line {i} is not valid JSON: {exc}") from exc
        return steps

    def get_values(self) -> dict:
        return {
            "name": self._name.text().strip(),
            "category": self._category.currentText().strip(),
            "description": self._description.text().strip(),
            "tags": [t.strip() for t in self._tags.text().split(",") if t.strip()],
            "workflow": self._parse_workflow(),
        }


class ExecuteSkillDialog(QDialog):
    """Simple dialog for entering skill parameters."""

    def __init__(self, skill_name: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle(f"Execute: {skill_name}")
        self.setMinimumWidth(420)
        self._build_ui(skill_name)

    def _build_ui(self, skill_name: str):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<b>Skill:</b> {skill_name}"))
        layout.addWidget(QLabel("Parameters (JSON object, optional):"))
        self._params = QTextEdit()
        self._params.setPlaceholderText('{"topic": "machine learning", "depth": "deep"}')
        self._params.setMaximumHeight(120)
        layout.addWidget(self._params)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept_if_valid)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _accept_if_valid(self):
        text = self._params.toPlainText().strip()
        if not text:
            self.accept()
            return
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            QMessageBox.warning(
                self,
                "Invalid Parameters",
                f"Parameters must be valid JSON.\n\n{exc}",
            )
            return
        if not isinstance(parsed, dict):
            QMessageBox.warning(
                self,
                "Invalid Parameters",
                "Parameters must be a JSON object (e.g. {\"key\": \"value\"}).",
            )
            return
        self.accept()

    def get_params(self) -> Optional[dict]:
        text = self._params.toPlainText().strip()
        if not text:
            return None
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None


class SkillLibraryWidget(QWidget):
    """
    Full-featured skill library panel.

    Features:
    - Search / filter by category
    - Skill detail view
    - Execute skill with parameters
    - Create new skill
    - Schedule skill via cron
    - Delete custom skills
    """

    skill_scheduled = pyqtSignal(str)  # skill name to schedule

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._registry = None
        self._build_ui()
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_list)
        self._refresh_timer.start(10000)
        self._refresh_list()

    def _get_registry(self):
        if self._registry is None:
            try:
                from skill_acquisition import skill_registry
                self._registry = skill_registry
            except Exception as e:
                logger.warning(f"Could not load skill registry: {e}")
        return self._registry

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("🎯  Skill Library")
        title.setFont(QFont("", 13, QFont.Weight.Bold))
        hdr.addWidget(title)
        hdr.addStretch()

        self._stats_label = QLabel("0 skills")
        hdr.addWidget(self._stats_label)
        root.addLayout(hdr)

        # Search + filter
        filter_row = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search skills…")
        self._search.textChanged.connect(self._refresh_list)
        filter_row.addWidget(self._search)

        self._cat_filter = QComboBox()
        self._cat_filter.addItem("All categories")
        for cat in ["research", "coding", "analytics", "writing", "automation",
                    "finance", "marketing", "outreach", "data", "learned"]:
            self._cat_filter.addItem(cat)
        self._cat_filter.currentIndexChanged.connect(self._refresh_list)
        filter_row.addWidget(self._cat_filter)
        root.addLayout(filter_row)

        # Toolbar
        toolbar = QHBoxLayout()
        self._exec_btn = QPushButton("▶ Execute")
        self._exec_btn.setEnabled(False)
        self._exec_btn.clicked.connect(self._execute_selected)
        toolbar.addWidget(self._exec_btn)

        self._schedule_btn = QPushButton("⏰ Schedule")
        self._schedule_btn.setEnabled(False)
        self._schedule_btn.setToolTip("Create a cron job for this skill")
        self._schedule_btn.clicked.connect(self._schedule_selected)
        toolbar.addWidget(self._schedule_btn)

        self._create_btn = QPushButton("➕ New Skill")
        self._create_btn.clicked.connect(self._create_skill)
        toolbar.addWidget(self._create_btn)

        self._delete_btn = QPushButton("🗑 Delete")
        self._delete_btn.setEnabled(False)
        self._delete_btn.clicked.connect(self._delete_selected)
        toolbar.addWidget(self._delete_btn)

        toolbar.addStretch()

        self._refresh_btn = QPushButton("🔄 Refresh")
        self._refresh_btn.clicked.connect(self._refresh_list)
        toolbar.addWidget(self._refresh_btn)
        root.addLayout(toolbar)

        # Splitter: list + detail
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self._list = QListWidget()
        self._list.itemSelectionChanged.connect(self._on_selection_changed)
        splitter.addWidget(self._list)

        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)
        detail_layout.setContentsMargins(8, 0, 0, 0)

        detail_layout.addWidget(QLabel("<b>Skill Details</b>"))

        self._detail_name = QLabel("—")
        self._detail_name.setFont(QFont("", 11, QFont.Weight.Bold))
        detail_layout.addWidget(self._detail_name)

        self._detail_category = QLabel("")
        self._detail_category.setStyleSheet("color: #2196F3;")
        detail_layout.addWidget(self._detail_category)

        self._detail_desc = QLabel("")
        self._detail_desc.setWordWrap(True)
        detail_layout.addWidget(self._detail_desc)

        self._detail_tags = QLabel("")
        self._detail_tags.setStyleSheet("color: #9E9E9E; font-size: 11px;")
        detail_layout.addWidget(self._detail_tags)

        stats_box = QGroupBox("Performance")
        stats_layout = QFormLayout(stats_box)
        self._detail_usage = QLabel("0")
        self._detail_success = QLabel("—")
        self._detail_last = QLabel("—")
        stats_layout.addRow("Usage count:", self._detail_usage)
        stats_layout.addRow("Success rate:", self._detail_success)
        stats_layout.addRow("Last used:", self._detail_last)
        detail_layout.addWidget(stats_box)

        detail_layout.addWidget(QLabel("<b>Workflow</b>"))
        self._detail_workflow = QTextEdit()
        self._detail_workflow.setReadOnly(True)
        self._detail_workflow.setFont(QFont("Courier New", 9))
        detail_layout.addWidget(self._detail_workflow)

        detail_layout.addStretch()
        splitter.addWidget(detail_widget)
        splitter.setSizes([300, 400])

        root.addWidget(splitter, stretch=1)

        # Output area
        output_box = QGroupBox("Execution Output")
        output_layout = QVBoxLayout(output_box)
        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setFont(QFont("Courier New", 9))
        self._output.setMaximumHeight(130)
        output_layout.addWidget(self._output)
        root.addWidget(output_box)

    # ── Skill list ────────────────────────────────────────────────────────────

    def _refresh_list(self):
        registry = self._get_registry()
        if not registry:
            return

        query = self._search.text().strip() or None
        cat = self._cat_filter.currentText()
        category = None if cat == "All categories" else cat

        skills = registry.search_skills(query=query, category=category)

        self._list.clear()
        for skill in skills:
            item = QListWidgetItem(
                f"{skill.name}  [{skill.category}]  ✓{int(skill.success_rate * 100)}%  ×{skill.usage_count}"
            )
            item.setData(Qt.ItemDataRole.UserRole, skill.skill_id)
            self._list.addItem(item)

        total = len(registry.skills)
        self._stats_label.setText(f"{total} skills  ({len(skills)} shown)")

    def _on_selection_changed(self):
        selected = self._list.selectedItems()
        has_sel = bool(selected)
        self._exec_btn.setEnabled(has_sel)
        self._schedule_btn.setEnabled(has_sel)

        registry = self._get_registry()
        if has_sel and registry:
            skill_id = selected[0].data(Qt.ItemDataRole.UserRole)
            skill = registry.skills.get(skill_id)
            if skill:
                self._show_detail(skill)
                # Only allow delete for auto-learned or custom skills
                self._delete_btn.setEnabled(skill.author in ("auto_learned", "custom"))
        else:
            self._delete_btn.setEnabled(False)

    def _show_detail(self, skill):
        self._detail_name.setText(skill.name)
        self._detail_category.setText(f"Category: {skill.category}")
        self._detail_desc.setText(skill.description)
        self._detail_tags.setText("Tags: " + ", ".join(skill.tags) if skill.tags else "")
        self._detail_usage.setText(str(skill.usage_count))
        self._detail_success.setText(f"{int(skill.success_rate * 100)}%")
        last = skill.last_used or "never"
        self._detail_last.setText(last[:19] if len(last) > 19 else last)
        self._detail_workflow.setPlainText(
            json.dumps(skill.workflow, indent=2)
        )

    # ── Actions ───────────────────────────────────────────────────────────────

    def _get_selected_skill(self):
        items = self._list.selectedItems()
        if not items:
            return None
        registry = self._get_registry()
        if not registry:
            return None
        return registry.skills.get(items[0].data(Qt.ItemDataRole.UserRole))

    def _execute_selected(self):
        skill = self._get_selected_skill()
        if not skill:
            return

        dlg = ExecuteSkillDialog(skill.name, parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        params = dlg.get_params()
        self._output.append(f"\n[{datetime.now().strftime('%H:%M:%S')}] Executing: {skill.name}…")

        # Run in background thread via QThread to avoid blocking UI
        class _ExecWorker(QThread):
            done = pyqtSignal(object)
            error = pyqtSignal(str)

            def __init__(self, skill_id, params, registry):
                super().__init__()
                self._skill_id = skill_id
                self._params = params
                self._registry = registry

            def run(self):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        self._registry.execute_skill(self._skill_id, self._params)
                    )
                    self.done.emit(result)
                except Exception as e:
                    self.error.emit(str(e))
                finally:
                    loop.close()

        registry = self._get_registry()
        if not registry:
            return

        worker = _ExecWorker(skill.skill_id, params, registry)
        worker.done.connect(self._on_exec_done)
        worker.error.connect(self._on_exec_error)
        worker.start()
        # Keep reference so it isn't garbage-collected
        self._active_worker = worker

    def _on_exec_done(self, result):
        ts = datetime.now().strftime("%H:%M:%S")
        if result.success:
            preview = str(result.output or "")[:500]
            self._output.append(
                f"[{ts}] ✅ Success ({result.duration_seconds:.1f}s, ${result.cost:.4f})\n{preview}"
            )
        else:
            self._output.append(f"[{ts}] ❌ Failed: {result.error}")
        self._refresh_list()

    def _on_exec_error(self, error: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self._output.append(f"[{ts}] ❌ Error: {error}")

    def _schedule_selected(self):
        skill = self._get_selected_skill()
        if not skill:
            return
        self.skill_scheduled.emit(skill.name)
        QMessageBox.information(
            self, "Schedule Skill",
            f"Skill '{skill.name}' sent to Cron Manager.\nOpen the ⏰ Cron Jobs tab to set the schedule."
        )

    def _create_skill(self):
        dlg = CreateSkillDialog(parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        vals = dlg.get_values()
        registry = self._get_registry()
        if not registry:
            QMessageBox.warning(self, "No Registry", "Skill registry is unavailable.")
            return

        try:
            from skill_acquisition import SkillDefinition
            skill = SkillDefinition(
                skill_id=str(uuid.uuid4()),
                name=vals["name"],
                description=vals["description"],
                category=vals["category"],
                workflow=vals["workflow"],
                tags=vals["tags"],
                author="custom",
            )
            registry.register_skill(skill)
            self._output.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Skill '{skill.name}' created.")
            self._refresh_list()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _delete_selected(self):
        skill = self._get_selected_skill()
        if not skill:
            return
        reply = QMessageBox.question(
            self, "Delete Skill",
            f"Delete skill '{skill.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            registry = self._get_registry()
            if registry and skill.skill_id in registry.skills:
                del registry.skills[skill.skill_id]
                self._output.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🗑 Deleted: {skill.name}")
                self._refresh_list()
