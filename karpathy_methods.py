"""
Karpathy LLM Methods - Advanced inference-time compute techniques
Implements Andrej Karpathy's key insights on LLM operational excellence:

1. Temperature Calibration  – task-type aware temperature selection
2. Scratchpad Reasoning     – extended private thinking before committing to an answer
3. Best-of-N Sampling       – generate N drafts, score and return the best
4. Few-Shot Library         – curated example bank with vector-similarity retrieval
5. Process Reward Model     – score intermediate reasoning steps, not just final answers
6. Self-Play Debate         – two-agent proposition / critique debate
7. Constitutional Reviewer  – check outputs against a configurable principle set
8. KarpathyEngine           – unified interface combining all techniques
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from loguru import logger

from config import settings

# ============================================================
# Data Classes
# ============================================================


class TaskNature(str, Enum):
    """Nature of a task, used for temperature calibration."""

    FACTUAL = "factual"  # Deterministic: exact answers, maths, facts → T≈0
    ANALYTICAL = "analytical"  # Structured: code, logic, planning → T≈0.2
    BALANCED = "balanced"  # Mixed: summarisation, Q&A → T≈0.5
    CREATIVE = "creative"  # Open-ended: brainstorm, stories, design → T≈0.9
    EXPLORATORY = "exploratory"  # Max diversity wanted → T≈1.0


@dataclass
class ScratchpadResult:
    """Result from scratchpad reasoning."""

    trace_id: str
    query: str
    scratchpad: str  # Private thinking (not shown to user by default)
    final_answer: str
    confidence: float
    model: str = ""
    cost: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class DraftCandidate:
    """A single candidate produced by Best-of-N sampling."""

    draft_id: str
    content: str
    score: float = 0.0
    score_rationale: str = ""
    temperature_used: float = 0.7


@dataclass
class BestOfNResult:
    """Result from Best-of-N sampling."""

    query: str
    best_draft: DraftCandidate
    all_drafts: list[DraftCandidate]
    n: int
    cost: float = 0.0


@dataclass
class FewShotExample:
    """A single few-shot example in the library."""

    example_id: str
    task_type: str
    input_text: str
    output_text: str
    tags: list[str] = field(default_factory=list)
    quality_score: float = 1.0
    usage_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class StepScore:
    """Score for a single reasoning step from the Process Reward Model."""

    step_number: int
    step_text: str
    score: float  # 0.0 – 1.0
    is_valid: bool
    critique: str = ""


@dataclass
class PRMResult:
    """Result from the Process Reward Model."""

    query: str
    step_scores: list[StepScore]
    overall_score: float
    weakest_step: Optional[StepScore] = None
    passed_threshold: bool = False


@dataclass
class DebateRound:
    """One round of a self-play debate."""

    round_number: int
    proposition: str
    critique: str
    rebuttal: str = ""


@dataclass
class DebateResult:
    """Result of a self-play debate."""

    topic: str
    rounds: list[DebateRound]
    final_verdict: str
    confidence: float
    cost: float = 0.0


@dataclass
class ConstitutionalCheck:
    """Result of a single constitutional principle check."""

    principle: str
    passed: bool
    violation_description: str = ""
    revised_output: str = ""


@dataclass
class ConstitutionalResult:
    """Result from the Constitutional Reviewer."""

    original_output: str
    final_output: str
    checks: list[ConstitutionalCheck]
    revision_count: int
    all_passed: bool
    cost: float = 0.0


# ============================================================
# 1. Temperature Calibrator
# ============================================================


class TemperatureCalibrator:
    """
    Karpathy insight: "temperature 0 for anything that has a right answer,
    higher temperatures for creative tasks where diversity matters."

    Automatically selects the optimal sampling temperature based on task nature.
    Temperature values are configurable via settings.karpathy_temp_* env knobs.
    """

    # Keywords that hint at each nature
    NATURE_KEYWORDS: dict[TaskNature, list[str]] = {
        TaskNature.FACTUAL: [
            "what is",
            "when did",
            "how many",
            "calculate",
            "compute",
            "fact",
            "true or false",
            "definition",
            "formula",
            "convert",
            "exact",
            "precisely",
        ],
        TaskNature.ANALYTICAL: [
            "code",
            "implement",
            "debug",
            "fix",
            "analyse",
            "analyze",
            "compare",
            "evaluate",
            "plan",
            "design",
            "algorithm",
            "logic",
            "explain why",
            "reasoning",
        ],
        TaskNature.BALANCED: [
            "summarise",
            "summarize",
            "explain",
            "describe",
            "review",
            "translate",
            "rewrite",
            "list",
            "what are the",
            "pros and cons",
        ],
        TaskNature.CREATIVE: [
            "brainstorm",
            "generate ideas",
            "creative",
            "imagine",
            "story",
            "write a",
            "compose",
            "invent",
            "suggest alternatives",
            "possibilities",
        ],
        TaskNature.EXPLORATORY: [
            "explore",
            "what if",
            "hypothetically",
            "speculate",
            "unconventional",
            "diverse",
            "varied",
            "many different",
            "unexpected",
        ],
    }

    @property
    def TEMPERATURE_MAP(self) -> dict[TaskNature, float]:
        """Temperature map populated from settings, with hard-coded fallbacks."""
        return {
            TaskNature.FACTUAL: getattr(settings, "karpathy_temp_factual", 0.0),
            TaskNature.ANALYTICAL: getattr(settings, "karpathy_temp_analytical", 0.2),
            TaskNature.BALANCED: getattr(settings, "karpathy_temp_balanced", 0.5),
            TaskNature.CREATIVE: getattr(settings, "karpathy_temp_creative", 0.9),
            TaskNature.EXPLORATORY: getattr(settings, "karpathy_temp_exploratory", 1.0),
        }

    def classify_task(self, task: str) -> TaskNature:
        """Classify a task into a nature category by keyword heuristics."""
        task_lower = task.lower()
        scores: dict[TaskNature, int] = dict.fromkeys(TaskNature, 0)

        for nature, keywords in self.NATURE_KEYWORDS.items():
            for kw in keywords:
                if kw in task_lower:
                    scores[nature] += 1

        best = max(scores, key=scores.get)
        if scores[best] == 0:
            return TaskNature.BALANCED  # sensible default

        return best

    def get_temperature(self, task: str, override_nature: Optional[TaskNature] = None) -> float:
        """Return the calibrated temperature for a given task."""
        nature = override_nature or self.classify_task(task)
        base_temp = self.TEMPERATURE_MAP[nature]

        # Slight positive nudge if task is long (likely nuanced)
        if len(task.split()) > 100:
            base_temp = min(1.0, base_temp + 0.05)

        logger.debug(f"Temperature calibrated to {base_temp} ({nature.value}) for task")
        return base_temp

    def get_temperature_for_role(self, role: str) -> float:
        """Return temperature appropriate for an agent role."""
        role_temps = {
            "architect": 0.2,  # Structured planning
            "worker": 0.0,  # Deterministic execution
            "coder": 0.1,  # Mostly deterministic code
            "researcher": 0.4,  # Some exploration
            "creative": 0.9,  # Maximum creativity
        }
        return role_temps.get(role.lower(), settings.temperature)


# ============================================================
# 2. Scratchpad Reasoner
# ============================================================


class ScratchpadReasoner:
    """
    Karpathy insight: "Give the model a private scratchpad to think in
    before it commits to a final answer — especially for complex questions."

    Similar to o1's extended thinking, this forces deliberate exploration
    before the answer is locked in.
    """

    SCRATCHPAD_SYSTEM = """You are an expert reasoning system.

