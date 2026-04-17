"""
Dynamic Skill Acquisition - Tier 6 Self-Improvement
Discover, learn, and activate new capability modules on demand
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from loguru import logger


@dataclass
class SkillDefinition:
    """A learnable skill/capability"""

    skill_id: str
    name: str
    description: str
    category: str
    workflow: list[dict[str, Any]]
    prerequisites: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    version: str = "1.0.0"
    author: str = "system"
    success_rate: float = 0.0
    usage_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_used: Optional[str] = None


@dataclass
class SkillExecutionResult:
    """Result of executing a skill"""

    skill_id: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    duration_seconds: float = 0.0
    cost: float = 0.0


class SkillRegistry:
    """
    Registry and manager for dynamic skills.

    Features:
    - Discover skills from task patterns
    - Learn new skills from successful workflows
    - Execute skills with parameter binding
    - Track skill performance
    - Version and update skills
    """

    def __init__(self):
        self.skills: dict[str, SkillDefinition] = {}
        self._memory = None
        self._router = None
        self._initialize_built_in_skills()

    def _get_memory(self):
        if self._memory is None:
            from memory import memory

            self._memory = memory
        return self._memory

    def _get_router(self):
        if self._router is None:
            from router import router

            self._router = router
        return self._router

    def _initialize_built_in_skills(self):
        """Register built-in skills"""
        built_ins = [
            SkillDefinition(
                skill_id="web_research",
                name="Web Research",
                description="Research a topic using web search and synthesize findings",
                category="research",
                workflow=[
                    {"step": 1, "action": "search", "description": "Search for the topic"},
                    {"step": 2, "action": "analyze", "description": "Analyze search results"},
                    {"step": 3, "action": "synthesize", "description": "Synthesize findings"},
                ],
                tags=["research", "web", "search"],
            ),
            SkillDefinition(
                skill_id="code_review",
                name="Code Review",
                description="Review code for quality, bugs, and improvements",
                category="coding",
                workflow=[
                    {"step": 1, "action": "parse", "description": "Parse and understand the code"},
                    {
                        "step": 2,
                        "action": "analyze",
                        "description": "Check for bugs and anti-patterns",
                    },
                    {
                        "step": 3,
                        "action": "suggest",
                        "description": "Generate improvement suggestions",
                    },
                ],
                tags=["coding", "review", "quality"],
            ),
            SkillDefinition(
                skill_id="data_analysis",
                name="Data Analysis",
                description="Analyze data sets and generate insights",
                category="analytics",
                workflow=[
                    {"step": 1, "action": "load", "description": "Load and inspect data"},
                    {"step": 2, "action": "clean", "description": "Clean and prepare data"},
                    {"step": 3, "action": "analyze", "description": "Run analysis"},
                    {
                        "step": 4,
                        "action": "visualize",
                        "description": "Generate visualizations/reports",
                    },
                ],
                tags=["data", "analysis", "analytics"],
            ),
            SkillDefinition(
                skill_id="document_summary",
                name="Document Summarization",
                description="Summarize documents preserving key information",
                category="writing",
                workflow=[
                    {"step": 1, "action": "extract", "description": "Extract key content"},
                    {"step": 2, "action": "identify", "description": "Identify main themes"},
                    {"step": 3, "action": "summarize", "description": "Generate concise summary"},
                ],
                tags=["writing", "summary", "documents"],
            ),
            SkillDefinition(
                skill_id="task_automation",
                name="Task Automation",
                description="Automate repetitive multi-step tasks",
                category="automation",
                workflow=[
                    {"step": 1, "action": "analyze", "description": "Analyze the task pattern"},
                    {"step": 2, "action": "plan", "description": "Create automation plan"},
                    {"step": 3, "action": "implement", "description": "Implement automation"},
                    {"step": 4, "action": "test", "description": "Test and validate"},
                ],
                tags=["automation", "workflow", "efficiency"],
            ),
        ]

        for skill in built_ins:
            self.skills[skill.skill_id] = skill

    def register_skill(self, skill: SkillDefinition):
        """Register a new skill"""
        self.skills[skill.skill_id] = skill

        # Also persist to memory
        try:
            self._get_memory().save_skill(
                name=skill.name, description=skill.description, workflow=skill.workflow
            )
        except Exception as e:
            logger.warning(f"Failed to persist skill to memory: {e}")

        logger.info(f"Skill registered: {skill.name} ({skill.skill_id})")

    def find_skill(self, query: str) -> Optional[SkillDefinition]:
        """
        Find the best matching skill for a query.

        Args:
            query: Task description to match against skills

        Returns:
            Best matching skill or None
        """
        query_lower = query.lower()

        best_match = None
        best_score = 0.0

        for skill in self.skills.values():
            score = 0.0

            # Check name match
            if skill.name.lower() in query_lower:
                score += 0.5

            # Check tag matches
            for tag in skill.tags:
                if tag in query_lower:
                    score += 0.2

            # Check description match
            desc_words = skill.description.lower().split()
            matching_words = sum(1 for w in desc_words if w in query_lower)
            score += (matching_words / max(len(desc_words), 1)) * 0.3

            # Boost by success rate
            score *= 0.5 + skill.success_rate * 0.5

            if score > best_score:
                best_score = score
                best_match = skill

        return best_match if best_score > 0.2 else None

    def search_skills(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> list[SkillDefinition]:
        """Search skills by query, category, or tags"""
        results = list(self.skills.values())

        if category:
            results = [s for s in results if s.category == category]

        if tags:
            results = [s for s in results if any(t in s.tags for t in tags)]

        if query:
            query_lower = query.lower()
            results = [
                s
                for s in results
                if query_lower in s.name.lower()
                or query_lower in s.description.lower()
                or any(query_lower in t for t in s.tags)
            ]

        return sorted(results, key=lambda s: s.usage_count, reverse=True)

    async def learn_skill_from_task(
        self, task_description: str, successful_workflow: list[dict], category: str = "learned"
    ) -> SkillDefinition:
        """
        Learn a new skill from a successfully completed task workflow.

        Distills the successful workflow into a reusable skill definition.

        Args:
            task_description: What the task accomplished
            successful_workflow: The steps that were taken
            category: Skill category

        Returns:
            The newly created skill
        """
        # Use the router to generate a clean skill definition
        learn_prompt = f"""A task was completed successfully. Create a reusable skill from this workflow.

