"""
Autonomous Loop & Evaluator-Optimizer - Tier 6 Self-Improvement
Autonomous coding loop + self-critique refinement cycle
"""
import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from loguru import logger


# ──────────────────────────────────────────────────────────────────────────────
# Draymond session helpers
# ──────────────────────────────────────────────────────────────────────────────

async def start_session(agent_id: str, trigger: str = "heartbeat") -> str:
    """Open a Draymond session row and return its UUID."""
    from supabase_client import get_supabase
    db = get_supabase()
    res = db.table("draymond_sessions").insert({
        "agent_id": agent_id,
        "trigger_source": trigger,
        "is_active": True,
    }).execute()
    return res.data[0]["id"]


async def close_session(session_id: str, stats: dict):
    """Close a Draymond session and write summary statistics."""
    from supabase_client import get_supabase
    db = get_supabase()
    db.table("draymond_sessions").update({
        "is_active": False,
        "ended_at": "now()",
        "total_actions": stats.get("total", 0),
        "successful_actions": stats.get("success", 0),
        "failed_actions": stats.get("failed", 0),
        "avg_confidence": stats.get("avg_confidence"),
    }).eq("id", session_id).execute()


class LoopStatus(str, Enum):
    """Status of an autonomous loop"""
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    MAX_ITERATIONS = "max_iterations_reached"


@dataclass
class LoopIteration:
    """A single iteration of the autonomous loop"""
    iteration: int
    action: str
    result: str
    tests_passed: Optional[bool] = None
    errors: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    cost: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AutonomousResult:
    """Result of an autonomous loop execution"""
    loop_id: str
    goal: str
    status: LoopStatus
    iterations: List[LoopIteration] = field(default_factory=list)
    final_output: Optional[str] = None
    total_cost: float = 0.0
    total_time_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalResult:
    """Result of an evaluation cycle"""
    original_output: str
    critique: str
    refined_output: str
    improvement_score: float  # 0.0-1.0 how much better the refined version is
    iteration: int
    cost: float = 0.0


