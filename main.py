"""
Big Homie - Main GUI Application
Cross-platform desktop application with modern UI
"""

import asyncio
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

from loguru import logger
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QFont, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from config import settings
from content_utils import markdown_exporter
from correction_ledger import correction_ledger
from cron_manager_widget import CronManagerWidget
from fact_metadata import fact_checker, metadata_tagger
from finance_dashboard_widget import FinanceDashboardWidget
from financial_settings_widget import SecureFinancialSettings
from llm_gateway import TaskType, llm
from marketing_dashboard_widget import MarketingDashboardWidget
from memory import memory
from skill_library_widget import SkillLibraryWidget
from time_awareness import time_awareness
from tone_preference import preference_tracker, tone_analyzer


class AgentWorker(QThread):
    """Background worker for agent tasks"""

    result_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    status_update = pyqtSignal(str)
    preflight_notice = pyqtSignal(str)
    progress_update = pyqtSignal(int, str)  # progress percentage, subtask
    fact_check_notice = pyqtSignal(str)

    def __init__(self, task: str, task_type: TaskType = TaskType.GENERAL, session_id: str = "main"):
        super().__init__()
        self.task = task
        self.task_type = task_type
        self.session_id = session_id

    def run(self):
        """Execute agent task"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Start progress tracking
            self.status_update.emit("Processing...")
            self.progress_update.emit(10, "Analyzing user input")

            # Analyze user's tone
            tone_analysis = tone_analyzer.analyze_message(self.task)
            style_guide = tone_analyzer.suggest_response_style()
            logger.debug(f"Tone analysis: {style_guide}")

            self.progress_update.emit(20, "Preparing context")

            # Prepare messages with enhanced context
            system_prompt = self.get_system_prompt()

            # Add time context
            system_prompt += f"\n\n{time_awareness.format_context_string()}"

            # Add correction ledger context
            corrections_context = correction_ledger.apply_corrections_to_context()
            if corrections_context:
                system_prompt += f"\n\n{corrections_context}"

            # Add user preferences context
            prefs_context = preference_tracker.apply_preferences_to_context()
            if prefs_context:
                system_prompt += f"\n\n{prefs_context}"

            # Add style guidance
            system_prompt += f"\n\n# Response Style Guidance:\n{style_guide}"

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": self.task},
            ]

            self.progress_update.emit(30, "Checking costs")

            preview = llm.preview_cost(messages, task_type=self.task_type)
            if preview and preview["warning_triggered"]:
                self.preflight_notice.emit(
                    f"Estimated request cost ${preview['estimated_cost']:.4f} "
                    f"using {preview['model']} exceeds the "
                    f"${preview['warning_threshold']:.2f} "
                    f"spend warning threshold."
                )
                self.status_update.emit(
                    f"Estimated cost ${preview['estimated_cost']:.4f}"
                    " — above spend warning threshold"
                )

            self.progress_update.emit(50, "Generating response")

            # Get completion
            result = loop.run_until_complete(llm.complete(messages, task_type=self.task_type))

            response = result["content"]

            self.progress_update.emit(70, "Fact-checking response")

            # Perform fact-checking
            fact_analysis = fact_checker.analyze_confidence(response)
            if fact_analysis["needs_verification"]:
                report = fact_checker.format_fact_check_report(fact_analysis)
                self.fact_check_notice.emit(report)

            self.progress_update.emit(80, "Tagging and categorizing")

            # Auto-tag the response
            tags = metadata_tagger.tag_content(response)
            logger.info(f"Auto-tagged response: {tags}")

            self.progress_update.emit(90, "Saving to memory")

            # Save to memory with metadata
            memory.add_message(self.session_id, "user", self.task, {"tone": tone_analysis})
            memory.add_message(
                self.session_id,
                "assistant",
                response,
                {
                    "tags": list(tags),
                    "fact_check": fact_analysis,
                    "model": result.get("_model", "unknown"),
                },
            )

            # Determine domain without mutating the tags set
            tags_list = list(tags)
            domain = tags_list[0] if tags_list else "general"

            # Log task
            memory.log_task(
                task=self.task,
                domain=domain,
                status="success",
                result={"response": response, "tags": tags_list},
                cost=llm.get_total_cost(),
            )

            self.progress_update.emit(100, "Complete")
            self.result_ready.emit(response)
            self.status_update.emit("Ready")

        except Exception as e:
            logger.error(f"Agent task failed: {str(e)}")
            self.error_occurred.emit(str(e))
            self.status_update.emit("Error")
        finally:
            loop.close()

    def get_system_prompt(self) -> str:
        """Get system prompt for agent"""
        return """You are Big Homie, an advanced AI agent with the following capabilities:

