"""
Unit tests for governance.py - Claw Protect

Covers: AuditTrail, HumanInTheLoop, SandboxedExecution, RiskLevel
"""

from __future__ import annotations

import json

import pytest

# ---------------------------------------------------------------------------
# AuditTrail tests
# ---------------------------------------------------------------------------


class TestAuditTrail:
    """AuditTrail should record, chain, and verify log integrity."""

    def test_log_entry_creates_file(self, audit_trail, tmp_path):
        audit_trail.log(action="test_action", details={"key": "value"})
        log_file = tmp_path / "audit.jsonl"
        assert log_file.exists()

    def test_log_entry_has_required_fields(self, audit_trail, tmp_path):
        audit_trail.log(action="create_file", details={"path": "/tmp/x"})
        log_file = tmp_path / "audit.jsonl"
        entries = [json.loads(line) for line in log_file.read_text().splitlines() if line]
        entry = entries[-1]
        assert "action" in entry
        assert "timestamp" in entry
        assert "hash" in entry

    def test_chain_integrity_valid(self, audit_trail):
        audit_trail.log(action="step1", details={})
        audit_trail.log(action="step2", details={})
        audit_trail.log(action="step3", details={})
        assert audit_trail.verify_integrity() is True

    def test_chain_integrity_detects_tampering(self, audit_trail, tmp_path):
        audit_trail.log(action="step1", details={})
        audit_trail.log(action="step2", details={})
        # Tamper with the log file
        log_file = tmp_path / "audit.jsonl"
        lines = log_file.read_text().splitlines()
        if lines:
            entry = json.loads(lines[0])
            entry["action"] = "TAMPERED"
            lines[0] = json.dumps(entry)
            log_file.write_text("\n".join(lines))
        assert audit_trail.verify_integrity() is False

    def test_empty_trail_is_valid(self, audit_trail):
        assert audit_trail.verify_integrity() is True

    def test_log_multiple_entries(self, audit_trail):
        for i in range(10):
            audit_trail.log(action=f"action_{i}", details={"index": i})
        entries = audit_trail.get_entries()
        assert len(entries) == 10


# ---------------------------------------------------------------------------
# HumanInTheLoop tests
# ---------------------------------------------------------------------------


class TestHumanInTheLoop:
    """HumanInTheLoop should correctly classify risk tiers."""

    def test_low_risk_classification(self, human_gate):
        from governance import RiskLevel

        risk = human_gate.classify_risk(action="read_file", context={})
        assert risk in (RiskLevel.LOW, RiskLevel.MEDIUM)

    def test_high_risk_financial(self, human_gate):
        from governance import RiskLevel

        risk = human_gate.classify_risk(
            action="transfer_funds", context={"amount": 10000, "target": "external_account"}
        )
        assert risk in (RiskLevel.HIGH, RiskLevel.CRITICAL)

    def test_critical_risk_delete_all(self, human_gate):
        from governance import RiskLevel

        risk = human_gate.classify_risk(action="delete_all_data", context={"scope": "production"})
        assert risk == RiskLevel.CRITICAL

    def test_auto_approve_low_risk(self, human_gate):
        """Low-risk actions should be auto-approved when flag is set."""
        from governance import RiskLevel

        approved = human_gate.request_approval(
            action="read_config", context={}, risk_level=RiskLevel.LOW
        )
        assert approved is True

    def test_four_risk_tiers_exist(self):
        from governance import RiskLevel

        levels = list(RiskLevel)
        assert len(levels) == 4


# ---------------------------------------------------------------------------
# SandboxedExecution tests
# ---------------------------------------------------------------------------


class TestSandboxedExecution:
    """SandboxedExecution should block dangerous commands and env variables."""

    def test_safe_command_allowed(self, sandbox):
        result = sandbox.execute(command="echo hello")
        assert result is not None

    def test_blocked_command_raises(self, sandbox):
        with pytest.raises((PermissionError, ValueError, RuntimeError)):
            sandbox.execute(command="rm -rf /")

    def test_api_key_not_in_env(self, sandbox, mock_env):
        """API keys must never be passed to sandboxed processes."""
        env = sandbox.get_safe_env()
        assert "ANTHROPIC_API_KEY" not in env
        assert "OPENAI_API_KEY" not in env
        assert "STRIPE_API_KEY" not in env

    def test_blocked_import_in_code(self, sandbox):
        """Code importing os.system or subprocess.shell should be blocked."""
        dangerous_code = "import subprocess; subprocess.run('rm -rf /', shell=True)"
        with pytest.raises((PermissionError, ValueError, RuntimeError)):
            sandbox.execute_code(code=dangerous_code)

    def test_sandbox_config_has_allowlist(self, sandbox):
        assert hasattr(sandbox, "config")
        assert hasattr(sandbox.config, "allowed_commands") or hasattr(
            sandbox.config, "blocked_commands"
        )
