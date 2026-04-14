"""
Secure Financial Settings Widget
A categorized, password-masked settings panel for financial integrations.
Reads from and writes to the .env file. Sensitive values are masked in the UI
but are stored in the .env file without encryption.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QDoubleSpinBox,
    QComboBox,
    QSpinBox,
)
from loguru import logger

# ─── Field descriptor ────────────────────────────────────────────────────────


class FieldDef:
    """Describes one settings field"""
    def __init__(
        self,
        env_key: str,
        label: str,
        sensitive: bool = False,
        placeholder: str = "",
        widget_type: str = "text",   # text | bool | float | int | combo
        choices: Optional[List[str]] = None,
        min_val: float = 0.0,
        max_val: float = 1_000_000.0,
        decimals: int = 2,
        step: float = 1.0,
        tooltip: str = "",
    ):
        self.env_key = env_key
        self.label = label
        self.sensitive = sensitive
        self.placeholder = placeholder
        self.widget_type = widget_type
        self.choices = choices or []
        self.min_val = min_val
        self.max_val = max_val
        self.decimals = decimals
        self.step = step
        self.tooltip = tooltip


# ─── Section definitions ─────────────────────────────────────────────────────

SECTIONS: Dict[str, List[Tuple[str, List[FieldDef]]]] = {
    "🏦 Banking": [
        ("Plaid (Bank Account Linking)", [
            FieldDef("PLAID_CLIENT_ID",  "Client ID",       sensitive=True,  placeholder="Plaid client_id"),
            FieldDef("PLAID_SECRET",     "Secret",          sensitive=True,  placeholder="Plaid secret"),
            FieldDef("PLAID_ENV",        "Environment",     widget_type="combo",
                     choices=["sandbox", "development", "production"]),
            FieldDef("PLAID_ENABLED",    "Enabled",         widget_type="bool"),
        ]),
    ],

    "📈 Trading": [
        ("Alpaca (Stocks / ETFs)", [
            FieldDef("ALPACA_API_KEY",    "API Key",        sensitive=True,  placeholder="pk_..."),
            FieldDef("ALPACA_SECRET_KEY", "Secret Key",     sensitive=True,  placeholder="alpaca secret"),
            FieldDef("ALPACA_BASE_URL",   "Base URL",       placeholder="https://paper-api.alpaca.markets"),
        ]),
        ("Interactive Brokers (IBKR)", [
            FieldDef("IBKR_HOST",      "TWS/Gateway Host", placeholder="127.0.0.1"),
            FieldDef("IBKR_PORT",      "Port",             widget_type="int", min_val=1, max_val=65535, step=1,
                     tooltip="7497=paper, 7496=live"),
            FieldDef("IBKR_CLIENT_ID", "Client ID",        widget_type="int", min_val=0, max_val=999, step=1),
            FieldDef("IBKR_ENABLED",   "Enabled",          widget_type="bool"),
        ]),
        ("Schwab (Options / Stocks)", [
            FieldDef("SCHWAB_CLIENT_ID",     "Client ID",       sensitive=True),
            FieldDef("SCHWAB_CLIENT_SECRET", "Client Secret",   sensitive=True),
            FieldDef("SCHWAB_REDIRECT_URI",  "Redirect URI",    placeholder="https://127.0.0.1"),
            FieldDef("SCHWAB_ENABLED",       "Enabled",         widget_type="bool"),
        ]),
    ],

    "₿ Crypto": [
        ("Binance", [
            FieldDef("BINANCE_API_KEY",    "API Key",        sensitive=True),
            FieldDef("BINANCE_SECRET_KEY", "Secret Key",     sensitive=True),
            FieldDef("BINANCE_TESTNET",    "Use Testnet",    widget_type="bool"),
            FieldDef("BINANCE_ENABLED",    "Enabled",        widget_type="bool"),
        ]),
        ("Kraken", [
            FieldDef("KRAKEN_API_KEY",     "API Key",        sensitive=True),
            FieldDef("KRAKEN_PRIVATE_KEY", "Private Key",    sensitive=True),
            FieldDef("KRAKEN_ENABLED",     "Enabled",        widget_type="bool"),
        ]),
        ("Coinbase Advanced Trade", [
            FieldDef("COINBASE_ADV_API_KEY", "API Key",      sensitive=True),
            FieldDef("COINBASE_ADV_SECRET",  "Secret",       sensitive=True),
            FieldDef("COINBASE_ADV_ENABLED", "Enabled",      widget_type="bool"),
        ]),
        ("Base L2 (Ethereum)", [
            FieldDef("BASE_RPC_URL",            "RPC URL",         placeholder="https://mainnet.base.org"),
            FieldDef("BASE_WALLET_ADDRESS",     "Wallet Address",  sensitive=True),
            FieldDef("BASE_WALLET_PRIVATE_KEY", "Private Key",     sensitive=True,
                     tooltip="⚠ Never share your private key"),
            FieldDef("BASE_ENABLED",            "Enabled",         widget_type="bool"),
        ]),
        ("Coinbase Commerce (Payments)", [
            FieldDef("COINBASE_COMMERCE_API_KEY",        "API Key",        sensitive=True),
            FieldDef("COINBASE_COMMERCE_WEBHOOK_SECRET", "Webhook Secret", sensitive=True),
            FieldDef("COINBASE_COMMERCE_ENABLED",        "Enabled",        widget_type="bool"),
        ]),
    ],

    "🎰 Betting": [
        ("DraftKings", [
            FieldDef("DRAFTKINGS_API_KEY", "API Key",  sensitive=True),
            FieldDef("DRAFTKINGS_ENABLED", "Enabled",  widget_type="bool"),
        ]),
        ("PrizePicks", [
            FieldDef("PRIZEPICKS_API_KEY", "API Key",  sensitive=True),
            FieldDef("PRIZEPICKS_ENABLED", "Enabled",  widget_type="bool"),
        ]),
        ("FanDuel", [
            FieldDef("FANDUEL_API_KEY", "API Key",     sensitive=True),
            FieldDef("FANDUEL_ENABLED", "Enabled",     widget_type="bool"),
        ]),
        ("The Odds API (Lines Aggregator)", [
            FieldDef("ODDS_API_KEY",     "API Key",    sensitive=True,  placeholder="odds-api.com key"),
            FieldDef("ODDS_API_ENABLED", "Enabled",    widget_type="bool"),
        ]),
    ],

    "💼 Job / Task Platforms": [
        ("Upwork", [
            FieldDef("UPWORK_CLIENT_ID",     "Client ID",     sensitive=True),
            FieldDef("UPWORK_CLIENT_SECRET", "Client Secret", sensitive=True),
            FieldDef("UPWORK_ENABLED",       "Enabled",       widget_type="bool"),
        ]),
        ("Fiverr", [
            FieldDef("FIVERR_API_KEY", "API Key",  sensitive=True),
            FieldDef("FIVERR_ENABLED", "Enabled",  widget_type="bool"),
        ]),
        ("Amazon Mechanical Turk", [
            FieldDef("MTURK_ACCESS_KEY", "Access Key", sensitive=True),
            FieldDef("MTURK_SECRET_KEY", "Secret Key", sensitive=True),
            FieldDef("MTURK_SANDBOX",    "Sandbox",    widget_type="bool"),
            FieldDef("MTURK_ENABLED",    "Enabled",    widget_type="bool"),
        ]),
    ],

    "🛒 Ecommerce / SaaS": [
        ("Shopify", [
            FieldDef("SHOPIFY_SHOP_DOMAIN",   "Shop Domain",    placeholder="my-store.myshopify.com"),
            FieldDef("SHOPIFY_ACCESS_TOKEN",  "Access Token",   sensitive=True),
            FieldDef("SHOPIFY_ENABLED",       "Enabled",        widget_type="bool"),
        ]),
        ("WooCommerce", [
            FieldDef("WOOCOMMERCE_URL",              "Store URL",       placeholder="https://myshop.com"),
            FieldDef("WOOCOMMERCE_CONSUMER_KEY",     "Consumer Key",    sensitive=True),
            FieldDef("WOOCOMMERCE_CONSUMER_SECRET",  "Consumer Secret", sensitive=True),
            FieldDef("WOOCOMMERCE_ENABLED",          "Enabled",         widget_type="bool"),
        ]),
        ("Amazon Seller (SP-API)", [
            FieldDef("AMAZON_SELLER_ID",         "Seller ID",        sensitive=True),
            FieldDef("AMAZON_SP_CLIENT_ID",      "Client ID",        sensitive=True),
            FieldDef("AMAZON_SP_CLIENT_SECRET",  "Client Secret",    sensitive=True),
            FieldDef("AMAZON_SP_REFRESH_TOKEN",  "Refresh Token",    sensitive=True),
            FieldDef("AMAZON_SP_ENABLED",        "Enabled",          widget_type="bool"),
        ]),
        ("Stripe (Payments / SaaS)", [
            FieldDef("STRIPE_API_KEY",        "API Key",        sensitive=True, placeholder="sk_live_..."),
            FieldDef("STRIPE_WEBHOOK_SECRET", "Webhook Secret", sensitive=True, placeholder="whsec_..."),
            FieldDef("STRIPE_ENABLED",        "Enabled",        widget_type="bool"),
        ]),
        ("SaaS / MaaS Config", [
            FieldDef("SAAS_DEPLOY_ENABLED",  "SaaS Deploy Enabled",  widget_type="bool"),
            FieldDef("SAAS_STRIPE_PRICE_ID", "Default Price ID",     placeholder="price_..."),
            FieldDef("SAAS_TRIAL_DAYS",      "Trial Days",            widget_type="int", min_val=0, max_val=365, step=1),
            FieldDef("MAAS_MODEL_ENDPOINT",  "MaaS Endpoint URL",    placeholder="https://..."),
            FieldDef("MAAS_API_KEY_HEADER",  "Auth Header Name",     placeholder="X-API-Key"),
        ]),
    ],

    "🚚 Supply Chain": [
        ("ShipStation", [
            FieldDef("SHIPSTATION_API_KEY",    "API Key",    sensitive=True),
            FieldDef("SHIPSTATION_API_SECRET", "API Secret", sensitive=True),
            FieldDef("SHIPSTATION_ENABLED",    "Enabled",    widget_type="bool"),
        ]),
        ("EasyPost (Shipping)", [
            FieldDef("EASYPOST_API_KEY", "API Key",  sensitive=True),
            FieldDef("EASYPOST_ENABLED", "Enabled",  widget_type="bool"),
        ]),
    ],

    "📞 Call Center": [
        ("Twilio (Voice / SMS)", [
            FieldDef("TWILIO_ACCOUNT_SID",  "Account SID",   sensitive=True,  placeholder="ACxxxxxxxx"),
            FieldDef("TWILIO_AUTH_TOKEN",   "Auth Token",    sensitive=True),
            FieldDef("TWILIO_PHONE_NUMBER", "Phone Number",  placeholder="+15551234567"),
            FieldDef("TWILIO_ENABLED",      "Enabled",       widget_type="bool"),
        ]),
    ],

    "🔌 API / MCP": [
        ("MCP (Model Context Protocol)", [
            FieldDef("MCP_SERVER_URLS",  "Server URLs",   placeholder="http://host1:port,http://host2:port"),
            FieldDef("MCP_AUTH_TOKENS",  "Auth Tokens",   sensitive=True, placeholder="token1,token2"),
            FieldDef("MCP_ENABLED",      "Enabled",       widget_type="bool"),
        ]),
        ("SerpAPI (Web Search)", [
            FieldDef("SERP_API_KEY", "API Key", sensitive=True),
        ]),
        ("Perplexity AI", [
            FieldDef("PERPLEXITY_API_KEY", "API Key",  sensitive=True),
            FieldDef("PERPLEXITY_ENABLED", "Enabled",  widget_type="bool"),
        ]),
        ("HuggingFace", [
            FieldDef("HUGGINGFACE_API_KEY", "API Key",  sensitive=True),
            FieldDef("HUGGINGFACE_ENABLED", "Enabled",  widget_type="bool"),
        ]),
    ],

    "🚀 Revenue Engine": [
        ("Goals & Risk", [
            FieldDef("REVENUE_ENGINE_ENABLED",       "Engine Enabled",          widget_type="bool"),
            FieldDef("REVENUE_GOAL_DAILY_USD",       "Daily Goal ($)",          widget_type="float",
                     min_val=0, max_val=100_000, decimals=2, step=10.0),
            FieldDef("REVENUE_GOAL_MONTHLY_USD",     "Monthly Goal ($)",        widget_type="float",
                     min_val=0, max_val=1_000_000, decimals=2, step=100.0),
            FieldDef("REVENUE_MAX_SINGLE_TRADE_USD", "Max Single Trade ($)",    widget_type="float",
                     min_val=0, max_val=100_000, decimals=2, step=10.0,
                     tooltip="Hard cap per automated trade or bet"),
            FieldDef("REVENUE_RISK_LEVEL",           "Risk Level",              widget_type="combo",
                     choices=["low", "medium", "high"]),
            FieldDef("REVENUE_AUTO_REINVEST_PCT",    "Auto-Reinvest (%)",       widget_type="float",
                     min_val=0, max_val=100, decimals=1, step=5.0),
            FieldDef("REVENUE_REPORT_INTERVAL_HOURS","Report Interval (hrs)",   widget_type="int",
                     min_val=1, max_val=168, step=1),
        ]),
        ("Active Streams", [
            FieldDef("REVENUE_ACTIVE_STREAMS", "Active Streams",
                     placeholder="trading,crypto,betting,ecommerce,saas,call_center",
                     tooltip="Comma-separated list of enabled revenue streams"),
        ]),
    ],
}


# ─── Settings Widget ──────────────────────────────────────────────────────────


class SecureFinancialSettings(QWidget):
    """
    Tabbed financial settings panel.

    • All sensitive fields are masked by default (show/hide toggle)
    • Values are loaded from and saved to the .env file
    • No secrets are ever logged
    """

    settings_saved = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._env_path = Path(__file__).parent / ".env"
        self._widgets: Dict[str, QWidget] = {}   # env_key -> input widget
        self._env_data: Dict[str, str] = {}       # full .env contents as dict
        self._build_ui()
        self._load_env()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("🔐  Secure Financial Settings")
        title.setFont(QFont("", 14, QFont.Weight.Bold))
        hdr.addWidget(title)
        hdr.addStretch()

        self._reveal_btn = QPushButton("👁  Show Secrets")
        self._reveal_btn.setCheckable(True)
        self._reveal_btn.toggled.connect(self._toggle_reveal)
        hdr.addWidget(self._reveal_btn)

        save_btn = QPushButton("💾  Save All")
        save_btn.clicked.connect(self._save_settings)
        save_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 6px 16px;")
        hdr.addWidget(save_btn)

        root.addLayout(hdr)

        # Warning banner
        warn = QLabel(
            "⚠  Secrets are stored in your local .env file. "
            "Never share that file or commit it to version control."
        )
        warn.setStyleSheet("color: #FFC107; font-style: italic; padding: 4px;")
        warn.setWordWrap(True)
        root.addWidget(warn)

        # Tab widget
        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.TabPosition.North)

        for tab_name, groups in SECTIONS.items():
            tab_widget = self._build_tab(groups)
            self._tabs.addTab(tab_widget, tab_name)

        root.addWidget(self._tabs, 1)

    def _build_tab(self, groups: List[Tuple[str, List[FieldDef]]]) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        for group_name, fields in groups:
            box = QGroupBox(group_name)
            form = QFormLayout(box)
            form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

            for fdef in fields:
                widget = self._make_widget(fdef)
                self._widgets[fdef.env_key] = widget
                label = QLabel(fdef.label)
                if fdef.tooltip:
                    label.setToolTip(fdef.tooltip)
                    widget.setToolTip(fdef.tooltip)
                if fdef.sensitive and isinstance(widget, QLineEdit):
                    # Wrap in h-layout with eye toggle
                    row = QWidget()
                    row_lay = QHBoxLayout(row)
                    row_lay.setContentsMargins(0, 0, 0, 0)
                    row_lay.addWidget(widget)
                    eye = QPushButton("👁")
                    eye.setFixedWidth(30)
                    eye.setCheckable(True)
                    eye.setStyleSheet("border: none; background: transparent;")
                    eye.toggled.connect(lambda checked, w=widget: self._set_echo(w, checked))
                    row_lay.addWidget(eye)
                    form.addRow(label, row)
                else:
                    form.addRow(label, widget)

            layout.addWidget(box)

        scroll.setWidget(inner)
        return scroll

    def _make_widget(self, fdef: FieldDef) -> QWidget:
        if fdef.widget_type == "bool":
            w = QCheckBox()
            return w
        if fdef.widget_type == "float":
            w = QDoubleSpinBox()
            w.setRange(fdef.min_val, fdef.max_val)
            w.setDecimals(fdef.decimals)
            w.setSingleStep(fdef.step)
            w.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            return w
        if fdef.widget_type == "int":
            w = QSpinBox()
            w.setRange(int(fdef.min_val), int(fdef.max_val))
            w.setSingleStep(int(fdef.step))
            w.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            return w
        if fdef.widget_type == "combo":
            w = QComboBox()
            for choice in fdef.choices:
                w.addItem(choice)
            return w
        # default: text
        w = QLineEdit()
        if fdef.sensitive:
            w.setEchoMode(QLineEdit.EchoMode.Password)
        if fdef.placeholder:
            w.setPlaceholderText(fdef.placeholder)
        w.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return w

    # ── Reveal / Hide ─────────────────────────────────────────────────────────

    def _set_echo(self, widget: QLineEdit, show: bool):
        widget.setEchoMode(
            QLineEdit.EchoMode.Normal if show else QLineEdit.EchoMode.Password
        )

    def _toggle_reveal(self, show: bool):
        self._reveal_btn.setText("🙈  Hide Secrets" if show else "👁  Show Secrets")
        for env_key, widget in self._widgets.items():
            if isinstance(widget, QLineEdit):
                # Check if this field is sensitive
                fdef = self._find_fdef(env_key)
                if fdef and fdef.sensitive:
                    self._set_echo(widget, show)

    def _find_fdef(self, env_key: str) -> Optional[FieldDef]:
        for groups in SECTIONS.values():
            for _, fields in groups:
                for fdef in fields:
                    if fdef.env_key == env_key:
                        return fdef
        return None

    # ── Load / Save .env ──────────────────────────────────────────────────────

    def _load_env(self):
        """Load current .env file into widget values"""
        self._env_data = {}
        if self._env_path.exists():
            with open(self._env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.rstrip("\n")
                    if line.startswith("#") or "=" not in line:
                        continue
                    key, _, val = line.partition("=")
                    self._env_data[key.strip()] = val.strip()

        for env_key, widget in self._widgets.items():
            raw = self._env_data.get(env_key, "")
            self._set_widget_value(widget, env_key, raw)

    def _set_widget_value(self, widget: QWidget, env_key: str, raw: str):
        if isinstance(widget, QCheckBox):
            widget.setChecked(raw.lower() in ("true", "1", "yes"))
        elif isinstance(widget, QDoubleSpinBox):
            try:
                widget.setValue(float(raw) if raw else 0.0)
            except ValueError:
                widget.setValue(0.0)
        elif isinstance(widget, QSpinBox):
            try:
                widget.setValue(int(raw) if raw else 0)
            except ValueError:
                widget.setValue(0)
        elif isinstance(widget, QComboBox):
            idx = widget.findText(raw, Qt.MatchFlag.MatchFixedString)
            if idx >= 0:
                widget.setCurrentIndex(idx)
        elif isinstance(widget, QLineEdit):
            widget.setText(raw)

    def _get_widget_value(self, widget: QWidget) -> str:
        if isinstance(widget, QCheckBox):
            return "true" if widget.isChecked() else "false"
        if isinstance(widget, QDoubleSpinBox):
            return str(widget.value())
        if isinstance(widget, QSpinBox):
            return str(widget.value())
        if isinstance(widget, QComboBox):
            return widget.currentText()
        if isinstance(widget, QLineEdit):
            return widget.text()
        return ""

    def _save_settings(self):
        """Persist all widget values back to .env"""
        # Read existing .env preserving comments and order
        existing_lines: List[str] = []
        if self._env_path.exists():
            with open(self._env_path, "r", encoding="utf-8") as f:
                existing_lines = f.readlines()

        # Build a map of key -> line-index for existing lines.
        # We only match lines that set a key (not comment lines) and we keep
        # track of any inline comment so we can restore it after updating.
        key_line: Dict[str, int] = {}
        key_comment: Dict[str, str] = {}   # optional inline comment per key
        for i, line in enumerate(existing_lines):
            stripped = line.rstrip("\n")
            if not stripped or stripped.lstrip().startswith("#"):
                continue
            if "=" not in stripped:
                continue
            k, _, rest = stripped.partition("=")
            k = k.strip()
            # Detect an inline comment: unquoted `#` after the value
            # Simple heuristic: if the value is not quoted and contains ` #`
            inline_comment = ""
            val_part = rest
            if not (rest.startswith('"') or rest.startswith("'")):
                comment_idx = rest.find(" #")
                if comment_idx != -1:
                    val_part = rest[:comment_idx]
                    inline_comment = rest[comment_idx:]
            key_line[k] = i
            key_comment[k] = inline_comment

        def _quote_value(v: str) -> str:
            """Quote a value if it contains characters that need protection."""
            # Quote if value contains: spaces, #, $, quotes, backslashes
            if not v:
                return v
            needs_quoting = any(c in v for c in ' #$"\'\\')
            if needs_quoting:
                # Double-quote, escaping inner double-quotes and backslashes
                escaped = v.replace("\\", "\\\\").replace('"', '\\"')
                return f'"{escaped}"'
            return v

        # Apply widget values
        for env_key, widget in self._widgets.items():
            value = self._get_widget_value(widget)
            quoted = _quote_value(value)
            comment = key_comment.get(env_key, "")
            new_line = f"{env_key}={quoted}{comment}\n"
            if env_key in key_line:
                existing_lines[key_line[env_key]] = new_line
            else:
                existing_lines.append(new_line)

        try:
            with open(self._env_path, "w", encoding="utf-8") as f:
                f.writelines(existing_lines)
            logger.info("Financial settings saved to .env")
            QMessageBox.information(
                self,
                "Settings Saved",
                "All financial settings have been saved to your .env file.\n\n"
                "Restart Big Homie to apply changes.",
            )
            self.settings_saved.emit()
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            QMessageBox.critical(self, "Save Failed", f"Could not write .env file:\n{e}")

    def reload(self):
        """Reload settings from disk (discards unsaved changes)"""
        self._load_env()

    # ── Status Summary ────────────────────────────────────────────────────────

    def get_integration_status(self) -> Dict[str, bool]:
        """Return dict of integration_name -> is_enabled (from current widget state)"""
        status: Dict[str, bool] = {}
        enabled_keys = [k for k in self._widgets if k.endswith("_ENABLED")]
        for k in enabled_keys:
            w = self._widgets[k]
            name = k.replace("_ENABLED", "").lower()
            status[name] = (
                w.isChecked() if isinstance(w, QCheckBox) else
                self._get_widget_value(w).lower() == "true"
            )
        return status
