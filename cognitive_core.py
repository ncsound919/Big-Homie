"""
Cognitive Core - Tier 1 Agent Reasoning Engine
Chain-of-Thought, ReAct Loop, Tree-of-Thought, Self-Consistency Verification
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from loguru import logger


class ReasoningStrategy(str, Enum):
    """Available reasoning strategies"""

    CHAIN_OF_THOUGHT = "cot"
    REACT = "react"
    TREE_OF_THOUGHT = "tot"
    SELF_CONSISTENCY = "cot_sc"


@dataclass
class ReasoningStep:
    """A single step in a reasoning chain"""

    step_id: str
    step_number: int
    thought: str
    action: Optional[str] = None
    observation: Optional[str] = None
    confidence: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ReasoningTrace:
    """Complete trace of a reasoning process"""

    trace_id: str
    strategy: ReasoningStrategy
    query: str
    steps: list[ReasoningStep] = field(default_factory=list)
    final_answer: Optional[str] = None
    total_confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ThoughtBranch:
    """A branch in Tree-of-Thought reasoning"""

    branch_id: str
    parent_id: Optional[str]
    thought: str
    score: float = 0.0
    children: list[str] = field(default_factory=list)
    is_terminal: bool = False
    is_pruned: bool = False


REFLECTION_CONFIDENCE_THRESHOLD = 0.6
MAX_REFLECTION_ROUNDS = 2


class CognitiveCore:
    """
    The reasoning engine at the heart of Big Homie.

    Implements four reasoning strategies:
    1. Chain-of-Thought (CoT) - Explicit step-by-step decomposition
    2. ReAct Loop - Think → Act → Observe iterative cycle
    3. Tree-of-Thought (ToT) - Multi-branch exploration with backtracking
    4. Self-Consistency (CoT-SC) - Multi-path consensus voting

    Enhanced with:
    - Self-reflection / skeptic loop for answer validation
    - Karpathy-method integration (temperature calibration, PRM, debate)
    """

    MAX_OBSERVATION_LENGTH = 2000
    MAX_OUTPUT_PREVIEW = 3000

    def __init__(self):
        self.traces: dict[str, ReasoningTrace] = {}
        self._llm = None
        self._router = None
        self._thoughts_logger = None
        self._karpathy = None

    def _get_llm(self):
        """Lazy-load LLM gateway to avoid circular imports"""
        if self._llm is None:
            from llm_gateway import LLMGateway

            self._llm = LLMGateway()
        return self._llm

    def _get_router(self):
        """Lazy-load router"""
        if self._router is None:
            from router import router

            self._router = router
        return self._router

    def _get_thoughts_logger(self):
        """Lazy-load thoughts logger"""
        if self._thoughts_logger is None:
            from config import settings

            if settings.enable_thought_logging:
                from thoughts_logger import thoughts_logger

                self._thoughts_logger = thoughts_logger
        return self._thoughts_logger

    def _get_karpathy_engine(self):
        """Lazy-load KarpathyEngine to avoid circular imports"""
        if self._karpathy is None:
            from karpathy_methods import KarpathyEngine

            self._karpathy = KarpathyEngine()
        return self._karpathy

    # ===== Chain-of-Thought Reasoning =====

    async def chain_of_thought(
        self, query: str, context: Optional[dict] = None, max_steps: int = 10
    ) -> ReasoningTrace:
        """
        Decompose a problem into explicit intermediate steps before producing an answer.

        Forces the agent to think step-by-step, dramatically reducing errors
        on complex tasks like math, logic, and multi-step reasoning.

        Args:
            query: The problem to reason about
            context: Additional context
            max_steps: Maximum reasoning steps

        Returns:
            ReasoningTrace with all steps and final answer
        """
        trace = ReasoningTrace(
            trace_id=str(uuid.uuid4()), strategy=ReasoningStrategy.CHAIN_OF_THOUGHT, query=query
        )

        cot_prompt = f"""You are solving a problem step-by-step using Chain-of-Thought reasoning.

Problem: {query}