STEP 1 – SCRATCHPAD: You MUST think through the problem in a private scratchpad
before writing your final answer. Use the scratchpad to:
  • Identify what you know and don't know
  • Break the problem into sub-problems
  • Consider multiple possible answers
  • Identify potential mistakes or edge cases
  • Verify your reasoning

STEP 2 – FINAL ANSWER: After thorough scratchpad thinking, write a clear, concise
final answer that does not repeat the scratchpad reasoning.

Always respond in this JSON format:
{
    "scratchpad": "<your private, extensive thinking>",
    "final_answer": "<concise answer after reflection>",
    "confidence": 0.85
}"""

    def __init__(self):
        self._router = None

    def _get_router(self):
        if self._router is None:
            from router import router

            self._router = router
        return self._router

    async def think(
        self, query: str, context: Optional[dict] = None, temperature: Optional[float] = None
    ) -> ScratchpadResult:
        """
        Reason about a query using a private scratchpad.

        Args:
            query: The question or task
            context: Optional extra context
            temperature: Override temperature (auto-calibrated if None)

        Returns:
            ScratchpadResult with scratchpad and final answer
        """
        calibrator = TemperatureCalibrator()
        temp = temperature if temperature is not None else calibrator.get_temperature(query)

        prompt = f"""{query}

{f"Context: {json.dumps(context, indent=2)}" if context else ""}

