"""
Sub-Agent Spawning System
Enables main agent to spawn specialized sub-agents for complex multi-step workflows
"""
import asyncio
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from loguru import logger
from router import router, AgentRole
from memory import memory

class SubAgentStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class SubAgentTask:
    """A task assigned to a sub-agent"""
    id: str
    description: str
    role: AgentRole
    parent_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict] = None
    status: SubAgentStatus = SubAgentStatus.CREATED
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    cost: float = 0.0
    error: Optional[str] = None

@dataclass
class WorkflowPlan:
    """A plan decomposed into sub-agent tasks"""
    id: str
    description: str
    tasks: List[SubAgentTask]
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    total_cost: float = 0.0

class SubAgentOrchestrator:
    """
    Orchestrates multiple sub-agents working on complex tasks

    Workflow:
    1. Main Agent receives complex task
    2. Architect decomposes into sub-tasks
    3. Spawn specialized sub-agents for each sub-task
    4. Coordinate execution with dependency management
    5. Aggregate results
    6. Main Agent reviews and delivers final output
    """

    def __init__(self):
        self.active_workflows: Dict[str, WorkflowPlan] = {}
        self.active_agents: Dict[str, SubAgentTask] = {}

    async def decompose_task(
        self,
        task: str,
        context: Optional[Dict] = None
    ) -> WorkflowPlan:
        """
        Use Architect to decompose complex task into sub-tasks

        Returns:
            WorkflowPlan with sub-agent tasks
        """
        logger.info(f"Decomposing task: {task[:100]}...")

        # Use Architect role for decomposition
        decomposition_prompt = f"""You are the Architect. Decompose this complex task into specialized sub-tasks for different sub-agents.

Task: {task}

Available sub-agent roles:
- Researcher: Deep analysis, fact-checking, information gathering
- Coder: Software development, debugging, implementation
- Worker: Data processing, summarization, formatting
- Architect: Planning, strategy, evaluation (can be used for final review)

Provide a JSON workflow plan with:
1. List of sub-tasks
2. Which role should handle each
3. Dependencies between tasks (which must complete before others)
4. Expected input/output for each

Format:
{{
  "tasks": [
    {{
      "id": "task_1",
      "description": "...",
      "role": "researcher",
      "dependencies": [],
      "context": {{}}
    }},
    ...
  ]
}}"""

        decision, result = await router.execute_with_routing(
            task=decomposition_prompt,
            context={"requires_reasoning": True}
        )

        # Parse workflow plan
        try:
            import json
            # Extract JSON from response
            content = result.get("content", "")

            # Simple JSON extraction (could be more robust)
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                plan_data = json.loads(content[start:end])
            else:
                raise ValueError("No valid JSON found in response")

            # Create workflow plan
            workflow_id = str(uuid.uuid4())
            tasks = []

            for task_data in plan_data.get("tasks", []):
                task_obj = SubAgentTask(
                    id=task_data.get("id", f"task_{len(tasks)}"),
                    description=task_data["description"],
                    role=AgentRole(task_data.get("role", "researcher")),
                    dependencies=task_data.get("dependencies", []),
                    context=task_data.get("context", {})
                )
                tasks.append(task_obj)

            workflow = WorkflowPlan(
                id=workflow_id,
                description=task,
                tasks=tasks
            )

            self.active_workflows[workflow_id] = workflow
            logger.info(f"Created workflow with {len(tasks)} sub-tasks")

            return workflow

        except Exception as e:
            logger.error(f"Failed to decompose task: {e}")
            # Fallback: create simple single-task workflow
            workflow_id = str(uuid.uuid4())
            workflow = WorkflowPlan(
                id=workflow_id,
                description=task,
                tasks=[
                    SubAgentTask(
                        id="task_1",
                        description=task,
                        role=AgentRole.RESEARCHER
                    )
                ]
            )
            self.active_workflows[workflow_id] = workflow
            return workflow

    async def execute_workflow(
        self,
        workflow: WorkflowPlan,
        parallel: bool = True
    ) -> WorkflowPlan:
        """
        Execute workflow by spawning and coordinating sub-agents

        Args:
            workflow: The workflow plan to execute
            parallel: Execute independent tasks in parallel

        Returns:
            Completed workflow with results
        """
        logger.info(f"Executing workflow: {workflow.description[:100]}...")

        start_time = datetime.now()

        # Build dependency graph
        task_map = {t.id: t for t in workflow.tasks}
        completed = set()
        total_cost = 0.0

        while len(completed) < len(workflow.tasks):
            # Find tasks that can run now (all dependencies met)
            ready_tasks = [
                t for t in workflow.tasks
                if t.id not in completed
                and all(dep in completed for dep in t.dependencies)
                and t.status == SubAgentStatus.CREATED
            ]

            if not ready_tasks:
                # Check if we're stuck
                remaining = [t for t in workflow.tasks if t.id not in completed]
                if remaining:
                    logger.error(f"Workflow stuck! {len(remaining)} tasks remaining with unmet dependencies")
                    for task in remaining:
                        task.status = SubAgentStatus.FAILED
                        task.error = "Dependency deadlock"
                break

            # Execute ready tasks
            if parallel and len(ready_tasks) > 1:
                # Execute in parallel
                results = await asyncio.gather(
                    *[self._execute_sub_agent(t, task_map) for t in ready_tasks],
                    return_exceptions=True
                )

                for task, result in zip(ready_tasks, results):
                    if isinstance(result, Exception):
                        task.status = SubAgentStatus.FAILED
                        task.error = str(result)
                    else:
                        completed.add(task.id)
                        total_cost += task.cost
            else:
                # Execute sequentially
                for task in ready_tasks:
                    try:
                        await self._execute_sub_agent(task, task_map)
                        completed.add(task.id)
                        total_cost += task.cost
                    except Exception as e:
                        task.status = SubAgentStatus.FAILED
                        task.error = str(e)
                        logger.error(f"Sub-agent task failed: {e}")

        # Mark workflow complete
        workflow.completed_at = datetime.now()
        workflow.total_cost = total_cost

        duration = (workflow.completed_at - start_time).total_seconds()
        logger.info(
            f"Workflow complete: {len(completed)}/{len(workflow.tasks)} tasks "
            f"in {duration:.1f}s (${total_cost:.4f})"
        )

        # Store workflow results
        memory.log_task(
            task=workflow.description,
            domain="multi_agent",
            status="completed" if len(completed) == len(workflow.tasks) else "partial",
            result={
                "workflow_id": workflow.id,
                "tasks_completed": len(completed),
                "total_tasks": len(workflow.tasks),
                "results": [t.result for t in workflow.tasks if t.result]
            },
            cost=total_cost,
            duration=duration
        )

        return workflow

    async def _execute_sub_agent(self, task: SubAgentTask, task_map: Optional[Dict] = None) -> SubAgentTask:
        """Execute a single sub-agent task"""
        logger.info(f"Spawning sub-agent for: {task.description[:80]}...")

        task.status = SubAgentStatus.RUNNING
        self.active_agents[task.id] = task

        try:
            # Build task prompt with context from dependencies
            full_context = task.context.copy()

            # Add results from dependency tasks using the persistent task_map
            if task.dependencies and task_map:
                for dep_id in task.dependencies:
                    dep_task = task_map.get(dep_id)
                    if dep_task and dep_task.result:
                        full_context[f"dependency_{dep_id}"] = dep_task.result

            # Execute with router using appropriate role
            task_prompt = f"""You are a specialized sub-agent with the role: {task.role.value}

Your task: {task.description}

Context:
{full_context}

Provide a clear, actionable result."""

            decision, result = await router.execute_with_routing(
                task=task_prompt,
                context={"sub_agent": True, "role": task.role.value}
            )

            # Store result
            task.result = {
                "content": result.get("content", ""),
                "role": task.role.value,
                "model": decision.model,
                "cost": decision.estimated_cost
            }
            task.cost = decision.estimated_cost
            task.status = SubAgentStatus.COMPLETED
            task.completed_at = datetime.now()

            logger.info(f"Sub-agent completed: {task.id} (${task.cost:.4f})")

        except Exception as e:
            logger.error(f"Sub-agent execution failed: {e}")
            task.status = SubAgentStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()

        finally:
            # Remove from active agents
            if task.id in self.active_agents:
                del self.active_agents[task.id]

        return task

    async def execute_task_with_sub_agents(
        self,
        task: str,
        context: Optional[Dict] = None,
        parallel: bool = True
    ) -> Dict[str, Any]:
        """
        High-level API: Execute task using sub-agent workflow

        Returns:
            Final aggregated result
        """
        # Decompose into workflow
        workflow = await self.decompose_task(task, context)

        # Execute workflow
        completed_workflow = await self.execute_workflow(workflow, parallel)

        # Aggregate results using Architect
        if len(completed_workflow.tasks) > 1:
            aggregation_prompt = f"""You are the Architect. Review and synthesize results from {len(completed_workflow.tasks)} sub-agents.

Original task: {task}

Sub-agent results:
"""
            for i, t in enumerate(completed_workflow.tasks, 1):
                if t.result:
                    aggregation_prompt += f"\n{i}. {t.role.value}: {t.result['content'][:500]}\n"

            aggregation_prompt += "\nProvide a coherent, final answer that integrates all sub-agent work."

            decision, final_result = await router.execute_with_routing(
                task=aggregation_prompt,
                context={"requires_reasoning": True}
            )

            return {
                "content": final_result.get("content", ""),
                "workflow_id": completed_workflow.id,
                "sub_agents_used": len(completed_workflow.tasks),
                "total_cost": completed_workflow.total_cost + decision.estimated_cost,
                "sub_results": [t.result for t in completed_workflow.tasks if t.result]
            }
        else:
            # Single task, return directly
            task_result = completed_workflow.tasks[0].result
            return {
                "content": task_result.get("content", "") if task_result else "",
                "workflow_id": completed_workflow.id,
                "sub_agents_used": 1,
                "total_cost": completed_workflow.total_cost
            }

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        """Get status of active workflow"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return None

        return {
            "id": workflow.id,
            "description": workflow.description,
            "total_tasks": len(workflow.tasks),
            "completed_tasks": len([t for t in workflow.tasks if t.status == SubAgentStatus.COMPLETED]),
            "failed_tasks": len([t for t in workflow.tasks if t.status == SubAgentStatus.FAILED]),
            "total_cost": workflow.total_cost,
            "tasks": [
                {
                    "id": t.id,
                    "description": t.description,
                    "role": t.role.value,
                    "status": t.status.value,
                    "cost": t.cost
                }
                for t in workflow.tasks
            ]
        }

    # ==========================================================
    # Hierarchical Coordination (Tier 5)
    # ==========================================================

    async def execute_hierarchical(
        self,
        task: str,
        team: Optional[List[Dict]] = None,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Orchestrate entire teams of specialist agents — a Researcher, Analyst,
        Writer, and Reviewer working in concert — with the parent agent managing
        the overall workflow and synthesizing results.

        Args:
            task: The high-level task to accomplish
            team: Optional custom team configuration. Each dict should have
                  'role' (AgentRole value) and optional 'description'.
            context: Additional context for the task

        Returns:
            Synthesized result from the hierarchical team
        """
        # Default team composition
        if team is None:
            team = [
                {"role": "researcher", "description": "Deep research and information gathering"},
                {"role": "worker", "description": "Data analysis and processing"},
                {"role": "coder", "description": "Implementation and technical work"},
                {"role": "architect", "description": "Review, quality assurance, and synthesis"},
            ]

        logger.info(
            f"Starting hierarchical coordination: {task[:80]}... "
            f"({len(team)} specialists)"
        )

        # Phase 1: Architect creates the execution plan
        plan_prompt = f"""You are the Lead Architect orchestrating a team of {len(team)} specialists.

Task: {task}

Team members:
{chr(10).join(f"- {m['role'].title()}: {m.get('description', '')}" for m in team)}

Create a detailed execution plan assigning specific responsibilities to each team member.
Include the order of execution and what each member should focus on.

Format as JSON:
{{
    "plan_summary": "High-level plan description",
    "assignments": [
        {{
            "role": "{team[0]['role']}",
            "task": "Specific task for this team member",
            "priority": 1,
            "depends_on": []
        }}
    ]
}}"""

        decision, plan_result = await router.execute_with_routing(
            task=plan_prompt,
            context={"requires_reasoning": True}
        )

        # Parse plan
        import json
        plan_content = plan_result.get("content", "")
        try:
            start = plan_content.find("{")
            end = plan_content.rfind("}") + 1
            if start >= 0 and end > start:
                plan = json.loads(plan_content[start:end])
            else:
                raise ValueError("No JSON found")
        except (json.JSONDecodeError, ValueError):
            # Fallback: assign task to all team members
            plan = {
                "plan_summary": "Parallel execution by all specialists",
                "assignments": [
                    {"role": m["role"], "task": f"Handle your part of: {task}", "priority": 1, "depends_on": []}
                    for m in team
                ]
            }

        # Phase 2: Execute assignments respecting dependencies
        assignments = plan.get("assignments", [])

        # Build dependency-ordered execution groups
        executed_roles = set()
        all_results = {}
        total_cost = decision.estimated_cost

        # Sort by priority
        assignments.sort(key=lambda a: a.get("priority", 99))
        pending_assignments = list(assignments)

        # Group by dependency level
        while pending_assignments:
            # Find assignments that can run now. Track completion by assignment
            # identity, not by role, so duplicate-role assignments are still run.
            ready = [
                a for a in pending_assignments
                if all(dep in executed_roles for dep in a.get("depends_on", []))
            ]

            if not ready:
                # Break deadlock: run remaining assignments anyway
                ready = list(pending_assignments)

            # Remove selected assignments from the pending queue before execution
            # so each assignment instance is executed exactly once.
            ready_ids = {id(a) for a in ready}
            pending_assignments = [
                a for a in pending_assignments
                if id(a) not in ready_ids
            ]
            # Execute ready assignments in parallel
            async_tasks = []
            for assignment in ready:
                raw_role = assignment.get("role", "")
                normalized_role = raw_role.strip().lower() if isinstance(raw_role, str) else ""
                role = AgentRole._value2member_map_.get(normalized_role)
                if role is None:
                    logger.warning(f"Skipping assignment with invalid role: {raw_role!r}")
                    all_results[str(raw_role)] = {
                        "status": "failed",
                        "error": f"Invalid agent role: {raw_role!r}",
                        "content": ""
                    }
                    executed_roles.add(raw_role)
                    continue
                role_task = assignment.get("task", task)

                # Build context including previous results
                role_context = context.copy() if context else {}
                if all_results:
                    role_context["previous_results"] = {
                        r: res.get("content", "")[:500]
                        for r, res in all_results.items()
                    }

                role_prompt = f"""You are a specialist {role.value} on a coordinated team.

Your assignment: {role_task}

Original team task: {task}

{f"Results from other team members: {json.dumps(role_context.get('previous_results', {}), indent=2)}" if role_context.get('previous_results') else ""}

Provide your specialized contribution."""

                async_tasks.append(
                    router.execute_with_routing(
                        task=role_prompt,
                        context={"sub_agent": True, "role": role.value}
                    )
                )

            results = await asyncio.gather(*async_tasks, return_exceptions=True)

            for assignment, result in zip(ready, results):
                role = assignment["role"]
                if isinstance(result, Exception):
                    all_results[role] = {"content": f"Error: {result}", "error": str(result)}
                    logger.error(f"Specialist {role} failed: {result}")
                else:
                    dec, res = result
                    all_results[role] = res
                    total_cost += dec.estimated_cost

                executed_roles.add(role)

        # Phase 3: Architect synthesizes all results
        synthesis_prompt = f"""You are the Lead Architect. Synthesize the work from your entire team into a cohesive final deliverable.

Original task: {task}

Team contributions:
"""
        for role, result in all_results.items():
            content = result.get("content", "")[:800] if isinstance(result, dict) else str(result)[:800]
            synthesis_prompt += f"\n--- {role.title()} ---\n{content}\n"

        synthesis_prompt += "\nCreate a comprehensive, polished final output that integrates all contributions."

        dec, synthesis = await router.execute_with_routing(
            task=synthesis_prompt,
            context={"requires_reasoning": True}
        )
        total_cost += dec.estimated_cost

        logger.info(
            f"Hierarchical coordination complete: {len(team)} specialists, "
            f"${total_cost:.4f} total cost"
        )

        return {
            "content": synthesis.get("content", ""),
            "plan": plan.get("plan_summary", ""),
            "team_size": len(team),
            "specialist_results": {
                role: result.get("content", "")[:500] if isinstance(result, dict) else str(result)[:500]
                for role, result in all_results.items()
            },
            "total_cost": total_cost,
            "workflow_type": "hierarchical_coordination"
        }

# Global orchestrator instance
orchestrator = SubAgentOrchestrator()