{f"Context: {json.dumps(context)}" if context else ""}

Instructions:
1. Break this problem into clear, numbered steps
2. Show your reasoning at each step
3. State any assumptions explicitly
4. After all steps, provide a final answer with a confidence score (0.0-1.0)

Respond in JSON format:
{{
    "steps": [
        {{"step": 1, "thought": "First, I need to...", "confidence": 0.9}},
        {{"step": 2, "thought": "Next, considering...", "confidence": 0.85}}
    ],
    "final_answer": "The answer is...",
    "overall_confidence": 0.87
}}"""

        decision, result = await self._get_router().execute_with_routing(
            task=cot_prompt, context={"requires_reasoning": True}
        )

        content = result.get("content", "")
        parsed = self._parse_json_response(content)

        if parsed:
            for step_data in parsed.get("steps", [])[:max_steps]:
                step = ReasoningStep(
                    step_id=str(uuid.uuid4()),
                    step_number=step_data.get("step", 0),
                    thought=step_data.get("thought", ""),
                    confidence=step_data.get("confidence", 0.5),
                )
                trace.steps.append(step)

            trace.final_answer = parsed.get("final_answer", content)
            trace.total_confidence = parsed.get("overall_confidence", 0.5)
        else:
            # Fallback: treat entire response as a single reasoning step
            trace.steps.append(
                ReasoningStep(
                    step_id=str(uuid.uuid4()), step_number=1, thought=content, confidence=0.5
                )
            )
            trace.final_answer = content
            trace.total_confidence = 0.5

        trace.metadata["model"] = decision.model
        trace.metadata["cost"] = decision.estimated_cost

        self.traces[trace.trace_id] = trace
        self._log_trace(trace)

        return trace

    # ===== ReAct Loop =====

    async def react_loop(
        self,
        query: str,
        available_tools: Optional[list[dict]] = None,
        context: Optional[dict] = None,
        max_iterations: int = 8,
    ) -> ReasoningTrace:
        """
        Think → Act → Observe iterative cycle.

        Grounds the agent in real-world feedback, preventing hallucinations
        and producing auditable reasoning traces.

        Args:
            query: The task to accomplish
            available_tools: List of tool descriptions the agent can use
            context: Additional context
            max_iterations: Maximum Think-Act-Observe cycles

        Returns:
            ReasoningTrace with interleaved thought/action/observation steps
        """
        trace = ReasoningTrace(
            trace_id=str(uuid.uuid4()), strategy=ReasoningStrategy.REACT, query=query
        )

        tool_descriptions = ""
        if available_tools:
            tool_descriptions = "Available tools:\n" + "\n".join(
                f"- {t['name']}: {t['description']}" for t in available_tools
            )

        conversation = [
            {
                "role": "system",
                "content": f"""You are an agent using the ReAct (Reasoning + Acting) framework.
For each step, you must:
1. THOUGHT: Reason about what to do next
2. ACTION: Choose an action to take (or "finish" if done)
3. Wait for OBSERVATION from the environment

{tool_descriptions}

Always respond in this exact JSON format:
{{
    "thought": "I need to...",
    "action": "tool_name",
    "action_input": {{"param": "value"}},
    "is_final": false
}}