Use your scratchpad to reason carefully before answering."""

        decision, result = await self._get_router().execute_with_routing(
            task=prompt,
            context={"requires_reasoning": True, "system_override": self.SCRATCHPAD_SYSTEM},
            temperature=temp,
        )

        content = result.get("content", "")
        parsed = self._parse_json(content)

        if parsed:
            scratchpad = parsed.get("scratchpad", "")
            final_answer = parsed.get("final_answer", content)
            confidence = float(parsed.get("confidence", 0.7))
        else:
            # Fallback: split on a separator if present
            if "FINAL ANSWER:" in content:
                parts = content.split("FINAL ANSWER:", 1)
                scratchpad = parts[0].strip()
                final_answer = parts[1].strip()
            else:
                scratchpad = content
                final_answer = content
            confidence = 0.5

        return ScratchpadResult(
            trace_id=str(uuid.uuid4()),
            query=query,
            scratchpad=scratchpad,
            final_answer=final_answer,
            confidence=confidence,
            model=decision.model,
            cost=decision.estimated_cost,
        )

    def _parse_json(self, content: str) -> Optional[dict]:
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


# ============================================================
# 3. Best-of-N Sampler
# ============================================================


class BestOfNSampler:
    """
    Karpathy insight: "Scaling inference compute: run the same prompt N times
    with temperature > 0, then pick the best response using a verifier or
    reward model. You get diminishing returns but real quality gains."

    Generates N independent drafts and selects the highest-scoring one.
    """

    DEFAULT_N = 3

    def __init__(self):
        self._router = None

    def _get_router(self):
        if self._router is None:
            from router import router

            self._router = router
        return self._router

    async def sample(
        self,
        query: str,
        n: Optional[int] = None,
        temperature: float = 0.7,
        context: Optional[dict] = None,
        scoring_criteria: Optional[list[str]] = None,
    ) -> BestOfNResult:
        """
        Generate N drafts and return the best-scoring one.

        Args:
            query: The task or question
            n: Number of drafts (defaults to config or 3)
            temperature: Sampling temperature for drafts
            context: Additional context
            scoring_criteria: Criteria to score against (auto-selected if None)

        Returns:
            BestOfNResult with the best draft and all candidates
        """
        n = n or getattr(settings, "karpathy_best_of_n", self.DEFAULT_N)
        criteria = scoring_criteria or [
            "Accuracy and correctness",
            "Clarity and completeness",
            "Addresses all parts of the question",
            "No unnecessary hedging or verbosity",
        ]

        logger.info(f"Best-of-N sampling: generating {n} drafts at T={temperature}")

        # Generate N drafts concurrently
        draft_tasks = [self._generate_draft(query, temperature, context, i) for i in range(n)]
        raw_drafts = await asyncio.gather(*draft_tasks, return_exceptions=True)

        drafts: list[DraftCandidate] = []
        total_cost = 0.0

        for i, draft in enumerate(raw_drafts):
            if isinstance(draft, Exception):
                logger.warning(f"Draft {i + 1} failed: {draft}")
                continue
            drafts.append(draft)

        if not drafts:
            raise RuntimeError("All draft generations failed")

        # Accumulate successful draft-generation costs
        total_cost = sum(float(getattr(d, "cost", 0.0) or 0.0) for d in drafts)
        draft_cost_by_id = {
            getattr(d, "id", i): float(getattr(d, "cost", 0.0) or 0.0) for i, d in enumerate(drafts)
        }

        # Score all drafts
        scored_drafts = await self._score_drafts(query, drafts, criteria)

        # Add any incremental scoring/judging cost without double-counting
        scoring_cost = 0.0
        for i, draft in enumerate(scored_drafts):
            draft_id = getattr(draft, "id", i)
            scored_cost = float(getattr(draft, "cost", 0.0) or 0.0)
            original_cost = draft_cost_by_id.get(draft_id, 0.0)
            if scored_cost > original_cost:
                scoring_cost += scored_cost - original_cost
        total_cost += scoring_cost
        # Select best
        best = max(scored_drafts, key=lambda d: d.score)

        logger.info(
            f"Best-of-N complete: best score={best.score:.2f} "
            f"(avg={sum(d.score for d in scored_drafts) / len(scored_drafts):.2f})"
        )

        return BestOfNResult(
            query=query, best_draft=best, all_drafts=scored_drafts, n=n, cost=total_cost
        )

    async def _generate_draft(
        self, query: str, temperature: float, context: Optional[dict], draft_index: int
    ) -> DraftCandidate:
        """Generate a single draft."""
        decision, result = await self._get_router().execute_with_routing(
            task=query, context=context, temperature=temperature
        )

        return DraftCandidate(
            draft_id=str(uuid.uuid4()),
            content=result.get("content", ""),
            temperature_used=temperature,
        )

    async def _score_drafts(
        self, query: str, drafts: list[DraftCandidate], criteria: list[str]
    ) -> list[DraftCandidate]:
        """Score all drafts using an LLM judge."""
        if len(drafts) == 1:
            drafts[0].score = 1.0
            drafts[0].score_rationale = "Only candidate"
            return drafts

        drafts_text = "\n\n".join(
            f"=== Draft {i + 1} ===\n{d.content}" for i, d in enumerate(drafts)
        )

        n_drafts = len(drafts)
        scoring_prompt = f"""\
You are a strict judge. Score these \
{n_drafts} responses to the question below.

Question: {query}

Scoring criteria:
{json.dumps(criteria, indent=2)}

Responses:
{drafts_text}

Score each draft from 0.0 to 1.0 against the criteria. Be discriminating.

