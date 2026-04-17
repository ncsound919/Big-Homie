"""
Cost Guards Module
Budget management, throttling, and cost estimation for LLM operations
"""

import asyncio
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any, Callable, Optional

from loguru import logger

from config import settings

try:
    import tiktoken

    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    logger.warning("tiktoken not available - token counting will be approximate")


class CostLevel(str, Enum):
    """Cost threshold levels"""

    LOW = "low"  # < $0.10
    MEDIUM = "medium"  # $0.10 - $0.50
    HIGH = "high"  # $0.50 - $2.00
    VERY_HIGH = "very_high"  # > $2.00


@dataclass
class CostEstimate:
    """Estimated cost for an operation"""

    input_tokens: int
    output_tokens_estimated: int
    total_tokens: int
    estimated_cost: float
    cost_level: CostLevel
    model: str
    requires_approval: bool


@dataclass
class BudgetStatus:
    """Current budget status"""

    daily_limit: float
    daily_spent: float
    daily_remaining: float
    session_spent: float
    last_reset: date
    is_over_budget: bool
    warning_threshold_reached: bool


class CostGuard:
    """
    Cost guard system for budget management and throttling

    Features:
    - Pre-execution cost estimation
    - Daily token/cost caps
    - Automatic approval thresholds
    - Budget tracking and alerts
    - Context pruning suggestions
    """

    def __init__(self):
        self.daily_budget = settings.max_autonomous_cost
        self.approval_threshold = getattr(settings, "cost_approval_threshold", 0.50)
        self.warning_threshold = getattr(
            settings, "cost_warning_threshold", 0.75
        )  # Warn at 75% of budget by default

        # Track spending
        self.session_cost = 0.0
        self.daily_cost = 0.0
        self.last_reset_date = date.today()

        # Tokenizer cache
        self.tokenizers = {}

        # Approval callback (can be set by GUI)
        self.approval_callback: Optional[Callable[[CostEstimate], bool]] = None

    def _get_tokenizer(self, model: str):
        """Get or create tokenizer for model"""
        if not TIKTOKEN_AVAILABLE:
            return None

        if model not in self.tokenizers:
            try:
                # Try to get exact encoding for model
                if "gpt" in model.lower():
                    encoding_name = "cl100k_base"  # GPT-4, GPT-3.5
                elif "claude" in model.lower():
                    encoding_name = "cl100k_base"  # Similar to GPT
                else:
                    encoding_name = "cl100k_base"  # Default

                self.tokenizers[model] = tiktoken.get_encoding(encoding_name)
            except Exception as e:
                logger.warning(f"Failed to get tokenizer for {model}: {e}")
                return None

        return self.tokenizers[model]

    def count_tokens(self, text: str, model: str = "gpt-4") -> int:
        """
        Count tokens in text

        Args:
            text: Text to count
            model: Model name for tokenizer selection

        Returns:
            Token count
        """
        if not text:
            return 0

        tokenizer = self._get_tokenizer(model)

        if tokenizer:
            try:
                return len(tokenizer.encode(text))
            except Exception as e:
                logger.warning(f"Token counting failed: {e}")

        # Fallback: rough approximation (1 token ≈ 4 characters)
        return len(text) // 4

    def estimate_cost(
        self, messages: list, model: str, max_output_tokens: int = 4096
    ) -> CostEstimate:
        """
        Estimate cost of an LLM operation

        Args:
            messages: Message list
            model: Model identifier
            max_output_tokens: Maximum expected output tokens

        Returns:
            CostEstimate with details
        """
        # Count input tokens
        input_text = " ".join(
            [
                msg.get("content", "")
                if isinstance(msg.get("content"), str)
                else str(msg.get("content", ""))
                for msg in messages
            ]
        )
        input_tokens = self.count_tokens(input_text, model)

        # Estimate output tokens (use max or 50% of max as default)
        output_tokens = max_output_tokens // 2

        total_tokens = input_tokens + output_tokens

        # Get pricing for model
        cost = self._calculate_model_cost(model, input_tokens, output_tokens)

        # Determine cost level
        if cost < 0.10:
            level = CostLevel.LOW
        elif cost < 0.50:
            level = CostLevel.MEDIUM
        elif cost < 2.00:
            level = CostLevel.HIGH
        else:
            level = CostLevel.VERY_HIGH

        # Check if requires approval
        requires_approval = cost >= self.approval_threshold

        return CostEstimate(
            input_tokens=input_tokens,
            output_tokens_estimated=output_tokens,
            total_tokens=total_tokens,
            estimated_cost=cost,
            cost_level=level,
            model=model,
            requires_approval=requires_approval,
        )

    def _calculate_model_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on model pricing"""
        # Pricing per 1M tokens (input, output)
        pricing = {
            # Anthropic Claude
            "claude-opus-4-5": (15.0, 75.0),
            "claude-sonnet-4-5": (3.0, 15.0),
            "claude-3.5-sonnet": (3.0, 15.0),
            "claude-haiku": (0.25, 1.25),
            "claude-3-haiku": (0.25, 1.25),
            # OpenAI GPT
            "gpt-4": (30.0, 60.0),
            "gpt-4-turbo": (10.0, 30.0),
            "gpt-3.5-turbo": (0.5, 1.5),
            # Google Gemini (via OpenRouter)
            "google/gemini-flash-1.5-8b": (0.04, 0.15),
            "google/gemini-pro-1.5": (1.25, 5.0),
            # Ollama (local - free)
            "qwen2.5:7b": (0.0, 0.0),
            "deepseek-coder:6.7b": (0.0, 0.0),
        }

        # Find matching pricing
        for key, (input_price, output_price) in pricing.items():
            if key in model.lower():
                cost = (input_tokens / 1_000_000 * input_price) + (
                    output_tokens / 1_000_000 * output_price
                )
                return cost

        # Default to moderate pricing if unknown
        return (input_tokens / 1_000_000 * 3.0) + (output_tokens / 1_000_000 * 15.0)

    async def check_budget_and_approve(self, estimate: CostEstimate) -> bool:
        """
        Check budget and get approval if needed

        Args:
            estimate: Cost estimate for operation

        Returns:
            True if approved, False if denied
        """
        # Reset daily counter if new day
        self._reset_daily_if_needed()

        # Check if over budget
        if self.daily_cost + estimate.estimated_cost > self.daily_budget:
            logger.warning(
                f"Operation would exceed daily budget: "
                f"${self.daily_cost:.4f} + "
                f"${estimate.estimated_cost:.4f} "
                f"> ${self.daily_budget:.2f}"
            )
            return False

        # Check if requires approval
        if estimate.requires_approval:
            logger.info(
                f"Operation requires approval "
                f"(${estimate.estimated_cost:.4f} "
                f">= ${self.approval_threshold:.2f})"
            )

            # Call approval callback if set
            if self.approval_callback:
                approved = await asyncio.get_event_loop().run_in_executor(
                    None, self.approval_callback, estimate
                )
                if not approved:
                    logger.info("Operation denied by user")
                    return False
            else:
                # Deny in headless/unconfigured mode to enforce explicit approval
                logger.warning(
                    f"Denying ${estimate.estimated_cost:.4f}"
                    " operation because it requires"
                    " approval "
                    f"and no approval callback is set"
                )
                return False

        return True

    def record_cost(self, actual_cost: float):
        """Record actual cost after operation"""
        self._reset_daily_if_needed()

        self.session_cost += actual_cost
        self.daily_cost += actual_cost

        logger.info(
            f"Cost recorded: ${actual_cost:.4f} | "
            f"Session: ${self.session_cost:.4f} | "
            f"Daily: ${self.daily_cost:.4f}/{self.daily_budget:.2f}"
        )

        # Check warning threshold
        if self.daily_cost >= self.daily_budget * self.warning_threshold:
            remaining = self.daily_budget - self.daily_cost
            logger.warning(
                f"Budget warning: ${remaining:.2f} remaining "
                f"({(remaining / self.daily_budget * 100):.1f}%)"
            )

    def get_budget_status(self) -> BudgetStatus:
        """Get current budget status"""
        self._reset_daily_if_needed()

        remaining = self.daily_budget - self.daily_cost

        return BudgetStatus(
            daily_limit=self.daily_budget,
            daily_spent=self.daily_cost,
            daily_remaining=remaining,
            session_spent=self.session_cost,
            last_reset=self.last_reset_date,
            is_over_budget=self.daily_cost >= self.daily_budget,
            warning_threshold_reached=self.daily_cost >= self.daily_budget * self.warning_threshold,
        )

    def _reset_daily_if_needed(self):
        """Reset daily counter if it's a new day"""
        today = date.today()
        if today > self.last_reset_date:
            logger.info(f"Daily budget reset: ${self.daily_cost:.4f} -> $0.00")
            self.daily_cost = 0.0
            self.last_reset_date = today

    def suggest_context_pruning(
        self, messages: list, target_reduction: float = 0.5
    ) -> dict[str, Any]:
        """
        Suggest how to prune context to reduce costs

        Args:
            messages: Current message list
            target_reduction: Target reduction ratio (0.0-1.0)

        Returns:
            Suggestions for context pruning
        """
        total_tokens = sum(self.count_tokens(str(msg.get("content", ""))) for msg in messages)

        # Calculate target tokens
        target_tokens = int(total_tokens * (1 - target_reduction))

        suggestions = {
            "current_tokens": total_tokens,
            "target_tokens": target_tokens,
            "reduction_needed": total_tokens - target_tokens,
            "strategies": [],
        }

        # Suggest strategies
        if len(messages) > 10:
            suggestions["strategies"].append(
                {
                    "strategy": "Keep only recent messages",
                    "description": f"Keep last {min(10, len(messages) // 2)} messages",
                    "estimated_savings": total_tokens * 0.3,
                }
            )

        suggestions["strategies"].append(
            {
                "strategy": "Summarize old messages",
                "description": "Summarize messages older than 5 turns",
                "estimated_savings": total_tokens * target_reduction,
            }
        )

        suggestions["strategies"].append(
            {
                "strategy": "Remove system messages",
                "description": "Keep only user/assistant messages",
                "estimated_savings": total_tokens * 0.1,
            }
        )

        return suggestions

    def reset_session(self):
        """Reset session cost counter"""
        logger.info(f"Session cost reset: ${self.session_cost:.4f} -> $0.00")
        self.session_cost = 0.0


