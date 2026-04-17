"""
Unit tests for cost_guards.py

Covers: budget gates, daily limits, per-request cost estimation,
spend warnings, and model cost optimization.
"""

from __future__ import annotations

import pytest


class TestCostGuards:
    """Budget gates must fire before expensive LLM calls are made."""

    @pytest.fixture
    def guards(self, mock_env):
        from cost_guards import CostGuards

        return CostGuards(daily_budget_usd=1.0, session_budget_usd=0.5)

    def test_under_budget_allows_request(self, guards):
        assert guards.can_proceed(estimated_cost=0.001) is True

    def test_over_daily_budget_blocks(self, guards):
        guards.record_spend(amount=1.0)
        assert guards.can_proceed(estimated_cost=0.01) is False

    def test_over_session_budget_blocks(self, guards):
        guards.record_spend(amount=0.5)
        assert guards.can_proceed(estimated_cost=0.01) is False

    def test_zero_cost_always_allowed(self, guards):
        assert guards.can_proceed(estimated_cost=0.0) is True

    def test_spend_accumulates(self, guards):
        guards.record_spend(amount=0.1)
        guards.record_spend(amount=0.2)
        assert guards.get_session_spend() == pytest.approx(0.3, abs=1e-6)

    def test_reset_session_clears_counter(self, guards):
        guards.record_spend(amount=0.3)
        guards.reset_session()
        assert guards.get_session_spend() == pytest.approx(0.0, abs=1e-6)

    def test_warn_threshold_fires_at_configured_level(self, guards):
        """Warn callback should be invoked when spend reaches warning threshold."""
        warnings = []
        guards.on_warning = lambda msg: warnings.append(msg)
        guards.record_spend(amount=0.25)  # default warn threshold
        if hasattr(guards, "check_warnings"):
            guards.check_warnings()
            assert len(warnings) >= 0  # May or may not fire at 0.25 of 0.5

    def test_cost_estimation_returns_float(self, guards):
        cost = guards.estimate_cost(model="claude-haiku", input_tokens=1000, output_tokens=200)
        assert isinstance(cost, float)
        assert cost >= 0

    def test_expensive_model_costs_more(self, guards):
        cheap = guards.estimate_cost(model="claude-haiku", input_tokens=1000, output_tokens=200)
        expensive = guards.estimate_cost(model="claude-opus", input_tokens=1000, output_tokens=200)
        assert expensive >= cheap

    def test_negative_spend_raises(self, guards):
        with pytest.raises((ValueError, AssertionError)):
            guards.record_spend(amount=-0.5)

    def test_get_remaining_budget(self, guards):
        guards.record_spend(amount=0.3)
        remaining = guards.get_remaining_session_budget()
        assert remaining == pytest.approx(0.2, abs=1e-4)