Respond in JSON:
{{
    "scores": [
        {{"draft": 1, "score": 0.92, "rationale": "..."}},
        {{"draft": 2, "score": 0.74, "rationale": "..."}}
    ]
}}"""

        _, judge_result = await self._get_router().execute_with_routing(
            task=scoring_prompt, context={"requires_reasoning": True}
        )

        parsed = self._parse_json(judge_result.get("content", ""))
        if parsed:
            for score_data in parsed.get("scores", []):
                idx = score_data.get("draft", 1) - 1
                if 0 <= idx < len(drafts):
                    drafts[idx].score = float(score_data.get("score", 0.5))
                    drafts[idx].score_rationale = score_data.get("rationale", "")
        else:
            # Fallback: assign equal scores
            for d in drafts:
                d.score = 0.5

        return drafts

    def _parse_json(self, content: str) -> Optional[dict]:
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


# ============================================================
# 4. Few-Shot Library
# ============================================================


class FewShotLibrary:
    """
    Karpathy insight: "Few-shot prompting is enormously powerful because
    the model has already seen millions of similar examples in pretraining.
    Giving it a few relevant examples at inference time can dramatically
    improve output quality on structured tasks."

    Maintains a library of curated input/output examples, retrieved by
    semantic similarity to the current task.
    """

    # Built-in seed examples
    SEED_EXAMPLES: list[dict] = [
        {
            "task_type": "code_review",
            "input": "Review this Python function for bugs:\ndef divide(a, b):\n    return a / b",
            "output": (
                "Issue: Division by zero not handled. Fix:\n"
                "def divide(a, b):\n"
                "    if b == 0:\n"
                "        raise ValueError('Division by zero')\n"
                "    return a / b"
            ),
            "tags": ["code", "review", "python", "bug"],
        },
        {
            "task_type": "summarization",
            "input": (
                "Summarize: The Federal Reserve raised"
                " interest rates by 0.25% in a unanimous"
                " vote, citing continued inflation"
                " pressures above the 2% target."
            ),
            "output": "The Fed raised rates by 0.25% due to persistent above-target inflation.",
            "tags": ["summarize", "finance", "concise"],
        },
        {
            "task_type": "reasoning",
            "input": (
                "If all Bloops are Razzies and all"
                " Razzies are Lazzies, are all"
                " Bloops definitely Lazzies?"
            ),
            "output": (
                "Yes. By transitivity: Bloop → Razzie"
                " → Lazzie. Therefore all Bloops"
                " are Lazzies."
            ),
            "tags": ["logic", "reasoning", "syllogism"],
        },
        {
            "task_type": "data_extraction",
            "input": (
                "Extract name and email: 'Contact"
                " John Smith at john@example.com"
                " for more info.'"
            ),
            "output": '{"name": "John Smith", "email": "john@example.com"}',
            "tags": ["extraction", "structured", "json"],
        },
        {
            "task_type": "planning",
            "input": "Plan a task: Deploy a new API to production.",
            "output": (
                "1. Code review & tests pass\n"
                "2. Staging deploy & smoke test\n"
                "3. Feature flag rollout"
                " (10% → 50% → 100%)\n"
                "4. Monitor error rates\n"
                "5. Rollback plan ready"
            ),
            "tags": ["planning", "deployment", "steps"],
        },
        {
            "task_type": "classification",
            "input": (
                "Classify sentiment: 'The product"
                " was absolutely terrible and broke"
                " after one day.'"
            ),
            "output": '{"sentiment": "negative", "intensity": "strong", "confidence": 0.97}',
            "tags": ["classification", "sentiment", "json"],
        },
    ]

    def __init__(self):
        self._examples: list[FewShotExample] = []
        self._embedder = None
        self._embeddings: list[Any] = []
        self._load_seeds()

    def _load_seeds(self):
        for seed in self.SEED_EXAMPLES:
            self._examples.append(
                FewShotExample(
                    example_id=str(uuid.uuid4()),
                    task_type=seed["task_type"],
                    input_text=seed["input"],
                    output_text=seed["output"],
                    tags=seed.get("tags", []),
                )
            )

    def _get_embedder(self):
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
                # Pre-compute embeddings for seed examples
                texts = [f"{e.task_type} {e.input_text}" for e in self._examples]
                self._embeddings = self._embedder.encode(texts).tolist()
            except ImportError:
                logger.warning(
                    "sentence-transformers not available; few-shot uses keyword matching"
                )
        return self._embedder

    def add_example(
        self,
        task_type: str,
        input_text: str,
        output_text: str,
        tags: Optional[list[str]] = None,
        quality_score: float = 1.0,
    ) -> str:
        """Add a new example to the library."""
        example = FewShotExample(
            example_id=str(uuid.uuid4()),
            task_type=task_type,
            input_text=input_text,
            output_text=output_text,
            tags=tags or [],
            quality_score=quality_score,
        )
        self._examples.append(example)

        # Re-embed if embedder is active
        if self._embedder:
            new_emb = self._embedder.encode([f"{task_type} {input_text}"]).tolist()
            self._embeddings.append(new_emb[0])

        return example.example_id

    def retrieve(
        self, query: str, k: int = 3, task_type: Optional[str] = None
    ) -> list[FewShotExample]:
        """
        Retrieve the k most relevant examples for a query.

        Uses vector similarity when embedder is available,
        falls back to keyword overlap otherwise.
        """
        candidates = self._examples
        if task_type:
            typed = [e for e in candidates if e.task_type == task_type]
            candidates = typed if typed else candidates

        if not candidates:
            return []

        embedder = self._get_embedder()
        if embedder and len(self._embeddings) == len(self._examples):
            # Vector similarity retrieval
            query_emb = embedder.encode([query])[0]
            import numpy as np

            query_vec = np.array(query_emb)

            # Build an index from example → its embedding position in self._embeddings
            example_index: dict[int, int] = {id(ex): i for i, ex in enumerate(self._examples)}

            scored: list[tuple[float, FewShotExample]] = []
            for example in candidates:
                emb_pos = example_index.get(id(example))
                if emb_pos is None:
                    continue
                emb_vec = np.array(self._embeddings[emb_pos])
                sim = float(
                    np.dot(query_vec, emb_vec)
                    / (np.linalg.norm(query_vec) * np.linalg.norm(emb_vec) + 1e-8)
                )
                scored.append((sim * example.quality_score, example))

            scored.sort(key=lambda x: x[0], reverse=True)
            return [ex for _, ex in scored[:k]]
        else:
            # Keyword overlap fallback
            query_words = set(query.lower().split())
            scored = []
            for ex in candidates:
                ex_words = set(f"{ex.input_text} {' '.join(ex.tags)}".lower().split())
                overlap = len(query_words & ex_words) / max(len(query_words), 1)
                scored.append((overlap * ex.quality_score, ex))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [ex for _, ex in scored[:k]]

    def build_few_shot_block(
        self,
        query: str,
        k: int = 3,
        task_type: Optional[str] = None,
        format_fn: Optional[Any] = None,
    ) -> str:
        """
        Retrieve examples and format them as a few-shot block for insertion
        into a prompt.

        Args:
            query: The current task
            k: Number of examples to retrieve
            task_type: Optional task type filter
            format_fn: Optional callable(example) -> str

        Returns:
            Formatted few-shot block string
        """
        examples = self.retrieve(query, k=k, task_type=task_type)
        if not examples:
            return ""

        if format_fn:
            return "\n\n".join(format_fn(e) for e in examples)

        lines = ["Here are some examples of how to handle similar tasks:\n"]
        for i, ex in enumerate(examples, 1):
            lines.append(f"Example {i}:")
            lines.append(f"Input: {ex.input_text}")
            lines.append(f"Output: {ex.output_text}")
            lines.append("")

        return "\n".join(lines)


# ============================================================
# 5. Process Reward Model (PRM)
# ============================================================


class ProcessRewardModel:
    """
    Karpathy insight (from o1 / AlphaCode discussion):
    "Don't just verify the final answer — score every intermediate step.
    A chain-of-thought with a wrong step mid-way may still produce a
    correct-looking final answer by accident. PRMs catch these failures."

    Scores each reasoning step independently and flags weak links.
    """

    DEFAULT_THRESHOLD = 0.6

    def __init__(self):
        self._router = None

    def _get_router(self):
        if self._router is None:
            from router import router

            self._router = router
        return self._router

    async def score_steps(
        self, query: str, steps: list[str], threshold: Optional[float] = None
    ) -> PRMResult:
        """
        Score a list of reasoning steps for logical validity.

        Args:
            query: The original question / task
            steps: List of reasoning step strings
            threshold: Minimum passing score per step (defaults to 0.6)

        Returns:
            PRMResult with per-step scores and overall assessment
        """
        thresh = threshold or getattr(settings, "karpathy_prm_threshold", self.DEFAULT_THRESHOLD)

        steps_text = "\n".join(f"Step {i + 1}: {s}" for i, s in enumerate(steps))

        scoring_prompt = f"""You are a process reward model. Evaluate each reasoning step for:
