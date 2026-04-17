"""
Shared pytest fixtures for Big Homie test suite.
Covers governance, memory, cost guards, and agent lifecycle.
"""
from __future__ import annotations

import os
import sys
import tempfile
import pytest

# Make root modules importable from tests
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture(scope="session")
def temp_dir():
    """Provide a temporary directory that persists for the test session."""
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def tmp_db(tmp_path):
    """Provide a fresh SQLite DB path per test."""
    return str(tmp_path / "test_memory.db")


@pytest.fixture
def mock_env(monkeypatch):
    """Provide a minimal set of env vars so modules don't crash on import."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-000")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-000")
    monkeypatch.setenv("HEARTBEAT_ENABLED", "false")
    monkeypatch.setenv("MAX_AUTONOMOUS_COST", "1.0")
    monkeypatch.setenv("DAILY_BUDGET_USD", "1.0")
    return monkeypatch


@pytest.fixture
def audit_trail(tmp_path):
    """Return a fresh AuditTrail instance backed by a temp file."""
    from governance import AuditTrail
    log_file = str(tmp_path / "audit.jsonl")
    return AuditTrail(log_file=log_file)


@pytest.fixture
def kill_switch(tmp_path):
    """Return a fresh KillSwitch instance."""
    from governance import KillSwitch
    state_file = str(tmp_path / "kill_state.json")
    return KillSwitch(state_file=state_file)


@pytest.fixture
def sandbox():
    """Return a SandboxedExecution instance with default config."""
    from governance import SandboxedExecution, SandboxConfig
    return SandboxedExecution(config=SandboxConfig())


@pytest.fixture
def human_gate():
    """Return a HumanInTheLoop instance."""
    from governance import HumanInTheLoop
    return HumanInTheLoop(auto_approve_low_risk=True)