1. **Multi-Domain Expertise**: Finance, coding, research, marketing, web automation
2. **Tool Access**: Browser automation, web search, API integrations
3. **Memory**: You remember conversations and can learn from past interactions
4. **Self-Improvement**: You can create and refine skills based on successful workflows

Core Principles:
- Be direct and actionable
- Use tools when available
- Learn from every interaction
- Always aim for production-quality results
- Track costs and optimize for efficiency

Available Domains:
- [FIN] Finance & Trading
- [CODE] Software Development
- [RESEARCH] Deep Research & Analysis
- [MKT] Marketing & Content
- [WEB] Web Automation & Maintenance
- [DATA] Data Analysis

Response Format:
- Be concise but thorough
- Provide actionable steps
- Cite sources when relevant
- Suggest next steps"""


class BigHomieGUI(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.current_worker = None
        self.session_id = self._generate_session_id()
        self.init_ui()
        self.load_settings()

    def _generate_session_id(self) -> str:
        """Create a simple unique session identifier."""
        session_base = datetime.now().strftime("session_%Y%m%d_%H%M%S")
        return f"{session_base}_{uuid.uuid4().hex[:6]}"

    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle(f"{settings.app_name} v{settings.app_version}")
        self.setGeometry(100, 100, 1200, 800)

        # Try to load logo
        logo_path = Path(__file__).parent / "logo.png"
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        # Create menu bar
        self.create_menu_bar()

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)

        # Header with logo and title
        header_layout = QHBoxLayout()

        # Logo
        if logo_path.exists():
            logo_label = QLabel()
            pixmap = QPixmap(str(logo_path))
            logo_label.setPixmap(
                pixmap.scaled(
                    64,
                    64,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            header_layout.addWidget(logo_label)

        # Title
        title_label = QLabel(
            f"<h1>{settings.app_name}</h1><p>Your AI-Powered Multi-Domain Agent</p>"
        )
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # KAIROS daemon status
        self.kairos_status_label = QLabel("🔮 KAIROS: —")
        self.kairos_status_label.setStyleSheet("font-weight: bold; color: #9E9E9E;")
        self.kairos_status_label.setToolTip("KAIROS autonomous background daemon state")
        header_layout.addWidget(self.kairos_status_label)

        # Cost display
        self.cost_label = QLabel("Session Cost: $0.00")
        self.cost_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        header_layout.addWidget(self.cost_label)

        main_layout.addLayout(header_layout)

        # Tab widget
        self.tabs = QTabWidget()

        # Chat tab
        self.chat_tab = self.create_chat_tab()
        self.tabs.addTab(self.chat_tab, "💬 Chat")

        # History tab
        self.history_tab = self.create_history_tab()
        self.tabs.addTab(self.history_tab, "📜 History")

        # Skills Library tab (enhanced)
        self.skill_library_tab = SkillLibraryWidget()
        self.skill_library_tab.skill_scheduled.connect(self._on_skill_scheduled)
        self.tabs.addTab(self.skill_library_tab, "🎯 Skills Library")

        # Finance Dashboard tab
        self.finance_tab = FinanceDashboardWidget()
        self.tabs.addTab(self.finance_tab, "💰 Finance")

        # Marketing Dashboard tab
        self.marketing_tab = MarketingDashboardWidget()
        self.tabs.addTab(self.marketing_tab, "📣 Marketing")

        # Cron Jobs tab
        self.cron_tab = CronManagerWidget()
        self.tabs.addTab(self.cron_tab, "⏰ Cron Jobs")

        # Settings tab
        self.settings_tab = self.create_settings_tab()
        self.tabs.addTab(self.settings_tab, "⚙️ Settings")

        main_layout.addWidget(self.tabs)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Apply theme
        self.apply_theme()

        # Start cost update timer
        self.cost_timer = QTimer()
        self.cost_timer.timeout.connect(self.update_cost_display)
        self.cost_timer.start(1000)  # Update every second

        # Start KAIROS status timer
        self._kairos_status_timer = QTimer()
        self._kairos_status_timer.timeout.connect(self._update_kairos_status)
        self._kairos_status_timer.start(3000)  # Update every 3 seconds

    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        new_action = QAction("New Session", self)
        new_action.triggered.connect(self.new_session)
        file_menu.addAction(new_action)

        export_action = QAction("Export History (JSON & Markdown)", self)
        export_action.triggered.connect(self.export_history)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu("Tools")

        clear_memory_action = QAction("Clear Memory", self)
        clear_memory_action.triggered.connect(self.clear_memory)
        tools_menu.addAction(clear_memory_action)

        reset_cost_action = QAction("Reset Cost Counter", self)
        reset_cost_action.triggered.connect(self.reset_cost)
        tools_menu.addAction(reset_cost_action)

        tools_menu.addSeparator()

        # New feature actions
        export_thought_action = QAction("Export Current Chat as Markdown", self)
        export_thought_action.triggered.connect(self.export_current_chat)
        tools_menu.addAction(export_thought_action)

        view_corrections_action = QAction("View Correction Ledger", self)
        view_corrections_action.triggered.connect(self.view_corrections)
        tools_menu.addAction(view_corrections_action)

        view_preferences_action = QAction("View Learned Preferences", self)
        view_preferences_action.triggered.connect(self.view_preferences)
        tools_menu.addAction(view_preferences_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_chat_tab(self) -> QWidget:
        """Create chat interface tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Courier New", settings.ui_font_size))
        layout.addWidget(self.chat_display)

        # Input area
        input_layout = QHBoxLayout()

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask Big Homie anything...")
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)

        layout.addLayout(input_layout)

        return widget

    def create_history_tab(self) -> QWidget:
        """Create history tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.history_list = QListWidget()
        layout.addWidget(self.history_list)

        refresh_button = QPushButton("Refresh History")
        refresh_button.clicked.connect(self.refresh_history)
        layout.addWidget(refresh_button)

        return widget

    def create_settings_tab(self) -> QWidget:
        """Create settings tab with secure financial settings panel"""
        self._financial_settings = SecureFinancialSettings()
        self._financial_settings.settings_saved.connect(
            lambda: self.status_bar.showMessage("Settings saved – restart to apply changes")
        )
        return self._financial_settings

    def send_message(self):
        """Send message to agent"""
        message = self.input_field.text().strip()
        if not message:
            return

        # Display user message
        self.chat_display.append(f"\n<b style='color: #2196F3;'>You:</b> {message}\n")
        self.input_field.clear()
        self.send_button.setEnabled(False)

        # Start worker thread
        self.current_worker = AgentWorker(message, session_id=self.session_id)
        self.current_worker.result_ready.connect(self.on_result_ready)
        self.current_worker.error_occurred.connect(self.on_error)
        self.current_worker.status_update.connect(self.status_bar.showMessage)
        self.current_worker.preflight_notice.connect(self.on_preflight_notice)
        self.current_worker.progress_update.connect(self.on_progress_update)
        self.current_worker.fact_check_notice.connect(self.on_fact_check_notice)
        self.current_worker.start()

    def on_result_ready(self, response: str):
        """Handle agent response"""
        self.chat_display.append(f"<b style='color: #4CAF50;'>Big Homie:</b> {response}\n")
        self.send_button.setEnabled(True)
        self.input_field.setFocus()

    def on_error(self, error: str):
        """Handle error"""
        self.chat_display.append(f"<b style='color: #F44336;'>Error:</b> {error}\n")
        self.send_button.setEnabled(True)
        QMessageBox.warning(self, "Error", f"An error occurred: {error}")

    def on_preflight_notice(self, notice: str):
        """Show a preflight cost notice in the transcript."""
        self.chat_display.append(f"<i style='color: #FFC107;'>Notice:</i> {notice}\n")

    def on_progress_update(self, progress: int, subtask: str):
        """Handle progress updates"""
        if progress < 100:
            bar = self._generate_progress_bar(progress)
            self.status_bar.showMessage(f"[{bar}] {progress}% - {subtask}")
        else:
            self.status_bar.showMessage("Ready")

    def on_fact_check_notice(self, report: str):
        """Show fact-check report in the transcript."""
        self.chat_display.append(f"<i style='color: #FF9800;'>Fact-Check:</i>\n{report}\n")

    def _generate_progress_bar(self, progress: int, width: int = 20) -> str:
        """Generate ASCII progress bar"""
        filled = int((progress / 100) * width)
        empty = width - filled
        return "|" * filled + "-" * empty

    def update_cost_display(self):
        """Update cost display"""
        total_cost = llm.get_total_cost()
        self.cost_label.setText(f"Session Cost: ${total_cost:.4f}")

        # Alert if threshold exceeded
        if total_cost > settings.cost_alert_threshold:
            self.cost_label.setStyleSheet("font-weight: bold; color: #F44336;")

    def _update_kairos_status(self):
        """Update KAIROS daemon status badge in the header."""
        try:
            if not settings.kairos_enabled:
                self.kairos_status_label.setText("🔮 KAIROS: disabled")
                self.kairos_status_label.setStyleSheet("font-weight: bold; color: #9E9E9E;")
                return
            # Only read status if the daemon has already been accessed — don't force startup
            daemon = self.cron_tab._daemon
            if daemon is None:
                self.kairos_status_label.setText("🔮 KAIROS: not started")
                self.kairos_status_label.setStyleSheet("font-weight: bold; color: #9E9E9E;")
                return
            state = daemon.state.value if hasattr(daemon.state, "value") else str(daemon.state)
            color_map = {
                "running": "#4CAF50",
                "idle": "#2196F3",
                "processing": "#FFC107",
                "paused": "#FF9800",
                "stopped": "#F44336",
                "initializing": "#9C27B0",
            }
            color = color_map.get(state, "#9E9E9E")
            self.kairos_status_label.setText(f"🔮 KAIROS: {state}")
            self.kairos_status_label.setStyleSheet(f"font-weight: bold; color: {color};")
        except Exception:  # noqa: S110
            pass

    def _on_skill_scheduled(self, skill_name: str):
        """Switch to Cron Jobs tab when a skill is sent there from the Skill Library."""
        for i in range(self.tabs.count()):
            if "Cron" in self.tabs.tabText(i):
                self.tabs.setCurrentIndex(i)
                self.status_bar.showMessage(
                    f"Skill '{skill_name}' ready to schedule"
                    " — click ➕ Add Task and link the skill."
                )
                return

    def refresh_history(self):
        """Refresh task history"""
        self.history_list.clear()
        history = memory.get_task_history(limit=100)
        for item in history:
            self.history_list.addItem(
                f"[{item['timestamp']}] {item['task'][:50]}..."
                f" - {item['status']} (${item['cost']:.4f})"
            )

    def new_session(self):
        """Start new session"""
        reply = QMessageBox.question(
            self,
            "New Session",
            "Clear current chat and start new session?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.chat_display.clear()
            memory.clear_session(self.session_id)
            self.session_id = self._generate_session_id()
            llm.reset_cost()
            self.status_bar.showMessage("New session started")

    def clear_memory(self):
        """Handle clear-memory request"""
        reply = QMessageBox.warning(
            self,
            "Clear Memory",
            "Clear Memory is not implemented yet. "
            "No history, skills, or preferences "
            "will be deleted.\n\n"
            "Select Yes to acknowledge this message.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(
                self,
                "Not Implemented",
                "Clear Memory is not available yet, and no data has been deleted.",
            )
            self.status_bar.showMessage("Clear Memory not implemented; no data deleted")

    def reset_cost(self):
        """Reset cost counter"""
        llm.reset_cost()
        self.status_bar.showMessage("Cost counter reset")

    def export_history(self):
        """Export history to file"""
        history = memory.get_task_history(limit=1000)
        session_messages = memory.get_session_messages(self.session_id, limit=1000)
        export_dir = settings.data_dir / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = export_dir / f"big_homie_history_{timestamp}.json"
        markdown_path = export_dir / f"big_homie_history_{timestamp}.md"
        exported_at = datetime.now().isoformat()
        json_payload = {
            "session_id": self.session_id,
            "exported_at": exported_at,
            "history": history,
            "session_messages": session_messages,
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_payload, f, indent=2, ensure_ascii=False)
        with open(markdown_path, "w", encoding="utf-8") as f:
            f.write(self._format_history_markdown(history, session_messages, exported_at))

        self.status_bar.showMessage(f"History exported to {markdown_path}")
        QMessageBox.information(
            self, "Export Complete", f"History exported to:\n- {json_path}\n- {markdown_path}"
        )

    def _format_history_markdown(self, history, session_messages, exported_at: str) -> str:
        """Render task-history dicts and session-message dicts as markdown."""
        lines = [
            "# Big Homie Export",
            "",
            f"Generated: {exported_at}",
            f"Session ID: {self.session_id}",
            "",
        ]

        if session_messages:
            lines.extend(["## Chat Session", ""])
            for message in session_messages:
                lines.append(f"#### {message['role'].capitalize()} - {message['timestamp']}")
                lines.append("")
                lines.append(message["content"])
                lines.append("")

        if history:
            lines.extend(["## Task History", ""])
            for item in history:
                lines.append(f"### {item['task']}")
                lines.append("")
                lines.append(f"- Timestamp: {item['timestamp']}")
                lines.append(f"- Domain: {item['domain']}")
                lines.append(f"- Status: {item['status']}")
                lines.append(f"- Cost: ${item['cost']:.4f}")
                if item.get("duration"):
                    lines.append(f"- Duration: {item['duration']}")
                lines.append("")
                result = item.get("result", {})
                if result:
                    lines.extend(
                        [
                            "#### Result",
                            "",
                            "```json",
                            json.dumps(result, indent=2),
                            "```",
                            "",
                        ]
                    )

        if not session_messages and not history:
            lines.extend(["No chat or task history was available to export.", ""])

        return "\n".join(lines)

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About Big Homie",
            f"""<h2>{settings.app_name}</h2>
            <p>Version {settings.app_version}</p>
            <p>Your AI-Powered Multi-Domain Agent</p>
            <p><b>Features:</b></p>
            <ul>
            <li>Multi-provider LLM support (Anthropic, OpenAI, OpenRouter, Ollama)</li>
            <li>Three-layer memory system (Session, Long-term, Skills)</li>
            <li>Self-improving with learned workflows</li>
            <li>Cost tracking and optimization</li>
            <li>Multi-domain expertise (Finance, Coding, Research, Marketing, Web)</li>
            <li>Progress tracking and fact-checking</li>
            <li>Tone mirroring and preference learning</li>
            <li>Correction ledger for continuous improvement</li>
            </ul>
            <p>Built with Python, PyQt6, and cutting-edge AI frameworks</p>""",
        )

    def export_current_chat(self):
        """Export current chat session as markdown"""
        session_messages = memory.get_session_messages(self.session_id, limit=1000)
        if not session_messages:
            QMessageBox.information(
                self, "Export Chat", "No messages in current session to export."
            )
            return

        filepath = markdown_exporter.export_conversation(
            messages=session_messages, title=f"Chat Session {self.session_id}"
        )

        QMessageBox.information(self, "Export Complete", f"Chat exported to:\n{filepath}")

    def view_corrections(self):
        """View correction ledger summary"""
        summary = correction_ledger.get_learnings_summary()
        QMessageBox.information(self, "Correction Ledger", summary)

    def view_preferences(self):
        """View learned preferences summary"""
        summary = preference_tracker.get_preferences_summary()
        QMessageBox.information(self, "Learned Preferences", summary)

    def apply_theme(self):
        """Apply dark theme"""
        if settings.ui_theme == "dark":
            self.setStyleSheet("""
                QMainWindow, QWidget {
                    background-color: #1E1E1E;
                    color: #D4D4D4;
                }
                QTextEdit, QLineEdit, QListWidget {
                    background-color: #2D2D2D;
                    color: #D4D4D4;
                    border: 1px solid #3E3E3E;
                    border-radius: 4px;
                    padding: 8px;
                }
                QPushButton {
                    background-color: #0E639C;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1177BB;
                }
                QPushButton:disabled {
                    background-color: #3E3E3E;
                    color: #808080;
                }
                QTabWidget::pane {
                    border: 1px solid #3E3E3E;
                    background-color: #1E1E1E;
                }
                QTabBar::tab {
                    background-color: #2D2D2D;
                    color: #D4D4D4;
                    padding: 8px 16px;
                    border: 1px solid #3E3E3E;
                }
                QTabBar::tab:selected {
                    background-color: #0E639C;
                }
                QMenuBar {
                    background-color: #2D2D2D;
                    color: #D4D4D4;
                }
                QMenuBar::item:selected {
                    background-color: #0E639C;
                }
                QMenu {
                    background-color: #2D2D2D;
                    color: #D4D4D4;
                    border: 1px solid #3E3E3E;
                }
                QMenu::item:selected {
                    background-color: #0E639C;
                }
                QStatusBar {
                    background-color: #2D2D2D;
                    color: #D4D4D4;
                }
            """)

    def load_settings(self):
        """Load saved settings"""
        # Could load window geometry, last session, etc.
        pass

    def closeEvent(self, event):  # noqa: N802
        """Handle window close"""
        reply = QMessageBox.question(
            self,
            "Exit",
            "Are you sure you want to exit Big Homie?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName(settings.app_name)
    app.setApplicationVersion(settings.app_version)

    # Create and show main window
    window = BigHomieGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