1. Logical validity – does it follow from previous steps?
2. Factual correctness – is the claim accurate?
3. Progress – does it move toward the answer?

Problem: {query}

Reasoning steps:
{steps_text}

Score each step from 0.0 to 1.0. A step scoring below {thresh} should be flagged.

Respond in JSON:
{{
    "step_scores": [
        {{"step": 1, "score": 0.95, "is_valid": true, "critique": "Correct and clear"}},
        {{"step": 2, "score": 0.42, "is_valid": false, \
"critique": "This step makes an unwarranted assumption..."}}
    ],
    "overall_score": 0.78
}}"""

        _, result = await self._get_router().execute_with_routing(
            task=scoring_prompt, context={"requires_reasoning": True}
        )

        content = result.get("content", "")
        parsed = self._parse_json(content)

        step_scores: list[StepScore] = []

        if parsed:
            for ss in parsed.get("step_scores", []):
                step_num = ss.get("step", 0) - 1
                step_text = steps[step_num] if 0 <= step_num < len(steps) else ""
                step_scores.append(
                    StepScore(
                        step_number=ss.get("step", step_num + 1),
                        step_text=step_text,
                        score=float(ss.get("score", 0.5)),
                        is_valid=bool(ss.get("is_valid", True)),
                        critique=ss.get("critique", ""),
                    )
                )
            overall_score = float(parsed.get("overall_score", 0.5))
        else:
            # Fallback: score everything as neutral
            for i, s in enumerate(steps):
                step_scores.append(
                    StepScore(step_number=i + 1, step_text=s, score=0.5, is_valid=True)
                )
            overall_score = 0.5

        weakest = min(step_scores, key=lambda s: s.score) if step_scores else None
        passed = overall_score >= thresh and all(s.score >= thresh for s in step_scores)

        return PRMResult(
            query=query,
            step_scores=step_scores,
            overall_score=overall_score,
            weakest_step=weakest,
            passed_threshold=passed,
        )

    def _parse_json(self, content: str) -> Optional[dict]:
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


# ============================================================
# 6. Self-Play Debate
# ============================================================


class SelfPlayDebate:
    """
    Karpathy insight: "Multi-agent debate improves answer quality on hard
    problems. Two models with different perspectives challenge each other,
    forcing deeper reasoning and catching errors."

    Implements structured debate between a Proposer and a Critic.
    A Judge agent evaluates the debate and delivers a verdict.
    """

    DEFAULT_ROUNDS = 2

    def __init__(self):
        self._router = None

    def _get_router(self):
        if self._router is None:
            from router import router

            self._router = router
        return self._router

    async def debate(
        self, topic: str, rounds: Optional[int] = None, context: Optional[dict] = None
    ) -> DebateResult:
        """
        Run a structured debate on a topic to arrive at a well-reasoned answer.

        Args:
            topic: The question, claim, or decision to debate
            rounds: Number of debate rounds (default 2)
            context: Additional context

        Returns:
            DebateResult with full debate transcript and final verdict
        """
        num_rounds = rounds or getattr(settings, "karpathy_debate_rounds", self.DEFAULT_ROUNDS)
        debate_rounds: list[DebateRound] = []
        total_cost = 0.0

        context_str = f"\n\nContext: {json.dumps(context)}" if context else ""

        # Initial proposition
        prop_prompt = f"""You are the Proposer in a structured debate.

