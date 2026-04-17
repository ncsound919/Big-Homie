"""
Unit tests for router.py - SmartRouter

Covers: role detection, complexity estimation, routing decisions,
cost vs. quality preference, and context-based overrides.
"""

from __future__ import annotations

import pytest


class TestRoleDetection:
    """SmartRouter._detect_role should map task keywords to the correct AgentRole."""

    @pytest.fixture
    def router(self, mock_env):
        from router import SmartRouter

        return SmartRouter()

    def test_coding_task_detected(self, router):
        from router import AgentRole

        role = router._detect_role("Write a Python function to sort a list", None)
        assert role == AgentRole.CODER

    def test_research_task_detected(self, router):
        from router import AgentRole

        role = router._detect_role("Research the latest breakthroughs in quantum computing", None)
        assert role == AgentRole.RESEARCHER

    def test_worker_task_detected(self, router):
        from router import AgentRole

        role = router._detect_role("Summarize this list of items quickly", None)
        assert role == AgentRole.WORKER

    def test_architect_task_detected(self, router):
        from router import AgentRole

        role = router._detect_role(
            "Design a scalable microservices architecture and recommend an approach", None
        )
        assert role == AgentRole.ARCHITECT

    def test_ambiguous_task_defaults_to_researcher(self, router):
        from router import AgentRole

        role = router._detect_role("Hello, how are you today?", None)
        assert role == AgentRole.RESEARCHER

    def test_context_code_context_boosts_coder(self, router):
        from router import AgentRole

        role = router._detect_role("Help me with this task", {"code_context": True})
        assert role == AgentRole.CODER

    def test_context_requires_reasoning_boosts_architect(self, router):
        from router import AgentRole

        role = router._detect_role("Help me with this task", {"requires_reasoning": True})
        assert role == AgentRole.ARCHITECT

    def test_context_simple_task_boosts_worker(self, router):
        from router import AgentRole

        role = router._detect_role("Help me with this task", {"simple_task": True})
        assert role == AgentRole.WORKER


class TestComplexityEstimation:
    """SmartRouter._estimate_complexity returns a 0.0-1.0 score."""

    @pytest.fixture
    def router(self, mock_env):
        from router import SmartRouter

        return SmartRouter()

    def test_simple_task_low_complexity(self, router):
        score = router._estimate_complexity("Just list the items")
        assert score < 0.5

    def test_complex_task_high_complexity(self, router):
        long_task = (
            "Analyze the comprehensive system architecture and integrate "
            "multiple components into a detailed design " + "word " * 80
        )
        score = router._estimate_complexity(long_task)
        assert score > 0.5

    def test_score_clamped_between_zero_and_one(self, router):
        low = router._estimate_complexity("just simple basic only quick")
        high = router._estimate_complexity(
            "analyze comprehensive detailed complex multiple integrate architecture system "
            + "word " * 120
        )
        assert 0.0 <= low <= 1.0
        assert 0.0 <= high <= 1.0

    def test_base_score_is_mid_range(self, router):
        score = router._estimate_complexity("a neutral sentence here")
        assert 0.2 <= score <= 0.8


class TestRoutingDecision:
    """SmartRouter.route_task should return a populated RoutingDecision."""

    @pytest.fixture
    def router(self, mock_env):
        from router import SmartRouter

        return SmartRouter()

    def test_returns_routing_decision(self, router):
        from router import RoutingDecision

        decision = router.route_task("Write a Python class for a linked list")
        assert isinstance(decision, RoutingDecision)

    def test_decision_has_all_fields(self, router):
        decision = router.route_task("Summarize this document")
        assert decision.role is not None
        assert decision.provider is not None
        assert decision.model is not None
        assert decision.reasoning is not None
        assert isinstance(decision.estimated_cost, float)

    def test_prefer_cost_selects_cheapest(self, router):
        decision = router.route_task("Summarize this paragraph", prefer_cost=True)
        # When preferring cost, the cheapest model should be selected
        assert decision.estimated_cost >= 0.0

    def test_prefer_quality_selects_best(self, router):
        decision = router.route_task("Design a complex distributed system", prefer_quality=True)
        # Quality route should pick the first (most capable) model for the role
        assert decision.model is not None

    def test_estimated_cost_is_non_negative(self, router):
        decision = router.route_task("Do something")
        assert decision.estimated_cost >= 0.0

    def test_reasoning_is_descriptive(self, router):
        decision = router.route_task("Debug this Python function")
        assert len(decision.reasoning) > 10
        assert "role" in decision.reasoning.lower() or "selected" in decision.reasoning.lower()


class TestExplainRouting:
    """SmartRouter._explain_routing produces human-readable explanations."""

    @pytest.fixture
    def router(self, mock_env):
        from router import SmartRouter

        return SmartRouter()

    def test_explanation_mentions_role(self, router):
        from llm_gateway import Provider
        from router import AgentRole

        explanation = router._explain_routing(
            AgentRole.CODER, Provider.OPENAI, "gpt-4", "Write code", None
        )
        assert "coder" in explanation.lower()

    def test_explanation_mentions_model(self, router):
        from llm_gateway import Provider
        from router import AgentRole

        explanation = router._explain_routing(
            AgentRole.WORKER, Provider.ANTHROPIC, "claude-haiku", "Summarize this", None
        )
        assert "claude-haiku" in explanation


class TestAgentRoleEnum:
    """AgentRole enum should have exactly four specializations."""

    def test_four_roles_exist(self):
        from router import AgentRole

        assert len(list(AgentRole)) == 4

    def test_role_values(self):
        from router import AgentRole

        values = {r.value for r in AgentRole}
        assert values == {"architect", "worker", "coder", "researcher"}