When you have the final answer, respond with:
{{
    "thought": "Based on my observations...",
    "action": "finish",
    "action_input": {{"answer": "The final answer"}},
    "is_final": true
}}""",
            },
            {
                "role": "user",
                "content": f"Task: {query}\n{f'Context: {json.dumps(context)}' if context else ''}",
            },
        ]

        for iteration in range(max_iterations):
            # THINK + ACT
            from llm_gateway import TaskType

            result = await self._get_llm().complete(conversation, task_type=TaskType.REASONING)

            content = result.get("content", "")
            parsed = self._parse_json_response(content)

            if not parsed:
                # If can't parse, create a thought step and break
                trace.steps.append(
                    ReasoningStep(
                        step_id=str(uuid.uuid4()),
                        step_number=iteration + 1,
                        thought=content,
                        confidence=0.5,
                    )
                )
                trace.final_answer = content
                break

            thought = parsed.get("thought", "")
            action = parsed.get("action", "finish")
            action_input = parsed.get("action_input", {})
            is_final = parsed.get("is_final", False)

            step = ReasoningStep(
                step_id=str(uuid.uuid4()),
                step_number=iteration + 1,
                thought=thought,
                action=f"{action}({json.dumps(action_input)})" if action != "finish" else None,
                confidence=0.7,
            )

            if is_final or action == "finish":
                step.confidence = 0.9
                trace.steps.append(step)
                trace.final_answer = action_input.get("answer", thought)
                trace.total_confidence = 0.9
                break

            # OBSERVE - Execute the action and get observation
            observation = await self._execute_react_action(action, action_input)
            step.observation = observation
            trace.steps.append(step)

            # Add to conversation for next iteration
            conversation.append({"role": "assistant", "content": content})
            conversation.append({"role": "user", "content": f"OBSERVATION: {observation}"})

        if not trace.final_answer:
            # Compile answer from all steps
            trace.final_answer = "\n".join(
                f"Step {s.step_number}: {s.thought}" for s in trace.steps
            )
            trace.total_confidence = sum(s.confidence for s in trace.steps) / max(
                len(trace.steps), 1
            )

        self.traces[trace.trace_id] = trace
        self._log_trace(trace)

        return trace

    async def _execute_react_action(self, action: str, action_input: dict) -> str:
        """Execute an action in the ReAct loop and return observation"""
        try:
            from mcp_integration import ToolCall, mcp

            tool_call = ToolCall(tool_name=action, arguments=action_input)

            result = await mcp.execute_tool(tool_call)

            if result.success:
                return str(result.data)[: self.MAX_OBSERVATION_LENGTH]
            else:
                return f"Action failed: {result.error}"

        except Exception as e:
            return f"Action execution error: {str(e)}"

    # ===== Tree-of-Thought Planning =====

    async def tree_of_thought(
        self,
        query: str,
        context: Optional[dict] = None,
        num_branches: int = 3,
        max_depth: int = 3,
        beam_width: int = 2,
    ) -> ReasoningTrace:
        """
        Explore multiple reasoning branches simultaneously, evaluate each path,
        and backtrack from dead ends.

        Ideal for strategy, math, and creative challenges.

        Args:
            query: The problem to solve
            context: Additional context
            num_branches: Number of initial thought branches to explore
            max_depth: Maximum depth of thought tree
            beam_width: Number of best branches to keep at each level

        Returns:
            ReasoningTrace with the best reasoning path
        """
        trace = ReasoningTrace(
            trace_id=str(uuid.uuid4()), strategy=ReasoningStrategy.TREE_OF_THOUGHT, query=query
        )

        branches: dict[str, ThoughtBranch] = {}

        # Step 1: Generate initial thought branches
        generation_prompt = f"""\
You are exploring multiple approaches to solve a problem \
using Tree-of-Thought reasoning.

Problem: {query}

{f"Context: {json.dumps(context)}" if context else ""}

Generate {num_branches} DIFFERENT initial approaches to solve this problem.
Each approach should take a fundamentally different angle.

Respond in JSON:
{{
    "branches": [
        {{"thought": "Approach 1: ...", "reasoning": "This works because..."}},
        {{"thought": "Approach 2: ...", "reasoning": "This works because..."}},
        {{"thought": "Approach 3: ...", "reasoning": "This works because..."}}
    ]
}}"""

        decision, result = await self._get_router().execute_with_routing(
            task=generation_prompt, context={"requires_reasoning": True}
        )

        parsed = self._parse_json_response(result.get("content", ""))
        initial_branches = parsed.get("branches", []) if parsed else []

        # Create initial branch nodes
        for i, branch_data in enumerate(initial_branches[:num_branches]):
            branch = ThoughtBranch(
                branch_id=str(uuid.uuid4()),
                parent_id=None,
                thought=branch_data.get("thought", f"Approach {i + 1}"),
                score=0.0,
            )
            branches[branch.branch_id] = branch

        # Step 2: Evaluate and expand branches for each depth level
        current_level = list(branches.keys())

        for depth in range(max_depth):
            if not current_level:
                break

            # Evaluate all branches at current level
            evaluation_prompt = f"""Evaluate these reasoning approaches for the problem: {query}