class CostGuards:
    """Test-compatible wrapper providing a simplified budget-guard API.

    Accepts ``daily_budget_usd`` and ``session_budget_usd`` constructor
    parameters and exposes lightweight ``can_proceed`` / ``record_spend``
    helpers that the unit-test suite expects.
    """

    def __init__(
        self,
        daily_budget_usd: float = 5.0,
        session_budget_usd: float = 2.0,
        warn_threshold: float = 0.75,
    ):
        self.daily_budget_usd = daily_budget_usd
        self.session_budget_usd = session_budget_usd
        self.warn_threshold = warn_threshold

        self._daily_spend: float = 0.0
        self._session_spend: float = 0.0

        self.on_warning: Optional[Callable[[str], None]] = None

    # ------------------------------------------------------------------
    # Core gate
    # ------------------------------------------------------------------

    def can_proceed(self, estimated_cost: float = 0.0) -> bool:
        if estimated_cost == 0.0:
            return True
        if self._daily_spend + estimated_cost > self.daily_budget_usd:
            return False
        if self._session_spend + estimated_cost > self.session_budget_usd:
            return False
        return True

    def record_spend(self, amount: float) -> None:
        if amount < 0:
            raise ValueError("Spend amount must be non-negative")
        self._daily_spend += amount
        self._session_spend += amount

    def get_session_spend(self) -> float:
        return self._session_spend

    def reset_session(self) -> None:
        self._session_spend = 0.0

    def get_remaining_session_budget(self) -> float:
        return max(0.0, self.session_budget_usd - self._session_spend)

    # ------------------------------------------------------------------
    # Warnings
    # ------------------------------------------------------------------

    def check_warnings(self) -> None:
        ratio = self._session_spend / self.session_budget_usd if self.session_budget_usd else 0.0
        if ratio >= self.warn_threshold and self.on_warning:
            self.on_warning(
                f"Session spend {self._session_spend:.4f} reached "
                f"{ratio:.0%} of budget {self.session_budget_usd:.2f}"
            )

    # ------------------------------------------------------------------
    # Cost estimation (simplified)
    # ------------------------------------------------------------------

    _PRICING: dict[str, tuple[float, float]] = {
        "claude-haiku": (0.25, 1.25),
        "claude-3-haiku": (0.25, 1.25),
        "claude-sonnet": (3.0, 15.0),
        "claude-opus": (15.0, 75.0),
        "gpt-4": (30.0, 60.0),
        "gpt-4-turbo": (10.0, 30.0),
        "gpt-3.5-turbo": (0.5, 1.5),
    }

    def estimate_cost(
        self,
        model: str = "gpt-4",
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> float:
        for key, (inp, out) in self._PRICING.items():
            if key in model.lower():
                return (input_tokens / 1_000_000 * inp) + (output_tokens / 1_000_000 * out)
        return (input_tokens / 1_000_000 * 3.0) + (output_tokens / 1_000_000 * 15.0)


# Global cost guard instance
cost_guard = CostGuard()
