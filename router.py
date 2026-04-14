"""
Advanced LLM Router - Multi-model orchestration with role-based delegation
Architect (reasoning) / Worker (volume) / Coder (development) specialization
With thought logging, transparent routing decisions, and Karpathy temperature calibration
"""
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from loguru import logger
from llm_gateway import LLMGateway, Provider, TaskType
from config import settings

class AgentRole(str, Enum):
    """Specialized agent roles for different task types"""
    ARCHITECT = "architect"  # High-level reasoning, planning, strategy
    WORKER = "worker"        # High-volume, cheap tasks
    CODER = "coder"          # Software development, debugging
    RESEARCHER = "researcher" # Deep analysis, fact-checking

@dataclass
class RoutingDecision:
    """Result of routing decision"""
    role: AgentRole
    provider: Provider
    model: str
    reasoning: str
    estimated_cost: float

class SmartRouter:
    """
    Intelligent routing system that analyzes tasks and delegates to
    the most appropriate model based on complexity, cost, and specialization.
    Uses Karpathy temperature calibration for optimal sampling parameters.
    """

    def __init__(self):
        self.llm = LLMGateway()

        # Initialize thoughts logger if enabled
        if settings.enable_thought_logging:
            from thoughts_logger import thoughts_logger
            self.thoughts_logger = thoughts_logger
        else:
            self.thoughts_logger = None

        # Karpathy temperature calibrator (lazy-loaded to avoid circular imports)
        self._temperature_calibrator = None

        # Role-specific model configurations
        self.role_models = {
            AgentRole.ARCHITECT: [
                (Provider.ANTHROPIC, "claude-opus-4-5", 15.0),  # Best for reasoning
                (Provider.OPENAI, "gpt-4", 30.0),  # Fallback
            ],
            AgentRole.WORKER: [
                (Provider.ANTHROPIC, "claude-haiku", 0.25),  # Cheapest, fast
                (Provider.OPENAI, "gpt-4o-mini", 0.15),  # Alternative cheap
                (Provider.OLLAMA, "qwen2.5:7b", 0.0),  # Free local
            ],
            AgentRole.CODER: [
                (Provider.OPENAI, "gpt-4", 30.0),  # Best for code
                (Provider.ANTHROPIC, "claude-sonnet-4-5", 3.0),  # Alternative
                (Provider.OLLAMA, "deepseek-coder:6.7b", 0.0),  # Local coding
            ],
            AgentRole.RESEARCHER: [
                (Provider.ANTHROPIC, "claude-sonnet-4-5", 3.0),  # Best balance
                (Provider.OPENAI, "gpt-4", 30.0),  # Alternative
            ],
        }

        # Task patterns for automatic role detection
        self.task_patterns = {
            AgentRole.ARCHITECT: [
                "plan", "strategy", "design", "architecture", "approach",
                "should i", "how would you", "what's the best way",
                "analyze", "evaluate", "compare", "recommend"
            ],
            AgentRole.WORKER: [
                "summarize", "list", "extract", "convert", "format",
                "translate", "clean", "organize", "sort", "filter",
                "count", "aggregate", "simple", "quick"
            ],
            AgentRole.CODER: [
                "code", "function", "class", "debug", "fix bug",
                "implement", "write program", "script", "api",
                "refactor", "optimize code", "test", "algorithm"
            ],
            AgentRole.RESEARCHER: [
                "research", "find information", "what is", "explain",
                "investigate", "fact check", "learn about", "understand",
                "deep dive", "comprehensive", "detailed analysis"
            ],
        }

    def route_task(
        self,
        task: str,
        context: Optional[Dict] = None,
        prefer_cost: bool = False,
        prefer_quality: bool = False
    ) -> RoutingDecision:
        """
        Analyze task and route to appropriate model

        Args:
            task: The task description
            context: Additional context (user preferences, history, etc.)
            prefer_cost: Prioritize cost optimization
            prefer_quality: Prioritize highest quality (ignore cost)

        Returns:
            RoutingDecision with selected model and reasoning
        """
        # Detect role based on task content
        role = self._detect_role(task, context)

        # Get available models for this role
        available_models = self.role_models.get(role, self.role_models[AgentRole.WORKER])

        # Select model based on preferences
        if prefer_quality:
            # Use the first (highest quality) model
            provider, model, base_cost = available_models[0]
        elif prefer_cost:
            # Use the cheapest available model
            available_models_sorted = sorted(available_models, key=lambda x: x[2])
            provider, model, base_cost = available_models_sorted[0]
        else:
            # Balanced selection based on task complexity
            complexity = self._estimate_complexity(task)
            if complexity > 0.7:
                provider, model, base_cost = available_models[0]  # High quality
            elif complexity < 0.3:
                provider, model, base_cost = available_models[-1]  # Cheap
            else:
                provider, model, base_cost = available_models[min(1, len(available_models)-1)]  # Medium

        # Estimate actual cost based on task length
        estimated_tokens = len(task.split()) * 1.3  # Rough estimate
        estimated_cost = (estimated_tokens / 1000) * (base_cost / 1000)

        reasoning = self._explain_routing(role, provider, model, task, context)

        logger.info(f"Routed to {role.value}: {provider.value}/{model} (est. ${estimated_cost:.4f})")

        # Log routing decision as thought
        if self.thoughts_logger:
            self.thoughts_logger.log_decision(
                decision=f"Route to {role.value} role using {provider.value}/{model}",
                rationale=reasoning,
                metadata={
                    "estimated_cost": f"${estimated_cost:.4f}",
                    "complexity": f"{self._estimate_complexity(task):.2f}"
                }
            )

        return RoutingDecision(
            role=role,
            provider=provider,
            model=model,
            reasoning=reasoning,
            estimated_cost=estimated_cost
        )

    def _detect_role(self, task: str, context: Optional[Dict]) -> AgentRole:
        """Detect appropriate role based on task content"""
        task_lower = task.lower()

        # Score each role based on keyword matches
        scores = {role: 0 for role in AgentRole}

        for role, keywords in self.task_patterns.items():
            for keyword in keywords:
                if keyword in task_lower:
                    scores[role] += 1

        # Check context hints
        if context:
            if context.get("code_context"):
                scores[AgentRole.CODER] += 3
            if context.get("requires_reasoning"):
                scores[AgentRole.ARCHITECT] += 3
            if context.get("simple_task"):
                scores[AgentRole.WORKER] += 3

        # Return role with highest score, default to RESEARCHER
        max_role = max(scores, key=scores.get)
        if scores[max_role] == 0:
            return AgentRole.RESEARCHER  # Default for general questions

        return max_role

    def _estimate_complexity(self, task: str) -> float:
        """
        Estimate task complexity (0.0 - 1.0)
        Returns higher score for more complex tasks
        """
        complexity_score = 0.5  # Base score

        # Length contributes to complexity
        word_count = len(task.split())
        if word_count > 100:
            complexity_score += 0.2
        elif word_count < 20:
            complexity_score -= 0.2

        # Complexity indicators
        complex_words = ["analyze", "comprehensive", "detailed", "complex",
                        "multiple", "integrate", "architecture", "system"]
        simple_words = ["simple", "quick", "basic", "just", "only", "list"]

        task_lower = task.lower()
        for word in complex_words:
            if word in task_lower:
                complexity_score += 0.1

        for word in simple_words:
            if word in task_lower:
                complexity_score -= 0.1

        # Clamp to 0-1 range
        return max(0.0, min(1.0, complexity_score))

    def _explain_routing(
        self,
        role: AgentRole,
        provider: Provider,
        model: str,
        task: str,
        context: Optional[Dict]
    ) -> str:
        """Generate human-readable explanation of routing decision"""
        role_descriptions = {
            AgentRole.ARCHITECT: "high-level reasoning and strategic planning",
            AgentRole.WORKER: "efficient processing of straightforward tasks",
            AgentRole.CODER: "software development and technical implementation",
            AgentRole.RESEARCHER: "deep analysis and information synthesis"
        }

        return (
            f"Selected {role.value} role for {role_descriptions[role]}. "
            f"Using {provider.value}/{model} as the optimal model for this task type."
        )

    def _get_temperature_calibrator(self):
        """Lazy-load temperature calibrator to avoid circular imports."""
        if self._temperature_calibrator is None:
            try:
                from karpathy_methods import TemperatureCalibrator
                self._temperature_calibrator = TemperatureCalibrator()
            except ImportError:
                self._temperature_calibrator = None
        return self._temperature_calibrator

    def get_calibrated_temperature(self, task: str, role: "AgentRole") -> float:
        """
        Get Karpathy-calibrated temperature for a task + role combination.
        Falls back to settings.temperature if calibrator not available.
        """
        calibrator = self._get_temperature_calibrator()
        if calibrator is None:
            return settings.temperature

        # Role takes precedence over task-nature for structured roles
        role_temp = calibrator.get_temperature_for_role(role.value)

        # For RESEARCHER/ARCHITECT, also consider task nature
        if role in (AgentRole.RESEARCHER, AgentRole.ARCHITECT):
            nature_temp = calibrator.get_temperature(task)
            # Blend: 60% role, 40% nature
            return round(role_temp * 0.6 + nature_temp * 0.4, 2)

        return role_temp

    async def execute_with_routing(
        self,
        task: str,
        context: Optional[Dict] = None,
        **kwargs
    ) -> Tuple[RoutingDecision, Dict[str, Any]]:
        """
        Route task and execute with selected model.
        Applies Karpathy temperature calibration unless temperature is explicitly provided.

        Returns:
            Tuple of (routing decision, LLM response)
        """
        # Get routing decision
        decision = self.route_task(task, context, **kwargs)

        # Apply Karpathy temperature calibration if not already set
        if "temperature" not in kwargs:
            calibrated_temp = self.get_calibrated_temperature(task, decision.role)
            kwargs["temperature"] = calibrated_temp
            logger.debug(
                f"Karpathy temperature calibration: {calibrated_temp} "
                f"for {decision.role.value} role"
            )

        # Allow context to supply a system prompt override (used by ScratchpadReasoner etc.)
        system_content = self._get_role_prompt(decision.role)
        if context and context.get("system_override"):
            system_content = context["system_override"]

        # Prepare messages
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": task}
        ]

        # Execute with the routed provider/model while keeping the existing
        # task type mapping for any downstream behavior that still depends on it.
        task_type_map = {
            AgentRole.ARCHITECT: TaskType.REASONING,
            AgentRole.WORKER: TaskType.FAST,
            AgentRole.CODER: TaskType.CODING,
            AgentRole.RESEARCHER: TaskType.GENERAL,
        }
        completion_kwargs = dict(kwargs)
        completion_kwargs.setdefault("provider", decision.provider)
        completion_kwargs.setdefault("model", decision.model)

        result = await self.llm.complete(
            messages,
            task_type=task_type_map[decision.role],
            **completion_kwargs
        )

        return decision, result

    def _get_role_prompt(self, role: AgentRole) -> str:
        """Get specialized system prompt for each role"""
        prompts = {
            AgentRole.ARCHITECT: """You are the Architect - responsible for high-level reasoning, strategic planning, and complex problem decomposition.

Your strengths:
- Breaking down complex problems into manageable steps
- Designing optimal system architectures
- Strategic decision making
- Evaluating trade-offs and recommending best approaches

Approach:
1. Understand the full scope and context
2. Consider multiple approaches
3. Recommend the optimal strategy
4. Provide clear reasoning for your decisions""",

            AgentRole.WORKER: """You are the Worker - responsible for efficient execution of straightforward, high-volume tasks.

Your strengths:
- Fast, accurate data processing
- Summarization and extraction
- Format conversion and data cleaning
- High-volume operations

Approach:
1. Execute tasks directly and efficiently
2. Focus on accuracy and completeness
3. Minimize unnecessary elaboration
4. Deliver results quickly""",

            AgentRole.CODER: """You are the Coder - responsible for software development, debugging, and technical implementation.

Your strengths:
- Writing clean, efficient code
- Debugging and problem solving
- Following best practices and patterns
- Optimizing performance

Approach:
1. Write production-quality code
2. Include proper error handling
3. Add clear comments for complex logic
4. Consider edge cases and security""",

            AgentRole.RESEARCHER: """You are the Researcher - responsible for deep analysis, fact-checking, and information synthesis.

Your strengths:
- Thorough investigation of topics
- Critical analysis and fact-checking
- Synthesizing information from multiple sources
- Providing comprehensive understanding

Approach:
1. Investigate thoroughly and systematically
2. Verify facts and cite sources when possible
3. Provide balanced, nuanced analysis
4. Identify knowledge gaps and uncertainties"""
        }

        return prompts.get(role, prompts[AgentRole.RESEARCHER])

# Global router instance
router = SmartRouter()