Approaches:
{json.dumps([{"id": bid, "thought": branches[bid].thought} for bid in current_level], indent=2)}

Score each approach from 0.0 to 1.0 based on:
- Correctness of reasoning
- Likelihood of reaching the right answer
- Efficiency of the approach

Respond in JSON:
{{
    "scores": [
        {{
            "id": "{current_level[0] if current_level else "example"}",
            "score": 0.85,
            "feedback": "Strong because..."
        }}
    ]
}}"""

            _, eval_result = await self._get_router().execute_with_routing(
                task=evaluation_prompt, context={"requires_reasoning": True}
            )

            eval_parsed = self._parse_json_response(eval_result.get("content", ""))
            if eval_parsed:
                for score_data in eval_parsed.get("scores", []):
                    bid = score_data.get("id", "")
                    if bid in branches:
                        branches[bid].score = score_data.get("score", 0.5)

            # Keep only beam_width best branches
            scored_branches = sorted(
                current_level, key=lambda bid: branches[bid].score, reverse=True
            )
            active_branches = scored_branches[:beam_width]

            # Prune low-scoring branches
            for bid in scored_branches[beam_width:]:
                branches[bid].is_pruned = True

            # Expand best branches (if not at max depth)
            if depth < max_depth - 1:
                next_level = []
                for bid in active_branches:
                    parent = branches[bid]

                    expand_prompt = f"""Continue this reasoning path for the problem: {query}

Current thought: {parent.thought}
Current score: {parent.score}

Provide the next step in this reasoning path.

Respond in JSON:
{{
    "next_thought": "Building on the previous step...",
    "is_conclusion": false
}}"""

                    _, expand_result = await self._get_router().execute_with_routing(
                        task=expand_prompt, context={"requires_reasoning": True}
                    )

                    expand_parsed = self._parse_json_response(expand_result.get("content", ""))
                    if expand_parsed:
                        child = ThoughtBranch(
                            branch_id=str(uuid.uuid4()),
                            parent_id=bid,
                            thought=expand_parsed.get("next_thought", ""),
                            is_terminal=expand_parsed.get("is_conclusion", False),
                        )
                        branches[child.branch_id] = child
                        parent.children.append(child.branch_id)
                        next_level.append(child.branch_id)

                current_level = next_level
            else:
                # Mark remaining as terminal
                for bid in active_branches:
                    branches[bid].is_terminal = True

        # Step 3: Select best path and compile answer
        best_branch = max(branches.values(), key=lambda b: b.score)

        # Trace back the best path
        path = []
        current = best_branch
        while current:
            path.insert(0, current)
            current = branches.get(current.parent_id) if current.parent_id else None

        for i, branch in enumerate(path):
            trace.steps.append(
                ReasoningStep(
                    step_id=branch.branch_id,
                    step_number=i + 1,
                    thought=branch.thought,
                    confidence=branch.score,
                )
            )

        # Generate final answer from best path
        path_summary = " → ".join(b.thought[:100] for b in path)
        final_prompt = f"""Based on this reasoning path, provide a final answer.

Problem: {query}
Reasoning path: {path_summary}

