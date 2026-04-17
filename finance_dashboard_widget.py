"""
Finance Dashboard Widget
Revenue summary, integration status, active stream controls, and quick actions.
"""

from __future__ import annotations

from datetime import datetime

from loguru import logger
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# Integration name → (enabled env key, description)
INTEGRATION_MAP = {
    "Alpaca (Stocks)": ("ALPACA_API_KEY", "Stock / ETF trading"),
    "IBKR": ("IBKR_ENABLED", "Interactive Brokers TWS"),
    "Schwab (Options)": ("SCHWAB_CLIENT_ID", "Options & equities"),
    "Binance": ("BINANCE_API_KEY", "Crypto spot trading"),
    "Kraken": ("KRAKEN_API_KEY", "Crypto exchange"),
    "Coinbase Adv.": ("COINBASE_ADV_API_KEY", "Coinbase Advanced Trade"),
    "Base L2": ("BASE_WALLET_ADDRESS", "Ethereum L2 wallet"),
    "Stripe": ("STRIPE_API_KEY", "Payment / SaaS billing"),
    "Shopify": ("SHOPIFY_ACCESS_TOKEN", "E-commerce store"),
    "Amazon SP-API": ("AMAZON_SELLER_ID", "Amazon seller"),
    "Plaid": ("PLAID_CLIENT_ID", "Bank account linking"),
    "Twilio": ("TWILIO_ACCOUNT_SID", "Voice / SMS"),
    "ShipStation": ("SHIPSTATION_API_KEY", "Order fulfillment"),
    "DraftKings": ("DRAFTKINGS_API_KEY", "Sports betting"),
    "PrizePicks": ("PRIZEPICKS_API_KEY", "Fantasy sports"),
    "Perplexity AI": ("PERPLEXITY_API_KEY", "AI research"),
}


def _env_key_configured(env_key: str) -> bool:
    """Return True if the env key is set to a non-empty, non-placeholder value."""
    import os

    val = os.environ.get(env_key, "").strip()
    return bool(val) and val not in ("your_key_here", "changeme", "")


