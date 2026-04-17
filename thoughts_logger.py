"""
Thoughts Logger Module
Reasoning trace logging for transparent AI decision-making
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from config import settings

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.syntax import Syntax  # noqa: F401

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    logger.warning("rich not available - thought logs will use plain text")


class ThoughtType(str, Enum):
    """Types of thoughts to log"""

    REASONING = "reasoning"
    DECISION = "decision"
    OBSERVATION = "observation"
    PLANNING = "planning"
    REFLECTION = "reflection"
    COST_ANALYSIS = "cost_analysis"
    MODEL_SELECTION = "model_selection"


@dataclass
class Thought:
    """A single thought/reasoning step"""

    timestamp: str
    type: ThoughtType
    content: str
    context: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)


class ThoughtsLogger:
    """
    Thoughts logger for transparent AI reasoning

    Features:
    - Structured thought logging
    - Beautiful terminal output with Rich
    - Exportable thought traces
    - Toggleable detail levels
    - Integration with router and LLM gateway
    """

    def __init__(self):
        self.enabled = getattr(settings, "enable_thought_logging", True)
        self.log_file = self._get_log_file_path()
        self.thoughts: list[Thought] = []
        self.console = Console() if RICH_AVAILABLE else None

        # Detail level: 0 = off, 1 = minimal, 2 = normal, 3 = verbose
        self.detail_level = getattr(settings, "thought_log_detail_level", 2)

    def _get_log_file_path(self) -> Path:
        """Get path to THOUGHTS.log file"""
        log_dir = settings.data_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create daily log file
        date_str = datetime.now().strftime("%Y-%m-%d")
        return log_dir / f"THOUGHTS_{date_str}.log"

    def log_thought(
        self,
        thought_type: ThoughtType,
        content: str,
        context: Optional[dict] = None,
        metadata: Optional[dict] = None,
        display: bool = True,
    ):
        """
        Log a thought/reasoning step

        Args:
            thought_type: Type of thought
            content: Thought content
            context: Additional context
            metadata: Metadata (costs, timing, etc.)
            display: Whether to display in terminal
        """
        if not self.enabled or self.detail_level == 0:
            return

        thought = Thought(
            timestamp=datetime.now().isoformat(),
            type=thought_type,
            content=content,
            context=context,
            metadata=metadata,
        )

        # Add to memory
        self.thoughts.append(thought)

        # Write to log file
        self._write_to_file(thought)

        # Display in terminal if requested
        if display and self.detail_level >= 2:
            self._display_thought(thought)

    def _write_to_file(self, thought: Thought):
        """Write thought to log file"""
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(thought.to_dict(), default=str) + "\n")
        except Exception as e:
            logger.error(f"Failed to write thought to log: {e}")

    def _display_thought(self, thought: Thought):
        """Display thought in terminal with Rich formatting"""
        if not RICH_AVAILABLE:
            # Fallback to plain text
            print(f"\n[{thought.type.value.upper()}] {thought.content}")
            if thought.metadata:
                print(f"  Metadata: {thought.metadata}")
            return

        # Rich formatting
        color_map = {
            ThoughtType.REASONING: "blue",
            ThoughtType.DECISION: "green",
            ThoughtType.OBSERVATION: "cyan",
            ThoughtType.PLANNING: "magenta",
            ThoughtType.REFLECTION: "yellow",
            ThoughtType.COST_ANALYSIS: "red",
            ThoughtType.MODEL_SELECTION: "green",
        }

        color = color_map.get(thought.type, "white")

        # Build content
        content_lines = [thought.content]

        if thought.context and self.detail_level >= 3:
            content_lines.append("\n[dim]Context:[/dim]")
            content_lines.append(f"[dim]{json.dumps(thought.context, indent=2, default=str)}[/dim]")

        if thought.metadata:
            content_lines.append("\n[dim]Metadata:[/dim]")
            for key, value in thought.metadata.items():
                content_lines.append(f"[dim]  {key}: {value}[/dim]")

        panel = Panel(
            "\n".join(content_lines),
            title=f"[bold {color}]{thought.type.value.upper()}[/bold {color}]",
            border_style=color,
            expand=False,
        )

        self.console.print(panel)

    def log_reasoning(self, reasoning: str, context: Optional[dict] = None):
        """Log a reasoning step"""
        self.log_thought(ThoughtType.REASONING, reasoning, context=context)

    def log_decision(
        self, decision: str, rationale: Optional[str] = None, metadata: Optional[dict] = None
    ):
        """Log a decision with rationale"""
        content = decision
        if rationale:
            content += f"\n\nRationale: {rationale}"

        self.log_thought(ThoughtType.DECISION, content, metadata=metadata)

    def log_model_selection(
        self,
        model: str,
        reason: str,
        alternatives: Optional[list[str]] = None,
        cost_estimate: Optional[float] = None,
    ):
        """Log model selection decision"""
        content = f"Selected: {model}\n\nReason: {reason}"

        if alternatives:
            content += f"\n\nAlternatives considered: {', '.join(alternatives)}"

        metadata = {}
        if cost_estimate is not None:
            metadata["estimated_cost"] = f"${cost_estimate:.4f}"

        self.log_thought(ThoughtType.MODEL_SELECTION, content, metadata=metadata)

    def log_cost_analysis(
        self, operation: str, estimated_cost: float, budget_impact: Optional[str] = None
    ):
        """Log cost analysis"""
        content = f"Operation: {operation}\nEstimated Cost: ${estimated_cost:.4f}"

        if budget_impact:
            content += f"\n\nBudget Impact: {budget_impact}"

        self.log_thought(ThoughtType.COST_ANALYSIS, content)

    def log_planning(self, plan: str, steps: Optional[list[str]] = None):
        """Log planning thoughts"""
        content = plan

        if steps:
            content += "\n\nSteps:\n" + "\n".join(
                [f"{i + 1}. {step}" for i, step in enumerate(steps)]
            )

        self.log_thought(ThoughtType.PLANNING, content)

    def log_reflection(self, reflection: str, lessons: Optional[list[str]] = None):
        """Log self-reflection"""
        content = reflection

        if lessons:
            content += "\n\nLessons learned:\n" + "\n".join([f"• {lesson}" for lesson in lessons])

        self.log_thought(ThoughtType.REFLECTION, content)

    def export_trace(self, output_path: Optional[str] = None) -> str:
        """
        Export thought trace to file

        Args:
            output_path: Optional output path (auto-generated if None)

        Returns:
            Path to exported file
        """
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(settings.data_dir / "logs" / f"thought_trace_{timestamp}.json")

        try:
            with open(output_path, "w") as f:
                json.dump([thought.to_dict() for thought in self.thoughts], f, indent=2)

            logger.info(f"Thought trace exported to: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to export thought trace: {e}")
            raise

    def get_recent_thoughts(
        self, n: int = 10, thought_type: Optional[ThoughtType] = None
    ) -> list[Thought]:
        """Get recent thoughts, optionally filtered by type"""
        thoughts = self.thoughts

        if thought_type:
            thoughts = [t for t in thoughts if t.type == thought_type]

        return thoughts[-n:]

    def clear(self):
        """Clear current thoughts from memory (file logs preserved)"""
        self.thoughts = []

    def set_detail_level(self, level: int):
        """
        Set detail level for thought logging

        Args:
            level: 0 = off, 1 = minimal, 2 = normal, 3 = verbose
        """
        if 0 <= level <= 3:
            self.detail_level = level
            logger.info(f"Thought logging detail level set to: {level}")
        else:
            logger.warning(f"Invalid detail level: {level}. Must be 0-3")

    def toggle(self, enabled: Optional[bool] = None):
        """Toggle thought logging on/off"""
        if enabled is None:
            self.enabled = not self.enabled
        else:
            self.enabled = enabled

        status = "enabled" if self.enabled else "disabled"
        logger.info(f"Thought logging {status}")

    def summary(self) -> dict[str, Any]:
        """Get summary of logged thoughts"""
        type_counts = {}
        for thought in self.thoughts:
            type_counts[thought.type.value] = type_counts.get(thought.type.value, 0) + 1

        return {
            "total_thoughts": len(self.thoughts),
            "by_type": type_counts,
            "log_file": str(self.log_file),
            "enabled": self.enabled,
            "detail_level": self.detail_level,
        }


# Global thoughts logger instance
thoughts_logger = ThoughtsLogger()
