"""
Swarm Intelligence & Agent-to-Agent Protocol - Tier 5 Multi-Agent
Decentralized agent coordination with emergent collective behavior
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

from loguru import logger


class AgentCapability(str, Enum):
    """Capabilities that agents can advertise"""

    REASONING = "reasoning"
    CODING = "coding"
    RESEARCH = "research"
    DATA_ANALYSIS = "data_analysis"
    WRITING = "writing"
    REVIEW = "review"
    PLANNING = "planning"
    EXECUTION = "execution"
    MONITORING = "monitoring"


class MessageType(str, Enum):
    """Types of inter-agent messages"""

    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    CAPABILITY_ANNOUNCEMENT = "capability_announcement"
    STATUS_UPDATE = "status_update"
    KNOWLEDGE_SHARE = "knowledge_share"
    VOTE_REQUEST = "vote_request"
    VOTE_RESPONSE = "vote_response"
    HEARTBEAT = "heartbeat"


@dataclass
class AgentCard:
    """Agent identity and capability card (A2A standard)"""

    agent_id: str
    name: str
    capabilities: list[AgentCapability]
    description: str = ""
    load: float = 0.0  # 0.0 = idle, 1.0 = fully loaded
    status: str = "available"
    metadata: dict[str, Any] = field(default_factory=dict)
    registered_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AgentMessage:
    """Structured inter-agent message (A2A protocol)"""

    message_id: str
    sender_id: str
    recipient_id: Optional[str]  # None = broadcast
    message_type: MessageType
    payload: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    correlation_id: Optional[str] = None  # Links related messages
    ttl: int = 300  # Time-to-live in seconds


@dataclass
class SwarmTask:
    """A task distributed across the swarm"""

    task_id: str
    description: str
    required_capabilities: list[AgentCapability]
    assigned_agents: list[str] = field(default_factory=list)
    results: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, in_progress, voting, completed, failed
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None


class AgentToAgentProtocol:
    """
    Structured inter-agent messaging via the A2A standard.

    Agents advertise capabilities, negotiate tasks, and exchange results
    without manual integration glue code.
    """

    MAX_QUEUE_SIZE = 10000

    def __init__(self):
        self.agents: dict[str, AgentCard] = {}
        self.message_queue: list[AgentMessage] = []
        self.message_handlers: dict[MessageType, list[Callable]] = {mt: [] for mt in MessageType}

    def register_agent(self, card: AgentCard):
        """Register an agent in the directory"""
        self.agents[card.agent_id] = card
        logger.info(f"Agent registered: {card.name} ({card.agent_id})")

        # Broadcast capability announcement
        self.send_message(
            AgentMessage(
                message_id=str(uuid.uuid4()),
                sender_id=card.agent_id,
                recipient_id=None,  # broadcast
                message_type=MessageType.CAPABILITY_ANNOUNCEMENT,
                payload={
                    "agent_id": card.agent_id,
                    "name": card.name,
                    "capabilities": [c.value for c in card.capabilities],
                },
            )
        )

    def unregister_agent(self, agent_id: str):
        """Remove an agent from the directory"""
        self.agents.pop(agent_id, None)
        logger.info(f"Agent unregistered: {agent_id}")

    def discover_agents(
        self, capability: Optional[AgentCapability] = None, status: str = "available"
    ) -> list[AgentCard]:
        """
        Discover available agents, optionally filtered by capability.

        Args:
            capability: Required capability
            status: Required status

        Returns:
            List of matching agent cards
        """
        agents = list(self.agents.values())

        if capability:
            agents = [a for a in agents if capability in a.capabilities]

        if status:
            agents = [a for a in agents if a.status == status]

        # Sort by load (prefer less loaded agents)
        agents.sort(key=lambda a: a.load)

        return agents

    def send_message(self, message: AgentMessage):
        """Send a message to the message queue"""
        # Prune expired messages periodically
        self._prune_expired()

        self.message_queue.append(message)

        # Cap queue length
        if len(self.message_queue) > self.MAX_QUEUE_SIZE:
            before_cap = len(self.message_queue)
            self.message_queue = self.message_queue[-self.MAX_QUEUE_SIZE :]
            logger.debug(
                f"Message queue capped: removed "
                f"{before_cap - len(self.message_queue)}"
                " oldest messages"
            )

        # Trigger handlers
        for handler in self.message_handlers.get(message.message_type, []):
            try:
                handler(message)
            except Exception as e:
                logger.error(f"Message handler error: {e}")

    def _prune_expired(self):
        """Remove messages that have exceeded their TTL"""
        now = datetime.now()
        before = len(self.message_queue)
        self.message_queue = [
            m
            for m in self.message_queue
            if (now - datetime.fromisoformat(m.timestamp)).total_seconds() < m.ttl
        ]
        pruned = before - len(self.message_queue)
        if pruned:
            logger.debug(f"Pruned {pruned} expired messages from queue")

    def on_message(self, message_type: MessageType, handler: Callable):
        """Register a message handler"""
        self.message_handlers[message_type].append(handler)

    def get_messages(
        self,
        recipient_id: Optional[str] = None,
        message_type: Optional[MessageType] = None,
        since: Optional[str] = None,
    ) -> list[AgentMessage]:
        """Get messages from the queue with optional filters"""
        messages = self.message_queue

        if recipient_id:
            messages = [
                m for m in messages if m.recipient_id == recipient_id or m.recipient_id is None
            ]

        if message_type:
            messages = [m for m in messages if m.message_type == message_type]

        if since:
            messages = [m for m in messages if m.timestamp > since]

        return messages

    def negotiate_task(
        self, task_description: str, required_capabilities: list[AgentCapability]
    ) -> Optional[AgentCard]:
        """
        Negotiate task assignment based on capabilities and load.

        Uses auction-based allocation: finds the best-fit, least-loaded agent.
        """
        candidates = []
        for cap in required_capabilities:
            candidates.extend(self.discover_agents(capability=cap))

        if not candidates:
            return None

        # Score candidates by capability match and load
        scored = []
        for agent in candidates:
            capability_match = len(set(required_capabilities) & set(agent.capabilities)) / len(
                required_capabilities
            )
            load_score = 1.0 - agent.load
            score = capability_match * 0.6 + load_score * 0.4
            scored.append((agent, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[0][0] if scored else None


class SwarmIntelligence:
    """
    Deploys a decentralized cluster of agents operating on local rules,
    producing emergent collective behavior.

    Features:
    - Decentralized task distribution
    - Consensus voting for decisions
    - Load-aware allocation
    - Emergent problem solving
    - Fault tolerance via redundancy
    """

    MAX_RESPONSE_PREVIEW_LENGTH = 500

    def __init__(self):
        self.protocol = AgentToAgentProtocol()
        self.active_tasks: dict[str, SwarmTask] = {}
        self._router = None

    def _get_router(self):
        """Lazy-load router"""
        if self._router is None:
            from router import router

            self._router = router
        return self._router

    def initialize_swarm(self, agent_configs: Optional[list[dict]] = None):
        """
        Initialize the swarm with a set of specialized agents.

        Args:
            agent_configs: Optional list of agent configurations
        """
        default_agents = [
            AgentCard(
                agent_id="researcher_1",
                name="Researcher Alpha",
                capabilities=[AgentCapability.RESEARCH, AgentCapability.DATA_ANALYSIS],
                description="Deep research and fact-checking specialist",
            ),
            AgentCard(
                agent_id="coder_1",
                name="Coder Prime",
                capabilities=[AgentCapability.CODING, AgentCapability.REVIEW],
                description="Software development and code review specialist",
            ),
            AgentCard(
                agent_id="analyst_1",
                name="Analyst One",
                capabilities=[AgentCapability.DATA_ANALYSIS, AgentCapability.REASONING],
                description="Data analysis and reasoning specialist",
            ),
            AgentCard(
                agent_id="writer_1",
                name="Writer Echo",
                capabilities=[AgentCapability.WRITING, AgentCapability.REVIEW],
                description="Content creation and editing specialist",
            ),
            AgentCard(
                agent_id="planner_1",
                name="Planner Core",
                capabilities=[AgentCapability.PLANNING, AgentCapability.REASONING],
                description="Strategic planning and coordination specialist",
            ),
            AgentCard(
                agent_id="executor_1",
                name="Executor Delta",
                capabilities=[AgentCapability.EXECUTION, AgentCapability.MONITORING],
                description="Task execution and monitoring specialist",
            ),
        ]

        agents = default_agents
        if agent_configs:
            parsed_agents = []
            for cfg in agent_configs:
                caps = []
                for c in cfg.get("capabilities", []):
                    try:
                        caps.append(AgentCapability(c))
                    except ValueError:
                        logger.warning(f"Skipping unknown capability: {c!r}")
                parsed_agents.append(
                    AgentCard(
                        agent_id=cfg.get("id", str(uuid.uuid4())),
                        name=cfg.get("name", "Agent"),
                        capabilities=caps,
                        description=cfg.get("description", ""),
                    )
                )
            agents = parsed_agents

        for agent in agents:
            self.protocol.register_agent(agent)

        logger.info(f"Swarm initialized with {len(agents)} agents")

    async def distribute_task(
        self,
        task_description: str,
        required_capabilities: Optional[list[AgentCapability]] = None,
        redundancy: int = 1,
        require_consensus: bool = False,
    ) -> SwarmTask:
        """
        Distribute a task across the swarm.

        Args:
            task_description: What needs to be done
            required_capabilities: Required agent capabilities
            redundancy: Number of agents to assign (for fault tolerance)
            require_consensus: Whether agents must agree on the result

        Returns:
            SwarmTask with results
        """
        task = SwarmTask(
            task_id=str(uuid.uuid4()),
            description=task_description,
            required_capabilities=required_capabilities or [AgentCapability.REASONING],
        )

        self.active_tasks[task.task_id] = task

        # Find suitable agents
        candidates = []
        for cap in task.required_capabilities:
            candidates.extend(self.protocol.discover_agents(capability=cap))

        # Deduplicate
        seen_ids = set()
        unique_candidates = []
        for agent in candidates:
            if agent.agent_id not in seen_ids:
                seen_ids.add(agent.agent_id)
                unique_candidates.append(agent)

        if not unique_candidates:
            task.status = "failed"
            logger.warning(f"No agents available for task: {task_description[:80]}")
            return task

        # Assign agents (up to redundancy count)
        assigned = unique_candidates[:redundancy]
        task.assigned_agents = [a.agent_id for a in assigned]
        task.status = "in_progress"

        # Execute task on each assigned agent
        agent_tasks = [self._execute_on_agent(agent, task_description) for agent in assigned]

        results = await asyncio.gather(*agent_tasks, return_exceptions=True)

        # Collect results
        for agent, result in zip(assigned, results):
            if isinstance(result, Exception):
                task.results[agent.agent_id] = {"error": str(result)}
            else:
                task.results[agent.agent_id] = result

        # If consensus required, vote on results
        if require_consensus and len(task.results) > 1:
            task.status = "voting"
            consensus = await self._reach_consensus(task)
            task.results["_consensus"] = consensus

        task.status = "completed"
        task.completed_at = datetime.now().isoformat()

        ok = [r for aid, r in task.results.items() if not aid.startswith("_") and "error" not in r]
        logger.info(
            f"Swarm task completed: {task.task_id} "
            f"({len(task.assigned_agents)} agents, "
            f"{len(ok)} succeeded)"
        )

        return task

    async def _execute_on_agent(self, agent: AgentCard, task: str) -> dict:
        """Execute a task using a specific agent's specialization"""
        # Update agent load
        agent.load = min(1.0, agent.load + 0.3)
        agent.status = "busy"

        try:
            # Build specialized prompt based on agent capabilities
            capability_str = ", ".join(c.value for c in agent.capabilities)
            prompt = f"""You are {agent.name}, a specialist in {capability_str}.
{agent.description}

Task: {task}

Provide your expert analysis and response based on your specialization."""

            decision, result = await self._get_router().execute_with_routing(
                task=prompt, context={"sub_agent": True, "agent_id": agent.agent_id}
            )

            return {
                "agent_id": agent.agent_id,
                "agent_name": agent.name,
                "content": result.get("content", ""),
                "model": decision.model,
                "cost": decision.estimated_cost,
            }

        finally:
            # Release agent load
            agent.load = max(0.0, agent.load - 0.3)
            agent.status = "available"

    async def _reach_consensus(self, task: SwarmTask) -> dict:
        """
        Have agents vote on the best result.

        Uses majority voting and quality scoring.
        """
        valid_results = {
            aid: r
            for aid, r in task.results.items()
            if not aid.startswith("_") and "error" not in r
        }

        if len(valid_results) <= 1:
            return {
                "method": "single_result",
                "result": list(valid_results.values())[0] if valid_results else {},
            }

        # Use an architect agent to evaluate and pick the best
        results_summary = json.dumps(
            [
                {
                    "agent": r.get("agent_name", aid),
                    "response": r.get("content", "")[: self.MAX_RESPONSE_PREVIEW_LENGTH],
                }
                for aid, r in valid_results.items()
            ],
            indent=2,
        )

        consensus_prompt = f"""\
Multiple agents have responded to the same task. \
Evaluate their responses and determine the best answer.

Task: {task.description}

Agent Responses:
{results_summary}

Evaluate based on:
1. Accuracy and correctness
2. Completeness
3. Quality of reasoning

Respond in JSON:
{{
    "best_agent": "agent_name",
    "consensus_answer": "The synthesized best answer...",
    "confidence": 0.9,
    "reasoning": "Why this answer is best..."
}}"""

        decision, result = await self._get_router().execute_with_routing(
            task=consensus_prompt, context={"requires_reasoning": True}
        )

        content = result.get("content", "")
        try:
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
        except json.JSONDecodeError:
            pass

        return {"method": "evaluation", "consensus_answer": content, "confidence": 0.6}

    async def collective_solve(
        self, problem: str, approach: str = "divide_and_conquer", max_agents: int = 4
    ) -> dict[str, Any]:
        """
        Solve a problem using collective swarm intelligence.

        Approaches:
        - divide_and_conquer: Break problem into sub-tasks for different specialists
        - redundant_voting: Have multiple agents solve independently, then vote
        - pipeline: Chain agents in a sequential pipeline

        Args:
            problem: The problem to solve
            approach: Solving approach
            max_agents: Maximum agents to deploy

        Returns:
            Collective solution
        """
        if approach == "divide_and_conquer":
            return await self._divide_and_conquer(problem, max_agents)
        elif approach == "redundant_voting":
            return await self._redundant_voting(problem, max_agents)
        elif approach == "pipeline":
            return await self._pipeline_solve(problem, max_agents)
        else:
            return await self._divide_and_conquer(problem, max_agents)

    async def _divide_and_conquer(self, problem: str, max_agents: int) -> dict:
        """Break problem into sub-tasks for different specialists"""
        # Use planner to decompose
        plan_task = await self.distribute_task(
            f"Break this problem into {max_agents} independent sub-tasks: {problem}",
            required_capabilities=[AgentCapability.PLANNING],
            redundancy=1,
        )

        plan_result = list(plan_task.results.values())[0] if plan_task.results else {}
        plan_content = plan_result.get("content", problem)

        # Execute sub-tasks in parallel
        sub_tasks = [
            self.distribute_task(
                f"Sub-task from: {problem}\n\nYour part: {plan_content[:500]}", redundancy=1
            )
            for _ in range(min(max_agents, len(self.protocol.agents)))
        ]

        results = await asyncio.gather(*sub_tasks, return_exceptions=True)

        # Synthesize results
        all_results = []
        for r in results:
            if isinstance(r, SwarmTask) and r.results:
                for agent_result in r.results.values():
                    if isinstance(agent_result, dict) and "content" in agent_result:
                        all_results.append(agent_result["content"])

        return {
            "approach": "divide_and_conquer",
            "agents_used": max_agents,
            "sub_results": all_results,
            "synthesis": "\n\n---\n\n".join(all_results[:max_agents]),
        }

    async def _redundant_voting(self, problem: str, max_agents: int) -> dict:
        """Have multiple agents solve independently, then vote"""
        task = await self.distribute_task(
            problem,
            required_capabilities=[AgentCapability.REASONING],
            redundancy=min(max_agents, 3),
            require_consensus=True,
        )

        return {
            "approach": "redundant_voting",
            "agents_used": len(task.assigned_agents),
            "results": task.results,
            "consensus": task.results.get("_consensus", {}),
        }

    async def _pipeline_solve(self, problem: str, max_agents: int) -> dict:
        """Chain agents in a sequential pipeline: Research → Analyze → Write → Review"""
        pipeline = [
            (AgentCapability.RESEARCH, "Research this problem thoroughly"),
            (AgentCapability.DATA_ANALYSIS, "Analyze the research findings"),
            (AgentCapability.WRITING, "Write a comprehensive solution"),
            (AgentCapability.REVIEW, "Review and refine the solution"),
        ]

        context = problem
        pipeline_results = []

        for cap, instruction in pipeline[:max_agents]:
            task = await self.distribute_task(
                f"{instruction}:\n\n{context}", required_capabilities=[cap], redundancy=1
            )

            result = list(task.results.values())[0] if task.results else {}
            content = result.get("content", "")
            pipeline_results.append(
                {"stage": cap.value, "instruction": instruction, "result": content[:1000]}
            )

            # Feed result to next stage
            context = (
                f"Previous stage ({cap.value}) output:\n{content}\n\nOriginal problem: {problem}"
            )

        return {
            "approach": "pipeline",
            "stages": len(pipeline_results),
            "pipeline_results": pipeline_results,
            "final_output": pipeline_results[-1]["result"] if pipeline_results else "",
        }

    def get_swarm_status(self) -> dict[str, Any]:
        """Get current swarm status"""
        return {
            "agents": {
                aid: {
                    "name": a.name,
                    "capabilities": [c.value for c in a.capabilities],
                    "load": a.load,
                    "status": a.status,
                }
                for aid, a in self.protocol.agents.items()
            },
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(
                [t for t in self.active_tasks.values() if t.status == "completed"]
            ),
            "message_queue_size": len(self.protocol.message_queue),
        }


# Global instances
swarm = SwarmIntelligence()
a2a_protocol = swarm.protocol