Topic: {topic}{context_str}

State your position clearly and provide your strongest arguments in support.
Be specific, use evidence and logical reasoning."""

        _, prop_result = await self._get_router().execute_with_routing(
            task=prop_prompt, context={"requires_reasoning": True}
        )
        proposition = prop_result.get("content", "")

        for round_num in range(1, num_rounds + 1):
            # Critic's challenge
            crit_prompt = f"""You are the Critic in a structured debate.

Topic: {topic}

The Proposer has argued:
{proposition}

Your role: Identify weaknesses, logical flaws, missing evidence, or alternative views.
Be rigorous and specific. This is round {round_num} of {num_rounds}."""

            _, crit_result = await self._get_router().execute_with_routing(
                task=crit_prompt, context={"requires_reasoning": True}
            )
            critique = crit_result.get("content", "")

            # Proposer's rebuttal
            rebut_prompt = f"""You are the Proposer. Respond to this critique:

Critique: {critique}

Defend your position, concede valid points, and strengthen your argument.
Topic: {topic}"""

            _, rebut_result = await self._get_router().execute_with_routing(
                task=rebut_prompt, context={"requires_reasoning": True}
            )
            rebuttal = rebut_result.get("content", "")

            # Capture this round's proposition BEFORE updating it for the next round
            round_proposition = proposition
            proposition = rebuttal  # Updated position for next round

            debate_rounds.append(
                DebateRound(
                    round_number=round_num,
                    proposition=round_proposition,
                    critique=critique,
                    rebuttal=rebuttal,
                )
            )

        # Judge delivers verdict
        debate_transcript = "\n\n".join(
            f"--- Round {r.round_number} ---\n"
            f"Proposition: {r.proposition[:800]}\n"
            f"Critique: {r.critique[:600]}\n"
            f"Rebuttal: {r.rebuttal[:600]}"
            for r in debate_rounds
        )

        judge_prompt = f"""You are an impartial Judge.

Topic: {topic}

Debate transcript:
{debate_transcript}

Deliver a final verdict:
1. Which arguments were strongest?
2. What was conceded vs. maintained?
3. What is the best, most defensible answer?