Task: {task_description}

Workflow steps taken:
{json.dumps(successful_workflow, indent=2)}

Create a generalized, reusable skill definition in JSON:
{{
    "name": "Short skill name",
    "description": "What this skill does, generalized",
    "tags": ["tag1", "tag2"],
    "workflow": [
        {{"step": 1, "action": "action_name", "description": "Generalized step description"}},
        ...
    ]
}}"""

        decision, result = await self._get_router().execute_with_routing(
            task=learn_prompt, context={"requires_reasoning": True}
        )

        content = result.get("content", "")
        parsed = self._parse_json(content)

        if parsed:
            skill = SkillDefinition(
                skill_id=str(uuid.uuid4()),
                name=parsed.get("name", f"Learned: {task_description[:50]}"),
                description=parsed.get("description", task_description),
                category=category,
                workflow=parsed.get("workflow", successful_workflow),
                tags=parsed.get("tags", []),
                author="auto_learned",
            )
        else:
            skill = SkillDefinition(
                skill_id=str(uuid.uuid4()),
                name=f"Learned: {task_description[:50]}",
                description=task_description,
                category=category,
                workflow=successful_workflow,
                author="auto_learned",
            )

        self.register_skill(skill)
        logger.info(f"Learned new skill from task: {skill.name}")

        return skill

    async def execute_skill(
        self, skill_id: str, parameters: Optional[dict] = None
    ) -> SkillExecutionResult:
        """
        Execute a registered skill.

        Args:
            skill_id: Skill to execute
            parameters: Parameters for the skill

        Returns:
            SkillExecutionResult with output
        """
        import time

        start = time.time()

        skill = self.skills.get(skill_id)
        if not skill:
            return SkillExecutionResult(
                skill_id=skill_id, success=False, error=f"Skill not found: {skill_id}"
            )

        try:
            # Build execution prompt from skill workflow
            workflow_str = "\n".join(
                f"  {s['step']}. {s['action']}: {s['description']}" for s in skill.workflow
            )

            exec_prompt = f"""Execute this skill: {skill.name}
Description: {skill.description}

Workflow:
{workflow_str}

{f"Parameters: {json.dumps(parameters)}" if parameters else ""}

Execute each step in order and provide the complete output."""

            decision, result = await self._get_router().execute_with_routing(
                task=exec_prompt, context=parameters or {}
            )

            output = result.get("content", "")
            duration = time.time() - start

            # Update skill metrics
            skill.usage_count += 1
            skill.last_used = datetime.now().isoformat()
            skill.success_rate = (
                skill.success_rate * (skill.usage_count - 1) + 1.0
            ) / skill.usage_count

            # Record in memory
            try:
                self._get_memory().record_skill_result(skill.name, True, duration)
            except Exception:
                pass

            return SkillExecutionResult(
                skill_id=skill_id,
                success=True,
                output=output,
                duration_seconds=duration,
                cost=decision.estimated_cost,
            )

        except Exception as e:
            duration = time.time() - start

            # Update failure metrics
            skill.usage_count += 1
            skill.success_rate = (skill.success_rate * (skill.usage_count - 1)) / skill.usage_count

            try:
                self._get_memory().record_skill_result(skill.name, False, duration)
            except Exception:
                pass

            return SkillExecutionResult(
                skill_id=skill_id, success=False, error=str(e), duration_seconds=duration
            )

    def get_skill_stats(self) -> dict[str, Any]:
        """Get statistics about registered skills"""
        return {
            "total_skills": len(self.skills),
            "by_category": self._group_by(list(self.skills.values()), lambda s: s.category),
            "most_used": sorted(
                [
                    {"name": s.name, "usage": s.usage_count, "success_rate": s.success_rate}
                    for s in self.skills.values()
                ],
                key=lambda x: x["usage"],
                reverse=True,
            )[:10],
            "learned_skills": len([s for s in self.skills.values() if s.author == "auto_learned"]),
        }

    def _group_by(self, items: list, key_fn) -> dict[str, int]:
        """Group items by key function"""
        groups = {}
        for item in items:
            key = key_fn(item)
            groups[key] = groups.get(key, 0) + 1
        return groups

    def _parse_json(self, content: str) -> Optional[dict]:
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


# Global skill registry instance
skill_registry = SkillRegistry()