class IntegrationStatusGrid(QWidget):
    """Compact grid of integration status pills."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(220)

        container = QWidget()
        grid = QHBoxLayout(container)
        grid.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        grid.setSpacing(8)

        col_max = 4
        col = 0
        row_widget = None
        row_layout = None

        for name, (env_key, desc) in INTEGRATION_MAP.items():
            if col % col_max == 0:
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setSpacing(8)
                grid.addWidget(row_widget)

            configured = _env_key_configured(env_key)
            pill = QLabel(f"{'✅' if configured else '⬜'} {name}")
            pill.setToolTip(
                f"{desc}\nEnv key: {env_key}\nStatus: {'configured' if configured else 'not set'}"
            )
            pill.setStyleSheet(
                "background-color: #1B5E20; border-radius: 4px; padding: 4px 8px; color: #C8E6C9;"
                if configured
                else "background-color: #37474F; border-radius:"
                " 4px; padding: 4px 8px; color: #90A4AE;"
            )
            if row_layout:
                row_layout.addWidget(pill)
            col += 1

        scroll.setWidget(container)
        layout.addWidget(scroll)

    def refresh(self):
        # Rebuild on refresh
        for i in reversed(range(self.layout().count())):
            w = self.layout().itemAt(i).widget()
            if w:
                w.deleteLater()
        self._build_ui()


class FinanceDashboardWidget(QWidget):
    """
    Finance Dashboard.

    Sections:
    - Revenue Goal Progress
    - Active Revenue Streams
    - Integration Status Grid
    - Recent Revenue Tasks
    - Quick Actions
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._revenue_engine = None
        self._build_ui()
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh)
        self._refresh_timer.start(10000)
        self._refresh()

    def _get_engine(self):
        if self._revenue_engine is None:
            try:
                from revenue_engine import RevenueEngine

                self._revenue_engine = RevenueEngine()
            except Exception as e:
                logger.warning(f"Could not load revenue engine: {e}")
        return self._revenue_engine

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("💰  Finance Dashboard")
        title.setFont(QFont("", 13, QFont.Weight.Bold))
        hdr.addWidget(title)
        hdr.addStretch()

        open_settings_btn = QPushButton("⚙️ Financial Settings")
        open_settings_btn.clicked.connect(self._open_financial_settings)
        hdr.addWidget(open_settings_btn)

        root.addLayout(hdr)

        # Revenue goal progress
        goal_box = QGroupBox("Revenue Goals")
        goal_layout = QFormLayout(goal_box)

        self._daily_goal_label = QLabel("$0.00")
        self._daily_goal_label.setFont(QFont("", 11, QFont.Weight.Bold))
        goal_layout.addRow("Daily Goal:", self._daily_goal_label)

        self._today_revenue_label = QLabel("$0.00")
        goal_layout.addRow("Today Revenue:", self._today_revenue_label)

        self._today_profit_label = QLabel("$0.00")
        goal_layout.addRow("Today Profit:", self._today_profit_label)

        self._goal_progress = QProgressBar()
        self._goal_progress.setRange(0, 100)
        self._goal_progress.setFormat("%p% of daily goal")
        goal_layout.addRow("Progress:", self._goal_progress)

        self._risk_label = QLabel("—")
        goal_layout.addRow("Risk Level:", self._risk_label)

        self._streams_label = QLabel("—")
        self._streams_label.setWordWrap(True)
        goal_layout.addRow("Active Streams:", self._streams_label)

        root.addWidget(goal_box)

        # Integration status
        integ_box = QGroupBox("Integration Status")
        integ_layout = QVBoxLayout(integ_box)
        self._integ_grid = IntegrationStatusGrid()
        integ_layout.addWidget(self._integ_grid)

        refresh_integ_btn = QPushButton("🔄 Refresh Integrations")
        refresh_integ_btn.clicked.connect(self._integ_grid.refresh)
        integ_layout.addWidget(refresh_integ_btn)
        root.addWidget(integ_box)

        # Recent tasks
        tasks_box = QGroupBox("Recent Revenue Tasks")
        tasks_layout = QVBoxLayout(tasks_box)
        self._tasks_table = QTableWidget()
        self._tasks_table.setColumnCount(5)
        self._tasks_table.setHorizontalHeaderLabels(
            ["ID", "Stream", "Goal ($)", "Revenue ($)", "Status"]
        )
        self._tasks_table.setMaximumHeight(160)
        self._tasks_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tasks_layout.addWidget(self._tasks_table)
        root.addWidget(tasks_box)

        # Quick actions
        action_box = QGroupBox("Quick Actions")
        action_layout = QHBoxLayout(action_box)

        run_session_btn = QPushButton("▶ Run Revenue Session")
        run_session_btn.setToolTip("Execute a revenue session against all active streams")
        run_session_btn.clicked.connect(self._run_revenue_session)
        action_layout.addWidget(run_session_btn)

        self._engine_toggle_btn = QPushButton("⏹ Disable Engine")
        self._engine_toggle_btn.clicked.connect(self._toggle_engine)
        action_layout.addWidget(self._engine_toggle_btn)

        action_layout.addStretch()
        root.addWidget(action_box)

        # Log
        log_box = QGroupBox("Activity Log")
        log_layout = QVBoxLayout(log_box)
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setFont(QFont("Courier New", 9))
        self._log.setMaximumHeight(110)
        log_layout.addWidget(self._log)
        root.addWidget(log_box)

    # ── Data refresh ──────────────────────────────────────────────────────────

    def _refresh(self):
        engine = self._get_engine()
        if not engine:
            return

        try:
            from config import settings

            daily_goal = engine.get_daily_goal()
            today_rev = engine.get_today_revenue()
            today_profit = engine.get_today_profit()

            self._daily_goal_label.setText(f"${daily_goal:,.2f}")
            self._today_revenue_label.setText(f"${today_rev:,.2f}")

            profit_color = "#4CAF50" if today_profit >= 0 else "#F44336"
            self._today_profit_label.setText(
                f"<span style='color:{profit_color}'>${today_profit:,.2f}</span>"
            )

            pct = int((today_rev / max(daily_goal, 0.01)) * 100)
            self._goal_progress.setValue(min(pct, 100))

            self._risk_label.setText(engine.risk_level.value.title())
            streams = [s.value for s in engine.active_streams]
            self._streams_label.setText(", ".join(streams) if streams else "none configured")

            # Update engine toggle button
            engine_enabled = getattr(settings, "revenue_engine_enabled", False)
            self._engine_toggle_btn.setText(
                "⏹ Disable Engine" if engine_enabled else "▶ Enable Engine"
            )
        except Exception as e:
            logger.debug(f"Finance dashboard refresh error: {e}")

        # Recent tasks table
        try:
            tasks = list(engine.tasks.values())[-20:]
            self._tasks_table.setRowCount(len(tasks))
            for row, task in enumerate(tasks):
                self._tasks_table.setItem(row, 0, QTableWidgetItem(task.id))
                self._tasks_table.setItem(row, 1, QTableWidgetItem(task.stream.value))
                self._tasks_table.setItem(row, 2, QTableWidgetItem(f"${task.goal_usd:.2f}"))
                self._tasks_table.setItem(row, 3, QTableWidgetItem(f"${task.revenue_usd:.2f}"))
                status_item = QTableWidgetItem(task.status)
                if task.status == "completed":
                    status_item.setForeground(Qt.GlobalColor.green)
                elif task.status == "failed":
                    status_item.setForeground(Qt.GlobalColor.red)
                self._tasks_table.setItem(row, 4, status_item)
        except Exception as e:
            logger.debug(f"Tasks table refresh error: {e}")

    # ── Actions ───────────────────────────────────────────────────────────────

    def _run_revenue_session(self):
        engine = self._get_engine()
        if not engine:
            QMessageBox.warning(self, "Unavailable", "Revenue engine not available.")
            return

        self._log_msg("Starting revenue session…")

        import asyncio

        from PyQt6.QtCore import QThread
        from PyQt6.QtCore import pyqtSignal as Signal

        class _Worker(QThread):
            done = Signal(object)
            error = Signal(str)

            def __init__(self, engine):
                super().__init__()
                self._engine = engine

            def run(self):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    report = loop.run_until_complete(self._engine.run_session())
                    self.done.emit(report)
                except Exception as e:
                    self.error.emit(str(e))
                finally:
                    loop.close()

        worker = _Worker(engine)
        worker.done.connect(self._on_session_done)
        worker.error.connect(self._on_session_error)
        worker.start()
        self._active_worker = worker

    def _on_session_done(self, report):
        try:
            self._log_msg(
                f"✅ Session complete — Revenue: ${report.total_revenue:.2f}  "
                f"Profit: ${report.total_profit:.2f}  "
                f"Tasks: {report.tasks_completed}/{report.tasks_completed + report.tasks_failed}"
            )
        except Exception:
            self._log_msg("✅ Revenue session complete.")
        self._refresh()

    def _on_session_error(self, error: str):
        self._log_msg(f"❌ Session error: {error}")

    def _toggle_engine(self):
        try:
            import re
            from pathlib import Path

            from config import settings

            new_enabled = not settings.revenue_engine_enabled

            # 1. Update the in-memory settings object so the running engine sees the change
            settings.revenue_engine_enabled = new_enabled

            # 2. Persist to .env so the change survives a restart
            env_path = Path(__file__).parent / ".env"
            new_val_str = "true" if new_enabled else "false"
            key = "REVENUE_ENGINE_ENABLED"

            if env_path.exists():
                content = env_path.read_text(encoding="utf-8")
                pattern = re.compile(r"^" + re.escape(key) + r"\s*=.*$", re.MULTILINE)
                if pattern.search(content):
                    content = pattern.sub(f"{key}={new_val_str}", content)
                else:
                    content = content.rstrip("\n") + f"\n{key}={new_val_str}\n"
            else:
                content = f"{key}={new_val_str}\n"

            env_path.write_text(content, encoding="utf-8")

            state_str = "enabled" if new_enabled else "disabled"
            self._log_msg(f"Revenue engine {state_str} and persisted to .env.")
            self._refresh()
        except Exception as e:
            self._log_msg(f"Error toggling engine: {e}")

    def _open_financial_settings(self):
        # Switch to the Settings tab — emit a signal if parent supports it,
        # otherwise show a message.
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, "tabs"):
                for i in range(parent.tabs.count()):
                    if "Settings" in parent.tabs.tabText(i):
                        parent.tabs.setCurrentIndex(i)
                        return
            parent = parent.parent()
        QMessageBox.information(
            self, "Settings", "Open the ⚙️ Settings tab to configure integrations."
        )

    def _log_msg(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self._log.append(f"[{ts}] {msg}")