Respond in JSON:
{{
    "verdict": "<comprehensive conclusion>",
    "confidence": 0.88,
    "key_insights": ["insight 1", "insight 2"]
}}"""

        _, judge_result = await self._get_router().execute_with_routing(
            task=judge_prompt, context={"requires_reasoning": True}
        )

        judge_content = judge_result.get("content", "")
        parsed = self._parse_json(judge_content)

        if parsed:
            verdict = parsed.get("verdict", judge_content)
            confidence = float(parsed.get("confidence", 0.7))
        else:
            verdict = judge_content
            confidence = 0.7

        return DebateResult(
            topic=topic,
            rounds=debate_rounds,
            final_verdict=verdict,
            confidence=confidence,
            cost=total_cost,
        )

    def _parse_json(self, content: str) -> Optional[dict]:
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


# ============================================================
# 7. Constitutional Reviewer
# ============================================================


class ConstitutionalReviewer:
    """
    Karpathy insight (from Constitutional AI discussions):
    "Have the model critique its own outputs against a set of principles
    and revise until all principles are satisfied. This is surprisingly
    effective at removing harmful, biased, or incorrect content."

    Checks outputs against a configurable principle set and auto-revises.
    """

    DEFAULT_PRINCIPLES = [
        "The response is accurate and does not contain false claims.",
        "The response is helpful and directly addresses the user's request.",
        "The response does not contain harmful, biased, or offensive content.",
        "The response does not reveal sensitive personal information.",
        "The response is clear, concise, and well-structured.",
        "The response acknowledges uncertainty when applicable.",
    ]

    def __init__(self, principles: Optional[list[str]] = None):
        self.principles = principles or self.DEFAULT_PRINCIPLES
        self._router = None

    def _get_router(self):
        if self._router is None:
            from router import router

            self._router = router
        return self._router

    def add_principle(self, principle: str):
        """Add a custom principle to the reviewer's constitution."""
        if principle not in self.principles:
            self.principles.append(principle)
            logger.info(f"Added constitutional principle: {principle[:60]}")

    async def review(
        self,
        output: str,
        original_query: str,
        max_revisions: int = 2,
        custom_principles: Optional[list[str]] = None,
    ) -> ConstitutionalResult:
        """
        Review output against the constitution and revise if needed.

        Args:
            output: The LLM output to review
            original_query: The original user query
            max_revisions: Maximum revision cycles
            custom_principles: Override default principles for this call

        Returns:
            ConstitutionalResult with checks and (possibly revised) final output
        """
        active_principles = custom_principles or self.principles
        current_output = output
        all_checks: list[ConstitutionalCheck] = []
        revision_count = 0
        total_cost = 0.0

        for _revision in range(max_revisions + 1):
            # Check each principle
            check_prompt = f"""\
You are a constitutional reviewer. \
Check this response against each principle.

Original query: {original_query}

Response to review:
{current_output}

Principles to check:
{json.dumps(active_principles, indent=2)}

For each principle, indicate if it's satisfied and suggest a revision if not.

Respond in JSON:
{{
    "checks": [
        {{
            "principle": "...",
            "passed": true,
            "violation": "",
            "suggested_revision": ""
        }}
    ],
    "all_passed": true
}}"""

            _, check_result = await self._get_router().execute_with_routing(
                task=check_prompt, context={"requires_reasoning": True}
            )

            content = check_result.get("content", "")
            parsed = self._parse_json(content)

            cycle_checks: list[ConstitutionalCheck] = []
            all_passed = True

            if parsed:
                for check_data in parsed.get("checks", []):
                    passed = bool(check_data.get("passed", True))
                    if not passed:
                        all_passed = False
                    cycle_checks.append(
                        ConstitutionalCheck(
                            principle=check_data.get("principle", ""),
                            passed=passed,
                            violation_description=check_data.get("violation", ""),
                            revised_output=check_data.get("suggested_revision", ""),
                        )
                    )
                all_passed = parsed.get("all_passed", all_passed)
            else:
                # Assume passed if we can't parse
                for p in active_principles:
                    cycle_checks.append(ConstitutionalCheck(principle=p, passed=True))

            all_checks.extend(cycle_checks)

            if all_passed or revision_count >= max_revisions:
                break

            # Revise the output
            failures = [c for c in cycle_checks if not c.passed]
            violations = json.dumps(
                [
                    {"principle": c.principle, "violation": c.violation_description}
                    for c in failures
                ],
                indent=2,
            )
            revise_prompt = f"""Revise this response to comply with these principles:

Original query: {original_query}

Current response:
{current_output}

Violations to fix:
{violations}

Produce an improved response that satisfies all principles while remaining helpful."""

            _, revise_result = await self._get_router().execute_with_routing(
                task=revise_prompt, context={"requires_reasoning": True}
            )
            current_output = revise_result.get("content", current_output)
            revision_count += 1

        final_all_passed = all(c.passed for c in all_checks)

        return ConstitutionalResult(
            original_output=output,
            final_output=current_output,
            checks=all_checks,
            revision_count=revision_count,
            all_passed=final_all_passed,
            cost=total_cost,
        )

    def _parse_json(self, content: str) -> Optional[dict]:
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


# ============================================================
# 8. Unified KarpathyEngine
# ============================================================