class AutonomousCodingLoop:
    """
    Iterates on code generation until a defined goal is fully met.

    Inspired by Anthropic's "Ralph" pattern:
    1. Generate code to meet the goal
    2. Run tests/validation
    3. If tests fail, analyze errors
    4. Debug and fix
    5. Repeat until goal is met or max iterations reached

    Works for any iterative refinement task, not just coding.
    """

    MAX_OUTPUT_DISPLAY_LENGTH = 3000

    def __init__(self, max_iterations: int = 10):
        self.max_iterations = max_iterations
        self.active_loops: Dict[str, AutonomousResult] = {}
        self._router = None
        self._shell = None

    def _get_router(self):
        if self._router is None:
            from router import router
            self._router = router
        return self._router

    async def run(
        self,
        goal: str,
        context: Optional[Dict] = None,
        validation_fn: Optional[Callable] = None,
        max_iterations: Optional[int] = None
    ) -> AutonomousResult:
        """
        Run the autonomous coding/refinement loop.

        Args:
            goal: What the loop should achieve
            context: Additional context (existing code, requirements, etc.)
            validation_fn: Optional async function that returns (passed: bool, feedback: str)
            max_iterations: Override max iterations

        Returns:
            AutonomousResult with final output and iteration history
        """
        import time
        start_time = time.time()
        max_iter = max_iterations or self.max_iterations

        result = AutonomousResult(
            loop_id=str(uuid.uuid4()),
            goal=goal,
            status=LoopStatus.RUNNING
        )

        self.active_loops[result.loop_id] = result
        current_output = ""
        error_history = []

        logger.info(f"Starting autonomous loop: {goal[:100]}...")

        for iteration in range(1, max_iter + 1):
            logger.info(f"Autonomous loop iteration {iteration}/{max_iter}")

            iter_result = LoopIteration(iteration=iteration, action="", result="")

            try:
                # Step 1: Generate or refine
                if iteration == 1:
                    # Initial generation
                    gen_prompt = f"""You are in an autonomous coding loop. Generate a solution for this goal.

Goal: {goal}

{f"Context: {json.dumps(context)}" if context else ""}

Provide complete, working code/solution. Be thorough and handle edge cases."""

                else:
                    # Refinement based on errors
                    gen_prompt = f"""You are in an autonomous coding loop (iteration {iteration}).

Goal: {goal}

Current solution:
```
{current_output[:self.MAX_OUTPUT_DISPLAY_LENGTH]}
```

Errors from previous iteration:
{json.dumps(error_history[-3:], indent=2)}

Fix the errors and improve the solution. Provide the complete updated solution."""

                decision, gen_result = await self._get_router().execute_with_routing(
                    task=gen_prompt,
                    context={"requires_reasoning": True}
                )

                current_output = gen_result.get("content", "")
                iter_result.action = "generate" if iteration == 1 else "refine"
                iter_result.result = current_output[:1000]
                iter_result.cost = decision.estimated_cost

                # Step 2: Validate
                if validation_fn:
                    passed, feedback = await validation_fn(current_output)
                    iter_result.tests_passed = passed

                    if passed:
                        result.status = LoopStatus.COMPLETED
                        result.final_output = current_output
                        result.iterations.append(iter_result)
                        break
                    else:
                        iter_result.errors.append(feedback)
                        error_history.append({
                            "iteration": iteration,
                            "error": feedback
                        })
                else:
                    # Self-validate: ask the model to critique its own output
                    critique_prompt = f"""Critically evaluate this solution for the goal: {goal}

Solution:
```
{current_output[:self.MAX_OUTPUT_DISPLAY_LENGTH]}
```

Are there any bugs, errors, or improvements needed?
Respond in JSON:
{{
    "has_issues": true/false,
    "issues": ["issue 1", "issue 2"],
    "quality_score": 0.85,
    "suggestions": ["suggestion 1"]
}}"""

                    _, critique_result = await self._get_router().execute_with_routing(
                        task=critique_prompt,
                        context={"requires_reasoning": True}
                    )

                    critique_content = critique_result.get("content", "")
                    critique = self._parse_json(critique_content)

                    if critique:
                        has_issues = critique.get("has_issues", True)
                        quality = critique.get("quality_score", 0.5)
                        issues = critique.get("issues", [])

                        iter_result.tests_passed = not has_issues or quality >= 0.9

                        if not has_issues or quality >= 0.9:
                            result.status = LoopStatus.COMPLETED
                            result.final_output = current_output
                            result.iterations.append(iter_result)
                            break
                        else:
                            iter_result.errors = issues
                            error_history.extend([
                                {"iteration": iteration, "error": issue}
                                for issue in issues
                            ])
                    else:
                        # Can't parse critique, assume done after a few iterations
                        if iteration >= 3:
                            result.status = LoopStatus.COMPLETED
                            result.final_output = current_output
                            result.iterations.append(iter_result)
                            break

            except Exception as e:
                logger.error(f"Loop iteration {iteration} failed: {e}")
                iter_result.errors.append(str(e))
                error_history.append({"iteration": iteration, "error": str(e)})

            result.iterations.append(iter_result)

        # If we exhausted iterations
        if result.status == LoopStatus.RUNNING:
            result.status = LoopStatus.MAX_ITERATIONS
            result.final_output = current_output

        result.total_cost = sum(i.cost for i in result.iterations)
        result.total_time_seconds = time.time() - start_time

        logger.info(
            f"Autonomous loop {result.status.value}: "
            f"{len(result.iterations)} iterations, "
            f"${result.total_cost:.4f}, {result.total_time_seconds:.1f}s"
        )

        return result

    def _parse_json(self, content: str) -> Optional[Dict]:
        """Parse JSON from response content"""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            try:
                start = content.find("{")
                end = content.rfind("}") + 1
                if start >= 0 and end > start:
                    return json.loads(content[start:end])
            except json.JSONDecodeError:
                return None


