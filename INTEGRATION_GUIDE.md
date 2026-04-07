# Big Homie - Integration Guide

This guide explains how to use all the advanced features together in your applications.

---

## 🎯 Quick Integration Examples

### 1. Using MCP Tools

```python
from llm_gateway import llm, TaskType

# Simple tool use
messages = [
    {"role": "user", "content": "Search GitHub for trending Python AI repos"}
]

response = await llm.complete_with_tools(
    messages=messages,
    task_type=TaskType.GENERAL
)

print(response["content"])
```

**What happens:**
1. LLM sees MCP tools available (github_search_repos, browser_navigate, etc.)
2. LLM requests `github_search_repos` tool with query
3. Tool executes and returns results
4. LLM synthesizes final answer

### 2. Using Vector Memory

```python
from vector_memory import vector_memory

# Store conversation for semantic search
vector_memory.add_conversation(
    content="User prefers dark mode in all applications",
    role="user",
    metadata={"category": "preference"}
)

# Later, retrieve relevant context
results = vector_memory.search_conversations(
    query="What UI preferences does the user have?",
    n_results=3
)

for result in results:
    print(result["content"])
```

### 3. Using Browser Automation

```python
from browser_skill import quick_scrape

# Scrape data from a webpage
data = await quick_scrape(
    url="https://news.ycombinator.com",
    selectors={
        "headlines": ".titleline > a",
        "points": ".score"
    }
)

print(data["headlines"])  # List of top stories
```

### 4. Using Sub-Agent Workflows

```python
from sub_agents import orchestrator

# Complex multi-step task
result = await orchestrator.execute_task_with_sub_agents(
    task="""
    Research the top 5 AI coding assistants,
    compare their features,
    and create a markdown report
    """,
    parallel=True  # Execute independent steps in parallel
)

print(result["content"])  # Final synthesized report
print(f"Used {result['sub_agents_used']} sub-agents")
print(f"Cost: ${result['total_cost']:.4f}")
```

### 5. Using Smart Router

```python
from router import router

# Automatic model selection based on task complexity
decision, result = await router.execute_with_routing(
    task="Design a scalable microservices architecture for e-commerce",
    context={"requires_reasoning": True}
)

print(f"Routed to: {decision.role.value}")
print(f"Model: {decision.model}")
print(f"Cost: ${decision.estimated_cost:.4f}")
print(result["content"])
```

---

## 🔧 Advanced Patterns

### Pattern 1: Multi-Turn Tool Use

```python
from llm_gateway import llm, TaskType

async def research_and_summarize(topic: str) -> str:
    """
    Use tools to research a topic and create summary

    Tools used: browser_navigate, github_search_repos, file_write
    """
    messages = [
        {
            "role": "system",
            "content": "You are a research assistant. Use tools to gather data."
        },
        {
            "role": "user",
            "content": f"""
            Research '{topic}' using these steps:
            1. Search GitHub for related repositories
            2. Visit top repo and extract README
            3. Write a summary to 'research_summary.md'

            Use the available tools to complete this task.
            """
        }
    ]

    response = await llm.complete_with_tools(
        messages=messages,
        task_type=TaskType.GENERAL,
        max_tool_rounds=10
    )

    return response["content"]

# Usage
summary = await research_and_summarize("vector databases")
```

### Pattern 2: Thread-Isolated Context

```python
from vector_memory import vector_memory

# Separate contexts for different workstreams
async def coding_session():
    # All coding-related memories go to 'coding' thread
    vector_memory.add_to_thread(
        thread_name="coding",
        content="Implemented OAuth2 authentication in auth.py",
        metadata={"file": "auth.py", "type": "implementation"}
    )

    # Search only within coding context
    related = vector_memory.search_thread(
        thread_name="coding",
        query="authentication implementation",
        n_results=5
    )

    return related

async def research_session():
    # Research memories separate from coding
    vector_memory.add_to_thread(
        thread_name="research",
        content="Claude Opus 4.5 has 200K context window",
        metadata={"source": "anthropic_docs"}
    )

    # Won't see coding memories
    findings = vector_memory.search_thread(
        thread_name="research",
        query="LLM capabilities"
    )

    return findings
```