Provide a clear, concise final answer."""

        _, final_result = await self._get_router().execute_with_routing(
            task=final_prompt, context={"requires_reasoning": True}
        )

        trace.final_answer = final_result.get("content", "")
        trace.total_confidence = best_branch.score
        trace.metadata["branches_explored"] = len(branches)
        trace.metadata["branches_pruned"] = sum(1 for b in branches.values() if b.is_pruned)
        trace.metadata["best_path_length"] = len(path)

        self.traces[trace.trace_id] = trace
        self._log_trace(trace)

        return trace

    # ===== Self-Consistency Verification =====

    async def self_consistency(
        self,
        query: str,
        context: Optional[dict] = None,
        num_samples: int = 3,
        temperature_range: tuple[float, float] = (0.5, 0.9),
    ) -> ReasoningTrace:
        """
        Sample multiple independent reasoning paths and select the most
        consistent answer — a built-in peer-review for every response.

        Args:
            query: The question to answer
            context: Additional context
            num_samples: Number of independent reasoning paths to sample
            temperature_range: Range of temperatures for diversity

        Returns:
            ReasoningTrace with consensus answer and confidence
        """
        trace = ReasoningTrace(
            trace_id=str(uuid.uuid4()), strategy=ReasoningStrategy.SELF_CONSISTENCY, query=query
        )

        # Generate multiple independent reasoning paths
        cot_prompt = f"""Solve this problem step-by-step:

Problem: {query}
{f"Context: {json.dumps(context)}" if context else ""}

Think through this carefully and provide:
1. Your step-by-step reasoning
2. Your final answer

Respond in JSON:
{{
    "reasoning": "Step 1: ... Step 2: ...",
    "answer": "The answer is...",
    "confidence": 0.85
}}"""

        answers = []
        reasoning_paths = []

        # Generate samples with varying temperatures for diversity
        temp_step = (temperature_range[1] - temperature_range[0]) / max(num_samples - 1, 1)

        tasks = []
        for i in range(num_samples):
            temp = temperature_range[0] + (temp_step * i)
            tasks.append(self._generate_sample(cot_prompt, temp, i))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Self-consistency sample {i} failed: {result}")
                continue

            parsed, content = result
            if parsed:
                answer = parsed.get("answer", "")
                reasoning = parsed.get("reasoning", "")
                confidence = parsed.get("confidence", 0.5)
            else:
                answer = content
                reasoning = content
                confidence = 0.5

            answers.append(answer)
            reasoning_paths.append(reasoning)

            trace.steps.append(
                ReasoningStep(
                    step_id=str(uuid.uuid4()),
                    step_number=i + 1,
                    thought=f"Path {i + 1}: {reasoning[:500]}",
                    confidence=confidence,
                )
            )

        if not answers:
            trace.final_answer = "Unable to generate consistent answers"
            trace.total_confidence = 0.0
            self.traces[trace.trace_id] = trace
            return trace

        # Vote on the most consistent answer
        consensus_answer, consensus_confidence = await self._vote_on_answers(
            query, answers, reasoning_paths
        )

        trace.final_answer = consensus_answer
        trace.total_confidence = consensus_confidence
        trace.metadata["num_samples"] = num_samples
        trace.metadata["num_valid_samples"] = len(answers)
        trace.metadata["all_answers"] = answers

        self.traces[trace.trace_id] = trace
        self._log_trace(trace)

        return trace

    async def _generate_sample(
        self, prompt: str, temperature: float, index: int
    ) -> tuple[Optional[dict], str]:
        """Generate a single reasoning sample"""
        from llm_gateway import TaskType

        result = await self._get_llm().complete(
            [{"role": "user", "content": prompt}],
            task_type=TaskType.REASONING,
            temperature=temperature,
        )
        content = result.get("content", "")
        parsed = self._parse_json_response(content)
        return parsed, content

    async def _vote_on_answers(
        self, query: str, answers: list[str], reasoning_paths: list[str]
    ) -> tuple[str, float]:
        """Vote across multiple answer paths to find consensus"""
        if len(answers) == 1:
            return answers[0], 0.7

        vote_prompt = f"""You are a judge evaluating multiple answers to the same question.

Question: {query}

Answers from independent reasoning paths:
{json.dumps(
    [
        {"path": i + 1, "answer": a, "reasoning": r[:300]}
        for i, (a, r) in enumerate(
            zip(answers, reasoning_paths)
        )
    ],
    indent=2,
)}

Select the BEST answer based on:
1. Consistency - Which answer appears most frequently or similarly across paths?
2. Correctness - Which reasoning path is most sound?
3. Completeness - Which answer is most thorough?