class EvaluatorOptimizer:
    """
    Generates output, critiques it as a second agent, then refines
    based on its own critique — a built-in quality assurance loop.

    Pattern:
    1. Generator produces initial output
    2. Evaluator critiques the output
    3. Optimizer refines based on critique
    4. Repeat until quality threshold met
    """

    def __init__(self, quality_threshold: float = 0.85, max_cycles: int = 3):
        self.quality_threshold = quality_threshold
        self.max_cycles = max_cycles
        self._router = None

    def _get_router(self):
        if self._router is None:
            from router import router
            self._router = router
        return self._router

    async def generate_and_refine(
        self,
        task: str,
        context: Optional[Dict] = None,
        criteria: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate, evaluate, and refine output through multiple cycles.

        Args:
            task: The task to accomplish
            context: Additional context
            criteria: Evaluation criteria (auto-generated if None)

        Returns:
            Dict with final output, evaluations, and improvement history
        """
        eval_criteria = criteria or [
            "Accuracy and correctness",
            "Completeness",
            "Clarity and readability",
            "Efficiency",
            "Error handling"
        ]

        history = []
        current_output = ""

        for cycle in range(self.max_cycles):
            # Step 1: GENERATE (or OPTIMIZE in subsequent cycles)
            if cycle == 0:
                gen_prompt = f"""Generate a high-quality response for this task:

Task: {task}
{f"Context: {json.dumps(context)}" if context else ""}

Be thorough, accurate, and complete."""

            else:
                gen_prompt = f"""Refine this output based on the critique below.

Original task: {task}

Current output:
{current_output[:4000]}

Critique:
{history[-1]["critique"] if history else "No critique yet"}

Improve the output to address ALL critique points while maintaining quality."""

            decision, gen_result = await self._get_router().execute_with_routing(
                task=gen_prompt,
                context={"requires_reasoning": True}
            )

            current_output = gen_result.get("content", "")

            # Step 2: EVALUATE
            eval_prompt = f"""You are a critical evaluator. Assess this output objectively.

Task: {task}

Output to evaluate:
{current_output[:4000]}

Evaluation criteria:
{json.dumps(eval_criteria, indent=2)}

Rate each criterion from 0.0 to 1.0 and provide specific feedback.

Respond in JSON:
{{
    "scores": {{
        "{eval_criteria[0]}": 0.85,
        ...
    }},
    "overall_score": 0.82,
    "strengths": ["strength 1", "strength 2"],
    "weaknesses": ["weakness 1", "weakness 2"],
    "specific_improvements": ["improvement 1", "improvement 2"]
}}"""

            _, eval_result = await self._get_router().execute_with_routing(
                task=eval_prompt,
                context={"requires_reasoning": True}
            )

            eval_content = eval_result.get("content", "")
            evaluation = self._parse_json(eval_content)

            overall_score = 0.0
            critique = ""

            if evaluation:
                overall_score = evaluation.get("overall_score", 0.5)
                weaknesses = evaluation.get("weaknesses", [])
                improvements = evaluation.get("specific_improvements", [])
                critique = (
                    f"Score: {overall_score:.2f}\n"
                    f"Weaknesses: {', '.join(weaknesses)}\n"
                    f"Improvements needed: {', '.join(improvements)}"
                )
            else:
                critique = eval_content
                overall_score = 0.5

            history.append(EvalResult(
                original_output=current_output[:1000],
                critique=critique,
                refined_output="",  # Will be set in next cycle
                improvement_score=overall_score,
                iteration=cycle + 1,
                cost=decision.estimated_cost
            ))

            # Check if quality threshold met
            if overall_score >= self.quality_threshold:
                logger.info(
                    f"Quality threshold met at cycle {cycle + 1}: "
                    f"{overall_score:.2f} >= {self.quality_threshold}"
                )
                break

        return {
            "final_output": current_output,
            "final_score": overall_score,
            "cycles": len(history),
            "history": [
                {
                    "iteration": h.iteration,
                    "score": h.improvement_score,
                    "critique": h.critique[:500],
                    "cost": h.cost
                }
                for h in history
            ],
            "total_cost": sum(h.cost for h in history),
            "threshold_met": overall_score >= self.quality_threshold
        }

    def _parse_json(self, content: str) -> Optional[Dict]:
        """Parse JSON from response"""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            try:
                start = content.find("{")
                end = content.rfind("}") + 1
                if start >= 0 and end > start:
                    return json.loads(content[start:end])
            except json.JSONDecodeError:
                return None


# Global instances
autonomous_loop = AutonomousCodingLoop()
evaluator_optimizer = EvaluatorOptimizer()