### Pattern 3: Autonomous Task with Self-Correction

```python
from heartbeat import heartbeat, HeartbeatConfig
from log_review import log_reviewer

# Configure autonomous system
config = HeartbeatConfig(
    enabled=True,
    interval_minutes=30,
    max_autonomous_cost=10.0
)

# Start heartbeat
heartbeat.config = config
heartbeat.start()

# Manually trigger log review
analysis = log_reviewer.perform_daily_review()

print(f"Errors found: {analysis.total_errors}")
print(f"Success rate: {analysis.success_metrics['success_rate']}%")

for suggestion in analysis.improvement_suggestions:
    print(f"- {suggestion}")
```

### Pattern 4: Skill Learning and Reuse

```python
from vector_memory import vector_memory
from memory import memory

# Learn a new skill after successful task
async def learn_skill(name: str, workflow: List[Dict]):
    vector_memory.add_skill(
        name=name,
        description="Successfully implemented feature",
        workflow=workflow,
        success_rate=1.0
    )

    # Also save to traditional memory
    memory.save_skill(
        name=name,
        description="Multi-step workflow",
        workflow=workflow
    )

# Retrieve relevant skills for new task
skills = vector_memory.search_skills(
    query="implement user authentication",
    n_results=3
)

print("Relevant past skills:")
for skill in skills:
    print(f"- {skill['metadata']['name']}: {skill['metadata']['success_rate']}")
```

---

## 🎨 Full Application Example

Here's how to build a complete autonomous research agent:

```python
import asyncio
from router import router
from sub_agents import orchestrator
from vector_memory import vector_memory
from browser_skill import BrowserSkill
from llm_gateway import llm
from mcp_integration import mcp

class ResearchAgent:
    """
    Autonomous research agent that:
    - Accepts research topics
    - Spawns sub-agents for different research angles
    - Uses browser automation to gather data
    - Stores findings in vector memory
    - Generates comprehensive reports
    """

    def __init__(self):
        self.thread_name = "research_agent"

    async def research_topic(self, topic: str) -> Dict:
        """Main research workflow"""

        # 1. Decompose research into sub-tasks
        workflow = await orchestrator.decompose_task(
            task=f"Comprehensive research on: {topic}",
            context={"domain": "research"}
        )

        # 2. Execute sub-agent workflow in parallel
        completed = await orchestrator.execute_workflow(
            workflow=workflow,
            parallel=True
        )

        # 3. Store all findings in vector memory
        for task in completed.tasks:
            if task.result:
                vector_memory.add_to_thread(
                    thread_name=self.thread_name,
                    content=task.result["content"],
                    metadata={
                        "topic": topic,
                        "role": task.role.value,
                        "subtask": task.description
                    }
                )

        # 4. Synthesize final report using ARCHITECT
        all_findings = "\n\n".join([
            t.result["content"]
            for t in completed.tasks
            if t.result
        ])

        decision, final_report = await router.execute_with_routing(
            task=f"""
            Synthesize a comprehensive research report on '{topic}'.

            Sub-agent findings:
            {all_findings}

            Create a well-structured markdown report.
            """,
            context={"requires_reasoning": True}
        )

        # 5. Return results
        return {
            "topic": topic,
            "report": final_report["content"],
            "subtasks_completed": len(completed.tasks),
            "total_cost": completed.total_cost,
            "workflow_id": completed.id
        }

    async def get_past_research(self, query: str) -> List[Dict]:
        """Retrieve past research findings"""
        return vector_memory.search_thread(
            thread_name=self.thread_name,
            query=query,
            n_results=10
        )

# Usage
async def main():
    agent = ResearchAgent()

    # Perform research
    result = await agent.research_topic("Quantum Computing Applications in AI")

    print(f"Report generated!")
    print(f"Cost: ${result['total_cost']:.4f}")
    print(f"Subtasks: {result['subtasks_completed']}")
    print("\n" + result['report'])

    # Later: retrieve relevant past research
    past = await agent.get_past_research("quantum applications")
    print(f"\nFound {len(past)} relevant past research items")

asyncio.run(main())
```

---

## 🔐 Permission & Safety

### Tool Confirmation

