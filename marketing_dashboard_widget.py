"""
Marketing Dashboard Widget
Content generation, campaign scheduling, marketing skill shortcuts, and activity log.
"""

from __future__ import annotations

from datetime import datetime

from loguru import logger
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# Marketing skill shortcuts keyed by label → skill tags
MARKETING_SHORTCUTS = {
    "📝 Blog Post": ["writing", "blog", "content"],
    "📧 Email Campaign": ["marketing", "email", "outreach"],
    "📱 Social Media Post": ["marketing", "social", "content"],
    "🎯 Ad Copy": ["marketing", "ads", "copy"],
    "🔍 SEO Analysis": ["research", "seo", "analytics"],
    "📊 Market Research": ["research", "market", "analytics"],
    "🎥 Video Script": ["writing", "video", "script"],
    "💬 Press Release": ["writing", "pr", "content"],
}

# Marketing integration status keys
MARKETING_INTEGRATIONS = {
    "Twilio (SMS/Voice)": "TWILIO_ACCOUNT_SID",
    "Stripe (Billing)": "STRIPE_API_KEY",
    "Shopify": "SHOPIFY_ACCESS_TOKEN",
    "Perplexity AI": "PERPLEXITY_API_KEY",
    "SerpAPI": "SERP_API_KEY",
    "HuggingFace": "HUGGINGFACE_API_KEY",
}


def _env_configured(key: str) -> bool:
    import os

    val = os.environ.get(key, "").strip()
    return bool(val) and val not in ("your_key_here", "changeme", "")