Respond in JSON:
{{
    "best_answer_index": 0,
    "consensus_answer": "The refined consensus answer...",
    "confidence": 0.9,
    "reasoning": "I chose this because..."
}}"""

        _, result = await self._get_router().execute_with_routing(
            task=vote_prompt, context={"requires_reasoning": True}
        )

        parsed = self._parse_json_response(result.get("content", ""))
        if parsed:
            return (parsed.get("consensus_answer", answers[0]), parsed.get("confidence", 0.7))

        # Fallback: return most common answer or first one
        return answers[0], 0.6

    # ===== Self-Reflection / Skeptic Loop =====

    async def self_reflect(self, trace: ReasoningTrace) -> ReasoningTrace:
        """
        Challenge the trace's conclusions with an internal skeptic sub-process.

        Takes the final answer and asks "What could be wrong?". If the skeptic
        identifies significant issues (confidence < REFLECTION_CONFIDENCE_THRESHOLD),
        re-runs reasoning with corrections appended as context.

        Args:
            trace: The ReasoningTrace to reflect on

        Returns:
            The original trace (if it holds up) or an improved trace with
            reflection metadata attached.
        """
        if not trace.final_answer:
            return trace

        for reflection_round in range(MAX_REFLECTION_ROUNDS):
            skeptic_prompt = f"""You are a rigorous skeptic reviewing an AI agent's reasoning.

Question / Task: {trace.query}

Proposed answer:
{trace.final_answer}

Reasoning steps taken:
{json.dumps([{"step": s.step_number, "thought": s.thought[:800]} for s in trace.steps], indent=2)}

Your job:
1. Identify logical errors, unsupported assumptions, or factual mistakes.
2. Note anything important that was overlooked.
3. Rate your confidence that the original answer is correct (0.0 – 1.0).