Some tools require user confirmation:

```python
from mcp_integration import mcp, ToolDefinition, ToolType

# Register tool that requires confirmation
mcp.register_tool(ToolDefinition(
    name="delete_database",
    type=ToolType.DATABASE,
    description="Delete entire database",
    parameters={"confirm": {"type": "boolean"}},
    handler=my_delete_handler,
    requires_confirmation=True  # <-- Will prompt user
))
```

### Cost Budgets

```python
from heartbeat import heartbeat

# Check if autonomous budget exceeded
if heartbeat.daily_cost >= heartbeat.config.max_autonomous_cost:
    print("Daily budget exceeded, pausing autonomous actions")
    heartbeat.pause()
```

### Quiet Hours

```python
from heartbeat import heartbeat
from datetime import time

# Configure quiet hours (no autonomous actions)
heartbeat.config.quiet_hours_start = time(22, 0)  # 10 PM
heartbeat.config.quiet_hours_end = time(7, 0)     # 7 AM
```

---

## 📊 Monitoring & Observability

### Track Costs

```python
from llm_gateway import llm

# Check session costs
total = llm.get_total_cost()
print(f"Session cost: ${total:.4f}")

# Reset for new session
llm.reset_cost()
```

### Vector Memory Stats

```python
from vector_memory import vector_memory

stats = vector_memory.get_stats()
print(f"Conversations: {stats['conversations']}")
print(f"Skills: {stats['skills']}")
print(f"Knowledge: {stats['knowledge']}")
print(f"Threads: {stats['threads']}")
```

### Tool Usage Analytics

```python
from mcp_integration import mcp

stats = mcp.get_tool_usage_stats()
print(f"Total tool calls: {stats['total_calls']}")
print(f"Most used tools: {stats['most_used']}")
```

### Log Analysis

```python
from log_review import log_reviewer

# Manual review
analysis = log_reviewer.perform_daily_review()

print(f"Error patterns: {len(analysis.error_patterns)}")
for pattern in analysis.error_patterns[:3]:
    print(f"- {pattern.category}: {pattern.count} occurrences")
    print(f"  Fix: {pattern.suggested_fix}")
```

---

## 🚀 Production Deployment

### Environment Configuration

```bash
# .env file
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx
GITHUB_TOKEN=ghp_xxx

# Heartbeat
HEARTBEAT_ENABLED=true
HEARTBEAT_INTERVAL=45
MAX_AUTONOMOUS_COST=5.0
QUIET_HOURS_START=23:00
QUIET_HOURS_END=06:00

# Sub-Agents
ENABLE_SUB_AGENTS=true
MAX_PARALLEL_SUB_AGENTS=3

# Self-Improvement
DAILY_LOG_REVIEW=true
LOG_REVIEW_TIME=03:00
```

### Logging Configuration

```python
from loguru import logger
import sys

# Configure logging
logger.remove()  # Remove default handler
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    level="INFO"
)
logger.add(
    "~/.big_homie/logs/main.log",
    rotation="100 MB",
    retention="30 days",
    level="DEBUG"
)
```

---

## 🎓 Best Practices

1. **Use Thread Isolation** - Keep different contexts separate (coding, research, logistics)
2. **Enable MCP Tools Selectively** - Not every completion needs all tools
3. **Monitor Costs** - Set budgets and track spending per task type
4. **Let Sub-Agents Handle Complexity** - Tasks with 3+ steps benefit from decomposition
5. **Review Logs Regularly** - Self-correction works best with feedback
6. **Store Important Context** - Use vector memory for semantic retrieval
7. **Configure Quiet Hours** - Prevent autonomous actions during off-hours
8. **Trust the Router** - Complexity-based model selection optimizes cost/quality

---

## 🔗 API Reference

See individual module documentation:
- `mcp_integration.py` - Tool definitions and execution
- `vector_memory.py` - Semantic memory storage/retrieval
- `browser_skill.py` - Web automation
- `sub_agents.py` - Multi-agent workflows
- `router.py` - Smart model routing
- `log_review.py` - Self-improvement system
- `llm_gateway.py` - LLM provider interface

---

**Big Homie** - Autonomous, intelligent, and always learning. 🏠