class KarpathyEngine:
    """
    Unified interface for all Karpathy LLM methods.

    Provides high-level methods that automatically select and compose
    the right techniques for the given task, following Karpathy's
    guidelines on when to apply each method.

    Quick reference:
        engine.auto()           – Pick the best method automatically
        engine.scratchpad()     – Force deliberate thinking first
        engine.best_of_n()      – Sample N, pick best
        engine.debate()         – Self-play debate for tough questions
        engine.constitutional() – Apply constitutional review
        engine.few_shot()       – Inject few-shot examples
        engine.prm()            – Score reasoning steps
        engine.temperature()    – Get calibrated temperature
    """

    def __init__(self):
        self.temperature_calibrator = TemperatureCalibrator()
        self.scratchpad_reasoner = ScratchpadReasoner()
        self.best_of_n_sampler = BestOfNSampler()
        self.few_shot_library = FewShotLibrary()
        self.process_reward_model = ProcessRewardModel()
        self.self_play_debate = SelfPlayDebate()
        self.constitutional_reviewer = ConstitutionalReviewer()

    # ----- Convenience properties -----

    @property
    def temperature(self) -> TemperatureCalibrator:
        return self.temperature_calibrator

    @property
    def few_shot(self) -> FewShotLibrary:
        return self.few_shot_library

    @property
    def prm(self) -> ProcessRewardModel:
        return self.process_reward_model

    # ----- High-level API -----

    async def auto(
        self, query: str, context: Optional[dict] = None, quality_mode: bool = False
    ) -> dict[str, Any]:
        """
        Automatically select the best Karpathy technique for the task.

        Heuristics:
        - Ambiguous / hard questions → scratchpad reasoning
        - Quality mode or cost-insensitive → best-of-N
        - Controversial or high-stakes → debate
        - Full/high-quality pipeline → constitutional review before returning

        Args:
            query: The task
            context: Optional context
            quality_mode: Use higher-quality (more expensive) pipeline

        Returns:
            Dict with answer and metadata
        """
        nature = self.temperature_calibrator.classify_task(query)
        total_cost = 0.0
        method_used = "scratchpad"

        if quality_mode:
            # Full pipeline: scratchpad → best-of-N → constitutional review
            method_used = "full_pipeline"

            # Scratchpad reasoning
            scratch = await self.scratchpad_reasoner.think(query, context)
            total_cost += scratch.cost

            # Enhance with few-shot context
            few_shot_block = self.few_shot_library.build_few_shot_block(query, k=2)
            enhanced_query = f"{few_shot_block}\n\n{query}" if few_shot_block else query

            # Best-of-N sampling
            bon = await self.best_of_n_sampler.sample(enhanced_query, n=3, context=context)
            total_cost += bon.cost
            raw_answer = bon.best_draft.content

            # Constitutional review
            cr = await self.constitutional_reviewer.review(output=raw_answer, original_query=query)
            total_cost += cr.cost
            final_answer = cr.final_output

            return {
                "answer": final_answer,
                "method": method_used,
                "scratchpad": scratch.scratchpad,
                "bon_score": bon.best_draft.score,
                "constitutional_passed": cr.all_passed,
                "revisions": cr.revision_count,
                "confidence": scratch.confidence,
                "cost": total_cost,
                "nature": nature.value,
            }

        elif nature in (TaskNature.CREATIVE, TaskNature.EXPLORATORY):
            # Debate for exploratory topics
            method_used = "debate"
            debate = await self.self_play_debate.debate(query, context=context)
            total_cost += debate.cost
            return {
                "answer": debate.final_verdict,
                "method": method_used,
                "confidence": debate.confidence,
                "debate_rounds": len(debate.rounds),
                "cost": total_cost,
                "nature": nature.value,
            }

        else:
            # Default: scratchpad + constitutional
            method_used = "scratchpad_constitutional"
            scratch = await self.scratchpad_reasoner.think(query, context)
            total_cost += scratch.cost

            cr = await self.constitutional_reviewer.review(
                output=scratch.final_answer, original_query=query, max_revisions=1
            )
            total_cost += cr.cost

            return {
                "answer": cr.final_output,
                "method": method_used,
                "scratchpad": scratch.scratchpad,
                "constitutional_passed": cr.all_passed,
                "confidence": scratch.confidence,
                "cost": total_cost,
                "nature": nature.value,
            }

    async def scratchpad(self, query: str, context: Optional[dict] = None) -> ScratchpadResult:
        """Run scratchpad reasoning on a query."""
        return await self.scratchpad_reasoner.think(query, context)

    async def best_of_n(
        self, query: str, n: int = 3, context: Optional[dict] = None
    ) -> BestOfNResult:
        """Generate n drafts and return the best-scoring one."""
        return await self.best_of_n_sampler.sample(query, n=n, context=context)

    async def debate(
        self, topic: str, rounds: int = 2, context: Optional[dict] = None
    ) -> DebateResult:
        """Run a self-play debate on a topic."""
        return await self.self_play_debate.debate(topic, rounds=rounds, context=context)

    async def constitutional(
        self, output: str, query: str, principles: Optional[list[str]] = None
    ) -> ConstitutionalResult:
        """Apply constitutional review to an output."""
        return await self.constitutional_reviewer.review(
            output=output, original_query=query, custom_principles=principles
        )

    async def verify_reasoning(self, query: str, steps: list[str]) -> PRMResult:
        """Score reasoning steps using the process reward model."""
        return await self.process_reward_model.score_steps(query, steps)

    def augment_with_examples(self, query: str, task_type: Optional[str] = None, k: int = 3) -> str:
        """
        Return a query augmented with k retrieved few-shot examples.
        Useful for inline prompt enhancement.
        """
        block = self.few_shot_library.build_few_shot_block(query, k=k, task_type=task_type)
        if not block:
            return query
        return f"{block}\n\nNow handle this task:\n{query}"

    def get_capabilities_summary(self) -> dict[str, str]:
        """Return a summary of all available Karpathy methods."""
        return {
            "temperature_calibration": (
                "Auto-tune sampling temperature per task nature. "
                "0 for factual, 0.2 for code, 0.9 for creative."
            ),
            "scratchpad_reasoning": (
                "Private thinking scratchpad before committing to an answer. "
                "Reduces errors on multi-step reasoning tasks."
            ),
            "best_of_n_sampling": (
                "Generate N independent drafts, score each, return the best. "
                "Scales inference compute for quality gains."
            ),
            "few_shot_library": (
                "Curated example bank with vector-similarity retrieval. "
                "Dynamic few-shot injection for any task type."
            ),
            "process_reward_model": (
                "Score each reasoning step independently. "
                "Catches flawed intermediate steps that lead to wrong answers."
            ),
            "self_play_debate": (
                "Two-agent proposition/critique/rebuttal debate. "
                "Judge delivers final verdict. Best for controversial or hard questions."
            ),
            "constitutional_review": (
                "Check output against a configurable principle set. "
                "Auto-revise until all principles are satisfied."
            ),
        }


# ============================================================
# Global instances
# ============================================================

temperature_calibrator = TemperatureCalibrator()
scratchpad_reasoner = ScratchpadReasoner()
best_of_n_sampler = BestOfNSampler()
few_shot_library = FewShotLibrary()
process_reward_model = ProcessRewardModel()
self_play_debate = SelfPlayDebate()
constitutional_reviewer = ConstitutionalReviewer()
karpathy_engine = KarpathyEngine()