class MarketingDashboardWidget(QWidget):
    """
    Marketing Dashboard.

    Sections:
    - Quick content generation (topic + platform + tone → generate)
    - Marketing skill shortcuts
    - Scheduled campaigns (via cron)
    - Content history
    - Integration status
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._registry = None
        self._content_history: list[dict] = []
        self._build_ui()
        self._refresh_integration_status()

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
        title = QLabel("📣  Marketing Dashboard")
        title.setFont(QFont("", 13, QFont.Weight.Bold))
        hdr.addWidget(title)
        hdr.addStretch()
        root.addLayout(hdr)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ── Left panel ──────────────────────────────────────────────────────
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 8, 0)

        # Content generation
        gen_box = QGroupBox("Content Generator")
        gen_layout = QVBoxLayout(gen_box)

        form = QFormLayout()
        self._topic_input = QLineEdit()
        self._topic_input.setPlaceholderText("E.g. AI-powered productivity tools")
        form.addRow("Topic:", self._topic_input)

        self._platform_combo = QComboBox()
        self._platform_combo.addItems(
            [
                "Blog Post",
                "Email Newsletter",
                "Twitter/X Thread",
                "LinkedIn Post",
                "Instagram Caption",
                "YouTube Script",
                "Press Release",
                "Ad Copy",
            ]
        )
        form.addRow("Platform:", self._platform_combo)

        self._tone_combo = QComboBox()
        self._tone_combo.addItems(
            [
                "Professional",
                "Casual",
                "Persuasive",
                "Educational",
                "Witty",
                "Inspirational",
                "Technical",
            ]
        )
        form.addRow("Tone:", self._tone_combo)

        self._audience_input = QLineEdit()
        self._audience_input.setPlaceholderText("E.g. SaaS founders, 25-40")
        form.addRow("Target Audience:", self._audience_input)

        gen_layout.addLayout(form)

        gen_btn = QPushButton("✨ Generate Content")
        gen_btn.setStyleSheet("font-weight: bold; padding: 8px;")
        gen_btn.clicked.connect(self._generate_content)
        gen_layout.addWidget(gen_btn)

        left_layout.addWidget(gen_box)

        # Skill shortcuts
        shortcuts_box = QGroupBox("Marketing Skill Shortcuts")
        shortcuts_layout = QVBoxLayout(shortcuts_box)
        shortcut_grid_row: QHBoxLayout | None = None
        col = 0
        for label, tags in MARKETING_SHORTCUTS.items():
            if col % 2 == 0:
                shortcut_grid_row = QHBoxLayout()
                shortcuts_layout.addLayout(shortcut_grid_row)
            btn = QPushButton(label)
            btn.setToolTip(f"Find and run a skill with tags: {', '.join(tags)}")
            btn.clicked.connect(lambda checked, t=tags: self._run_shortcut(t))
            if shortcut_grid_row is not None:
                shortcut_grid_row.addWidget(btn)
            col += 1

        left_layout.addWidget(shortcuts_box)

        # Schedule campaign
        sched_box = QGroupBox("Schedule Campaign")
        sched_layout = QVBoxLayout(sched_box)
        sched_layout.addWidget(QLabel("Link a cron job to auto-run marketing tasks."))
        sched_btn = QPushButton("⏰ Open Cron Manager")
        sched_btn.clicked.connect(self._open_cron_tab)
        sched_layout.addWidget(sched_btn)
        left_layout.addWidget(sched_box)

        # Integration status
        integ_box = QGroupBox("Marketing Integrations")
        integ_layout = QVBoxLayout(integ_box)
        self._integ_labels: dict[str, QLabel] = {}
        for name, _env_key in MARKETING_INTEGRATIONS.items():
            row = QHBoxLayout()
            lbl = QLabel(name)
            status = QLabel()
            self._integ_labels[name] = status
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(status)
            integ_layout.addLayout(row)
        left_layout.addWidget(integ_box)

        left_layout.addStretch()
        splitter.addWidget(left)

        # ── Right panel ─────────────────────────────────────────────────────
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 0, 0, 0)

        right_layout.addWidget(QLabel("<b>Generated Content</b>"))
        self._output_area = QTextEdit()
        self._output_area.setReadOnly(False)
        self._output_area.setFont(QFont("Courier New", 10))
        self._output_area.setPlaceholderText("Generated content will appear here…")
        right_layout.addWidget(self._output_area, stretch=2)

        # Content history
        hist_box = QGroupBox("Content History")
        hist_layout = QVBoxLayout(hist_box)
        self._history_list = QListWidget()
        self._history_list.itemClicked.connect(self._load_history_item)
        self._history_list.setMaximumHeight(180)
        hist_layout.addWidget(self._history_list)

        hist_buttons = QHBoxLayout()
        copy_btn = QPushButton("📋 Copy to Clipboard")
        copy_btn.clicked.connect(self._copy_output)
        hist_buttons.addWidget(copy_btn)

        clear_hist_btn = QPushButton("🗑 Clear History")
        clear_hist_btn.clicked.connect(self._clear_history)
        hist_buttons.addWidget(clear_hist_btn)
        hist_layout.addLayout(hist_buttons)

        right_layout.addWidget(hist_box)

        splitter.addWidget(right)
        splitter.setSizes([420, 560])
        root.addWidget(splitter, stretch=1)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _refresh_integration_status(self):
        for name, env_key in MARKETING_INTEGRATIONS.items():
            lbl = self._integ_labels.get(name)
            if lbl:
                configured = _env_configured(env_key)
                lbl.setText("✅ configured" if configured else "⬜ not set")
                lbl.setStyleSheet("color: #4CAF50;" if configured else "color: #9E9E9E;")

    def _generate_content(self):
        topic = self._topic_input.text().strip()
        if not topic:
            QMessageBox.warning(self, "Input Required", "Please enter a topic.")
            return

        platform = self._platform_combo.currentText()
        tone = self._tone_combo.currentText()
        audience = self._audience_input.text().strip() or "general audience"

        prompt = (
            f"Create a {platform} about: {topic}\n"
            f"Tone: {tone}\n"
            f"Target audience: {audience}\n\n"
            f"Produce ready-to-publish content with appropriate formatting, "
            f"hooks, CTAs, and hashtags where relevant."
        )

        self._output_area.setPlainText("Generating content…")

        import asyncio

        from PyQt6.QtCore import QThread
        from PyQt6.QtCore import pyqtSignal as Signal

        class _Worker(QThread):
            done = Signal(str)
            error = Signal(str)

            def __init__(self, prompt: str):
                super().__init__()
                self._prompt = prompt

            def run(self):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    from llm_gateway import llm

                    messages = [
                        {
                            "role": "system",
                            "content": "You are a world-class marketing copywriter and content strategist. "
                            "Produce polished, engaging content that drives real results.",
                        },
                        {"role": "user", "content": self._prompt},
                    ]
                    result = loop.run_until_complete(llm.complete(messages))
                    self.done.emit(result.get("content", ""))
                except Exception as e:
                    self.error.emit(str(e))
                finally:
                    loop.close()

        worker = _Worker(prompt)
        worker.done.connect(lambda text: self._on_content_ready(text, platform, topic))
        worker.error.connect(self._on_content_error)
        worker.start()
        self._active_worker = worker

    def _on_content_ready(self, text: str, platform: str, topic: str):
        self._output_area.setPlainText(text)
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "platform": platform,
            "topic": topic,
            "content": text,
        }
        self._content_history.append(entry)
        item = QListWidgetItem(f"[{entry['timestamp']}] {platform}: {topic[:50]}")
        item.setData(Qt.ItemDataRole.UserRole, len(self._content_history) - 1)
        self._history_list.addItem(item)

    def _on_content_error(self, error: str):
        self._output_area.setPlainText(f"Error generating content:\n{error}")

    def _run_shortcut(self, tags: list[str]):
        registry = self._get_registry()
        if not registry:
            QMessageBox.warning(self, "Unavailable", "Skill registry not available.")
            return

        skills = registry.search_skills(tags=tags)
        if not skills:
            QMessageBox.information(
                self,
                "No Skill Found",
                f"No skill found for tags: {', '.join(tags)}\n"
                "Create one in the 🎯 Skills Library tab.",
            )
            return

        skill = skills[0]
        topic = self._topic_input.text().strip() or "the selected topic"
        self._output_area.setPlainText(f"Running skill: {skill.name}…")

        import asyncio

        from PyQt6.QtCore import QThread
        from PyQt6.QtCore import pyqtSignal as Signal

        class _Worker(QThread):
            done = Signal(object)
            error = Signal(str)

            def __init__(self, registry, skill_id, params):
                super().__init__()
                self._registry = registry
                self._skill_id = skill_id
                self._params = params

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

        params = {"topic": topic, "audience": self._audience_input.text().strip() or "general"}
        worker = _Worker(registry, skill.skill_id, params)
        worker.done.connect(
            lambda r: self._output_area.setPlainText(str(r.output or r.error or "No output"))
        )
        worker.error.connect(lambda e: self._output_area.setPlainText(f"Error: {e}"))
        worker.start()
        self._active_worker = worker

    def _load_history_item(self, item: QListWidgetItem):
        idx = item.data(Qt.ItemDataRole.UserRole)
        if idx is not None and 0 <= idx < len(self._content_history):
            self._output_area.setPlainText(self._content_history[idx]["content"])

    def _copy_output(self):
        from PyQt6.QtWidgets import QApplication

        QApplication.clipboard().setText(self._output_area.toPlainText())
        QMessageBox.information(self, "Copied", "Content copied to clipboard.")

    def _clear_history(self):
        self._content_history.clear()
        self._history_list.clear()

    def _open_cron_tab(self):
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, "tabs"):
                for i in range(parent.tabs.count()):
                    if "Cron" in parent.tabs.tabText(i):
                        parent.tabs.setCurrentIndex(i)
                        return
            parent = parent.parent()
        QMessageBox.information(
            self, "Cron Manager", "Open the ⏰ Cron Jobs tab to schedule marketing campaigns."
        )