Respond in JSON:
{{
    "issues": ["issue 1", "issue 2"],
    "overlooked": ["thing 1"],
    "confidence_in_original": 0.75,
    "suggested_correction": "If confidence is low, suggest a better answer here.",
    "reasoning": "Explain your assessment."
}}"""

            decision, result = await self._get_router().execute_with_routing(
                task=skeptic_prompt, context={"requires_reasoning": True}
            )

            content = result.get("content", "")
            parsed = self._parse_json_response(content)

            reflection_meta = {
                "reflection_round": reflection_round + 1,
                "raw_skeptic_response": content[:500],
            }

            if parsed:
                skeptic_confidence = float(parsed.get("confidence_in_original", 0.5))
                issues = parsed.get("issues", [])
                suggested_correction = parsed.get("suggested_correction", "")

                reflection_meta.update(
                    {
                        "skeptic_confidence": skeptic_confidence,
                        "issues_found": issues,
                        "suggested_correction": suggested_correction[:300],
                    }
                )

                if skeptic_confidence >= REFLECTION_CONFIDENCE_THRESHOLD:
                    # Answer holds up — accept it
                    trace.metadata.setdefault("reflections", []).append(reflection_meta)
                    logger.info(
                        f"Self-reflect round {reflection_round + 1}: "
                        f"answer accepted (skeptic confidence={skeptic_confidence:.2f})"
                    )
                    break

                # Skeptic found significant issues — re-run reasoning with corrections
                logger.warning(
                    f"Self-reflect round {reflection_round + 1}: skeptic confidence "
                    f"{skeptic_confidence:.2f} < {REFLECTION_CONFIDENCE_THRESHOLD}, re-reasoning"
                )

                correction_context = {
                    "previous_answer": trace.final_answer,
                    "issues_found": issues,
                    "suggested_correction": suggested_correction,
                    "instruction": "Address the issues identified and provide a corrected answer.",
                }

                corrected_trace = await self.chain_of_thought(
                    query=trace.query,
                    context=correction_context,
                )

                # Carry forward reflection history (copy to avoid duplication)
                prior_reflections = list(trace.metadata.get("reflections", []))
                prior_reflections.append(reflection_meta)
                corrected_trace.metadata["reflections"] = prior_reflections
                corrected_trace.metadata["original_trace_id"] = trace.trace_id
                trace = corrected_trace
            else:
                # Could not parse skeptic response — keep the original answer
                reflection_meta["parse_error"] = True
                trace.metadata.setdefault("reflections", []).append(reflection_meta)
                logger.warning("Self-reflect: could not parse skeptic response, keeping original")
                break

        trace.metadata["reflection_completed"] = True
        return trace

    # ===== Auto-Select Strategy =====

    async def reason(
        self,
        query: str,
        context: Optional[dict] = None,
        strategy: Optional[ReasoningStrategy] = None,
        enable_reflection: bool = True,
        use_karpathy: bool = False,
        high_stakes: bool = False,
        **kwargs,
    ) -> ReasoningTrace:
        """
        Main entry point: automatically select and execute the best reasoning strategy.

        Args:
            query: The problem/task
            context: Additional context
            strategy: Force a specific strategy (auto-selects if None)
            enable_reflection: Run self-reflection skeptic loop after reasoning
            use_karpathy: Use KarpathyEngine enhancements (temperature calibration, PRM)
            high_stakes: Use self-play debate for critical decisions
            **kwargs: Additional arguments for the specific strategy

        Returns:
            ReasoningTrace with results
        """
        if strategy is None:
            strategy = self._select_strategy(query, context)

        logger.info(f"Using reasoning strategy: {strategy.value}")

        karpathy_meta: dict[str, Any] = {}

        # --- Karpathy pre-reasoning: temperature calibration ---
        calibrated_temp: Optional[float] = None
        if use_karpathy:
            engine = self._get_karpathy_engine()
            calibrated_temp = engine.temperature.get_temperature(query)
            karpathy_meta["calibrated_temperature"] = calibrated_temp
            kwargs.setdefault("temperature", calibrated_temp)
            logger.info(f"Karpathy temperature calibration: {calibrated_temp}")

        # --- High-stakes: run self-play debate instead of normal strategy ---
        if high_stakes and use_karpathy:
            engine = self._get_karpathy_engine()
            debate_result = await engine.debate(topic=query, rounds=2, context=context)
            karpathy_meta["debate_verdict"] = debate_result.final_verdict[:300]
            karpathy_meta["debate_confidence"] = debate_result.confidence
            karpathy_meta["debate_cost"] = debate_result.cost
            logger.info(f"Karpathy debate completed: confidence={debate_result.confidence:.2f}")
            # Enrich context with debate findings for the main strategy
            context = context or {}
            context["debate_verdict"] = debate_result.final_verdict

        # --- Core reasoning ---
        if strategy == ReasoningStrategy.CHAIN_OF_THOUGHT:
            trace = await self.chain_of_thought(query, context, **kwargs)
        elif strategy == ReasoningStrategy.REACT:
            trace = await self.react_loop(query, context=context, **kwargs)
        elif strategy == ReasoningStrategy.TREE_OF_THOUGHT:
            trace = await self.tree_of_thought(query, context, **kwargs)
        elif strategy == ReasoningStrategy.SELF_CONSISTENCY:
            trace = await self.self_consistency(query, context, **kwargs)
        else:
            trace = await self.chain_of_thought(query, context, **kwargs)

        # --- Karpathy post-reasoning: Process Reward Model verification ---
        if use_karpathy and trace.steps:
            try:
                engine = self._get_karpathy_engine()
                step_texts = [s.thought for s in trace.steps if s.thought]
                if step_texts:
                    prm_result = await engine.verify_reasoning(query, step_texts)
                    karpathy_meta["prm_overall_score"] = prm_result.overall_score
                    karpathy_meta["prm_passed"] = prm_result.passed_threshold
                    if prm_result.weakest_step:
                        karpathy_meta["prm_weakest_step"] = {
                            "step_number": prm_result.weakest_step.step_number,
                            "score": prm_result.weakest_step.score,
                            "critique": prm_result.weakest_step.critique[:300],
                        }
                    logger.info(
                        f"Karpathy PRM score: {prm_result.overall_score:.2f}, "
                        f"passed={prm_result.passed_threshold}"
                    )
            except Exception as e:
                logger.warning(f"Karpathy PRM verification failed: {e}")
                karpathy_meta["prm_error"] = str(e)

        if karpathy_meta:
            trace.metadata["karpathy"] = karpathy_meta

        # --- Self-reflection skeptic loop ---
        if enable_reflection:
            trace = await self.self_reflect(trace)

        return trace

    def _select_strategy(self, query: str, context: Optional[dict] = None) -> ReasoningStrategy:
        """Auto-select the best reasoning strategy based on query characteristics"""
        query_lower = query.lower()

        # ReAct: tasks that need tool use or real-world interaction
        react_indicators = ["search", "look up", "find", "check", "browse", "fetch", "get data"]
        if any(ind in query_lower for ind in react_indicators):
            return ReasoningStrategy.REACT

        # Tree-of-Thought: creative, strategic, or multi-path problems
        tot_indicators = [
            "creative",
            "strategy",
            "design",
            "multiple ways",
            "brainstorm",
            "explore",
            "alternatives",
            "options",
            "best approach",
        ]
        if any(ind in query_lower for ind in tot_indicators):
            return ReasoningStrategy.TREE_OF_THOUGHT

        # Self-Consistency: high-stakes decisions or factual questions
        sc_indicators = [
            "verify",
            "accurate",
            "certain",
            "factual",
            "correct answer",
            "important",
            "critical",
            "precise",
        ]
        if any(ind in query_lower for ind in sc_indicators):
            return ReasoningStrategy.SELF_CONSISTENCY

        # Default: Chain-of-Thought for general reasoning
        return ReasoningStrategy.CHAIN_OF_THOUGHT

    # ===== Utility Methods =====

    def _parse_json_response(self, content: str) -> Optional[dict]:
        """Safely parse JSON from LLM response"""
        try:
            # Try direct parse
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code blocks
        try:
            if "```json" in content:
                start = content.index("```json") + 7
                end = content.index("```", start)
                return json.loads(content[start:end].strip())
            elif "```" in content:
                start = content.index("```") + 3
                end = content.index("```", start)
                return json.loads(content[start:end].strip())
        except (json.JSONDecodeError, ValueError):
            pass

        # Try to find JSON object in content
        try:
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
        except json.JSONDecodeError:
            pass

        return None

    def _log_trace(self, trace: ReasoningTrace):
        """Log a reasoning trace to the thoughts logger"""
        tl = self._get_thoughts_logger()
        if tl:
            tl.log_reasoning(
                f"[{trace.strategy.value}] {trace.query[:100]}... → "
                f"Steps: {len(trace.steps)}, Confidence: {trace.total_confidence:.2f}",
                context={
                    "trace_id": trace.trace_id,
                    "strategy": trace.strategy.value,
                    "steps": len(trace.steps),
                    "confidence": trace.total_confidence,
                },
            )

    def get_trace(self, trace_id: str) -> Optional[ReasoningTrace]:
        """Retrieve a reasoning trace by ID"""
        return self.traces.get(trace_id)

    def get_recent_traces(self, limit: int = 10) -> list[ReasoningTrace]:
        """Get recent reasoning traces"""
        traces = sorted(self.traces.values(), key=lambda t: t.created_at, reverse=True)
        return traces[:limit]

    def export_trace(self, trace_id: str) -> Optional[dict]:
        """Export a trace as a dictionary for serialization"""
        trace = self.traces.get(trace_id)
        if not trace:
            return None

        return {
            "trace_id": trace.trace_id,
            "strategy": trace.strategy.value,
            "query": trace.query,
            "steps": [
                {
                    "step_number": s.step_number,
                    "thought": s.thought,
                    "action": s.action,
                    "observation": s.observation,
                    "confidence": s.confidence,
                }
                for s in trace.steps
            ],
            "final_answer": trace.final_answer,
            "total_confidence": trace.total_confidence,
            "metadata": trace.metadata,
            "created_at": trace.created_at,
        }


# Global cognitive core instance
cognitive_core = CognitiveCore()
