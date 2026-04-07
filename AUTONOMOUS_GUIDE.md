# Big Homie - Advanced Autonomous Agent

## 🌟 What Makes Big Homie Different

Big Homie isn't just another AI chatbot. It's a **truly autonomous agent** with:

- **Persistent Identity (SOUL)** - Remembers who it is across sessions
- **Autonomous Heartbeat** - Wakes up every 45 minutes to work proactively
- **Multi-Model Orchestration** - Routes tasks to specialized AI models
- **Sub-Agent Spawning** - Breaks complex work into parallel workflows
- **Self-Improvement** - Reviews its own logs and gets better over time
- **Cost Optimization** - Always chooses the right model for the job

---

## 🧠 Core Architecture

### 1. SOUL - Persistent Identity

Big Homie has a **soul** defined in `SOUL.md` that persists across all sessions:

**Core Directives:**
- Autonomy with alignment (acts proactively but always in your interest)
- Continuous learning from every interaction
- Multi-domain excellence (Finance, Code, Research, Marketing, Web)
- Transparent operation with detailed logging

**Ethical Guardrails:**
- Won't make financial transactions without permission
- Won't send communications without review
- Won't delete data without confirmation
- Always explains reasoning and shows work

**Working Principles:**
- Action over analysis
- Iterate quickly
- Learn in public
- Measure everything
- Automate relentlessly

### 2. HEARTBEAT - Autonomous Execution

Every 30-60 minutes, Big Homie autonomously:

```
🫀 HEARTBEAT CYCLE
┌─────────────────────────────┐
│  1. System Health Check     │  ← Verify APIs, memory, budget
│  2. Scan Action Items       │  ← Find new opportunities
│  3. Process Tasks           │  ← Execute autonomously
│  4. Review Logs (Daily)     │  ← Self-improve
│  5. Notify User             │  ← Report findings
└─────────────────────────────┘
```

**What It Does:**
- ✅ Monitors markets (if configured)
- ✅ Scans emails/messages (if authorized)
- ✅ Processes data aggregations
- ✅ Generates reports
- ✅ Analyzes error patterns
- ✅ Optimizes its own code
- ✅ Cleans old data

**Safety Mechanisms:**
- Daily cost budget ($5 default)
- Quiet hours (23:00-06:00)
- Rate limiting (max 3 actions/hour)
- Permission levels for different actions

### 3. Smart Router - Multi-Model Orchestration

Big Homie uses **4 specialized agent roles** and routes tasks intelligently:

#### Agent Roles

**🏛️ ARCHITECT** (Claude Opus 4.5)
- High-level reasoning and strategic planning
- System design and architecture
- Complex problem decomposition
- Trade-off evaluation
- **Use case**: "Design a scalable microservices architecture"

**⚡ WORKER** (Claude Haiku / GPT-4o-mini)
- High-volume, cheap tasks
- Data processing and summarization
- Format conversion
- Simple extractions
- **Use case**: "Summarize these 100 customer reviews"

**💻 CODER** (GPT-4 / DeepSeek)
- Software development
- Debugging and optimization
- Code review
- Technical implementation
- **Use case**: "Implement OAuth2 authentication in Python"

**🔍 RESEARCHER** (Claude Sonnet 4.5)
- Deep analysis and investigation
- Fact-checking and synthesis
- Information gathering
- Comprehensive understanding
- **Use case**: "Research the latest quantum computing breakthroughs"

#### Routing Decision Process

```python
Task → Analyze Complexity → Detect Role → Select Model → Execute

Example:
"Analyze NVDA stock and create investment strategy"
  → High complexity (0.8)
  → Role: ARCHITECT
  → Model: Claude Opus 4.5
  → Estimated cost: $0.02
```

**Optimization Modes:**
- `prefer_cost=True` - Use cheapest suitable model
- `prefer_quality=True` - Use highest quality model
- Default: Balanced (complexity-based)

### 4. Sub-Agent Spawning

For complex multi-step tasks, Big Homie spawns specialized sub-agents:

#### Workflow Example

**User Request:** "Research AI trends, write a comprehensive report, and create a presentation"

```
Main Agent (Architect)
    │
    ├─ Decompose into 5 sub-tasks
    │
    ├─→ Sub-Agent 1 (Researcher)
    │   └─ "Gather AI trend data from multiple sources"
    │
    ├─→ Sub-Agent 2 (Researcher)
    │   └─ "Fact-check and verify data" [depends on 1]
    │
    ├─→ Sub-Agent 3 (Worker)
    │   └─ "Summarize findings" [depends on 2]
    │
    ├─→ Sub-Agent 4 (Coder)
    │   └─ "Generate presentation slides" [depends on 3]
    │
    └─→ Sub-Agent 5 (Architect)
        └─ "Review and synthesize final report" [depends on all]

Main Agent
    └─ Aggregate results and deliver
```

**Benefits:**
- ✅ Prevents token limit issues
- ✅ Maintains focus per sub-task
- ✅ Parallel execution when possible
- ✅ Dependency management
- ✅ Cost-effective (right model per task)

#### Execution Modes

**Parallel Execution:**
```python
orchestrator.execute_workflow(workflow, parallel=True)
# Sub-agents 1 & 2 run simultaneously
# Sub-agents 3 & 4 wait for dependencies
```

**Sequential Execution:**
```python
orchestrator.execute_workflow(workflow, parallel=False)
# All sub-agents run one at a time
# Safer for tasks with unclear dependencies
```

---

## 🎯 Use Cases & Examples

### Finance & Trading

```python
# Autonomous market monitoring
Task: "Monitor my watchlist and alert on 5%+ moves"
└─ Heartbeat executes every 45 minutes
└─ Checks prices autonomously
└─ Notifies only on significant events
```

### Software Development

```python
# Complex feature implementation
Request: "Add user authentication with email verification"
└─ ARCHITECT decomposes task
    ├─ CODER: Implement backend API
    ├─ CODER: Create frontend components
    ├─ CODER: Write tests
    └─ WORKER: Update documentation
└─ Main agent reviews and integrates
```

### Research & Analysis

```python
# Deep competitive analysis
Request: "Analyze top 5 competitors in AI agent space"
└─ Sub-agents spawn in parallel
    ├─ RESEARCHER: Company 1 analysis
    ├─ RESEARCHER: Company 2 analysis
    ├─ RESEARCHER: Company 3 analysis
    ├─ RESEARCHER: Company 4 analysis
    └─ RESEARCHER: Company 5 analysis
└─ ARCHITECT synthesizes findings
└─ WORKER formats final report
```

### Content Creation

```python
# Multi-platform campaign
Request: "Create marketing campaign for product launch"
└─ ARCHITECT plans strategy
    ├─ WORKER: Generate 10 social media posts
    ├─ WORKER: Write email campaign
    ├─ RESEARCHER: Analyze competitor campaigns
    └─ ARCHITECT: Review and refine
```

---

## ⚙️ Configuration

### Basic Setup

1. **Copy environment template**
```bash
cp .env.example .env
```

2. **Configure in `.env`**
```bash
# Required: At least one LLM provider
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Heartbeat Configuration
HEARTBEAT_ENABLED=true
HEARTBEAT_INTERVAL=45  # minutes
MAX_AUTONOMOUS_COST=5.00  # USD per day
QUIET_HOURS_START=23:00
QUIET_HOURS_END=06:00

# Sub-Agent Settings
ENABLE_SUB_AGENTS=true
MAX_PARALLEL_SUB_AGENTS=3

# Model Selection (optional customization)
DEFAULT_MODEL=claude-sonnet-4-5
REASONING_MODEL=claude-opus-4-5
FAST_MODEL=claude-haiku
CODING_MODEL=gpt-4
```

### Advanced Configuration

**Heartbeat Customization:**
```python
from heartbeat import HeartbeatSystem, HeartbeatConfig
from datetime import time

config = HeartbeatConfig(
    enabled=True,
    interval_minutes=30,  # More frequent
    quiet_hours_start=time(22, 0),
    quiet_hours_end=time(7, 0),
    max_autonomous_cost=10.0,  # Higher budget
    notification_callback=my_notification_handler
)

heartbeat = HeartbeatSystem(config)
heartbeat.start()
```

**Router Customization:**
```python
from router import router

# Force specific role
decision = router.route_task(
    task="Implement feature X",
    context={"code_context": True},
    prefer_quality=True  # Use best model
)

# Execute with routing
decision, result = await router.execute_with_routing(
    task="Your task",
    context={"requires_reasoning": True}
)
```

**Sub-Agent Usage:**
```python
from sub_agents import orchestrator

# Simple API
result = await orchestrator.execute_task_with_sub_agents(
    task="Complex multi-step task",
    parallel=True  # Execute independently tasks in parallel
)

# Advanced workflow control
workflow = await orchestrator.decompose_task(task)
completed = await orchestrator.execute_workflow(workflow)
```

---

## 📊 Cost Optimization

### Smart Model Selection

Big Homie automatically chooses the cheapest suitable model:

| Task Type | Default Model | Cost/1M tokens | Use Case |
|-----------|--------------|----------------|----------|
| Simple tasks | Claude Haiku | $0.25 | Summaries, lists |
| General work | Claude Sonnet | $3.00 | Most tasks |
| Complex reasoning | Claude Opus | $15.00 | Strategy, planning |
| Code generation | GPT-4 | $30.00 | Development |
| Local (offline) | Ollama | $0.00 | Privacy, no cost |

### Cost Tracking

```python
# Real-time cost monitoring
from llm_gateway import llm

current_cost = llm.get_total_cost()  # Session total
print(f"Current session: ${current_cost:.4f}")

# Heartbeat tracks autonomous costs separately
from heartbeat import heartbeat

autonomous_cost = heartbeat.daily_cost
print(f"Autonomous today: ${autonomous_cost:.4f}")
```

### Budget Controls

**Session Budget:**
```python
# Alert when threshold reached
COST_ALERT_THRESHOLD=10.0
# GUI shows warning when exceeded
```

**Daily Autonomous Budget:**
```python
# Heartbeat stops when reached
MAX_AUTONOMOUS_COST=5.0
# Resets at midnight
```

---

## 🔒 Safety & Permissions

### Permission Levels

**Level 0: Always Allowed** (No permission needed)
- Reading and analyzing data
- Creating drafts for review
- Research and information gathering
- Log analysis
- Cost calculations

**Level 1: Heartbeat Allowed** (During autonomous execution)
- Data processing
- Summarization
- Report generation
- System monitoring

**Level 2: User Confirmation** (Single approval)
- Sending messages (after draft review)
- Creating calendar events
- Minor configuration changes

**Level 3: Multiple Confirmations** (Requires 2+ approvals)
- Financial transactions
- Deleting data
- System-critical changes
- Privacy-sensitive operations

### Autonomous Safety

**Rate Limiting:**
- Max 1 heartbeat per 30 minutes
- Max 3 autonomous actions per hour
- Budget check before each action

**Failure Handling:**
- 3 consecutive failures → pause system
- Cost spike → alert and pause
- API errors → exponential backoff
- All failures logged for review

**Quiet Hours:**
- No autonomous actions during sleep hours
- No notifications (except critical)
- System maintenance only

---

## 📈 Self-Improvement

### Daily Log Review

Every day at 3 AM, Big Homie:

1. **Analyzes error logs**
   - Identifies failure patterns
   - Categorizes error types
   - Tracks frequency

2. **Reviews successful tasks**
   - Identifies optimal workflows
   - Updates skill success rates
   - Benchmarks performance

3. **Proposes improvements**
   - Suggests code fixes
   - Recommends skill updates
   - Optimizes model routing

4. **Updates skills**
   - Refines existing workflows
   - Removes obsolete patterns
   - Documents best practices

### Skill Learning

```python
# After successful complex task
memory.save_skill(
    name="competitor_analysis",
    description="Research and analyze competitors",
    workflow=[
        {"role": "researcher", "task": "Gather data"},
        {"role": "researcher", "task": "Fact-check"},
        {"role": "architect", "task": "Synthesize"}
    ]
)

# Skill improves with use
memory.record_skill_result("competitor_analysis", success=True, duration=45.0)
```

### Continuous Optimization

**Model Performance Tracking:**
- Success rate per model/task type
- Average cost per task category
- Response quality scores
- User feedback integration

**Routing Improvements:**
- Learn optimal model for each task pattern
- Adjust complexity thresholds
- Update role detection keywords
- Refine cost/quality balance

---

## 🚀 Getting Started

### Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your API keys

# 3. Run
python main.py
```

### First Autonomous Cycle

After starting Big Homie:

1. **Heartbeat starts automatically** (if enabled)
2. **First wake-up in 45 minutes**
3. **Check dashboard for status**
4. **View autonomous actions in History tab**

### Example Commands

**Test Router:**
```python
# In Python console or UI
"Analyze the architecture of Big Homie and suggest improvements"
# → Routes to ARCHITECT role (Claude Opus)
# → Provides detailed strategic analysis
```

**Test Sub-Agents:**
```python
"Research quantum computing trends, create a technical report, and generate a presentation outline"
# → Spawns 4-5 sub-agents
# → Executes in parallel
# → Delivers comprehensive result
```

**Test Heartbeat:**
```bash
# Monitor heartbeat.log
tail -f ~/.big_homie/heartbeat.log

# Or check in UI Settings tab
# Shows: Next heartbeat, Daily cost, Actions taken
```

---

## 🎓 Best Practices

### 1. Let It Learn
- Don't micromanage - let Big Homie find optimal workflows
- Review autonomous actions weekly
- Provide feedback on quality
- Let skills develop over time

### 2. Set Appropriate Budgets
- Start conservative ($5/day autonomous)
- Increase as you see value
- Monitor cost per task type
- Adjust model preferences

### 3. Use Sub-Agents for Complex Work
- Tasks with 3+ distinct steps
- Projects requiring different expertise
- Parallel research opportunities
- Multi-format deliverables

### 4. Trust the Router
- Don't override model selection often
- Let complexity detection work
- Monitor routing decisions
- Provide feedback on misroutes

### 5. Review Autonomously
- Check heartbeat results daily
- Approve autonomous drafts
- Learn from autonomous insights
- Refine action item scanning

---

## 🔧 Troubleshooting

### Heartbeat Not Running

```bash
# Check configuration
cat .env | grep HEARTBEAT

# Verify in Python
from heartbeat import heartbeat
print(heartbeat.state)  # Should be "running"

# Start manually if needed
heartbeat.start()
```

### High Autonomous Costs

```bash
# Check daily cost
from heartbeat import heartbeat
print(f"Today: ${heartbeat.daily_cost:.2f}")

# Reduce budget
MAX_AUTONOMOUS_COST=2.0  # In .env

# Increase interval
HEARTBEAT_INTERVAL=60  # Every hour instead of 45 min
```

### Sub-Agents Failing

```python
# Check workflow status
from sub_agents import orchestrator
status = orchestrator.get_workflow_status(workflow_id)
print(status)

# Disable parallel execution
result = await orchestrator.execute_workflow(workflow, parallel=False)
```

---

## 📚 Further Reading

- `SOUL.md` - Big Homie's persistent identity and principles
- `HEARTBEAT.md` - Detailed autonomous system documentation
- `router.py` - Multi-model orchestration implementation
- `sub_agents.py` - Sub-agent spawning system
- `heartbeat.py` - Autonomous heartbeat implementation

---

## 🌟 Comparison

| Feature | Big Homie | OpenClaw | Hermes |
|---------|-----------|----------|--------|
| Autonomous Heartbeat | ✅ 45min | ❌ | ❌ |
| Multi-Model Routing | ✅ 4 roles | ❌ Single | ✅ Limited |
| Sub-Agent Spawning | ✅ Full | ✅ Plugins | ❌ |
| Cost Optimization | ✅ Auto | ❌ | ❌ |
| Self-Improvement | ✅ Daily | ✅ Manual | ✅ Automatic |
| Desktop GUI | ✅ Native | ❌ Web | ❌ CLI |
| Persistent Soul | ✅ SOUL.md | ❌ | ✅ Memory |
| Local Fallback | ✅ Ollama | ❌ | ✅ Local |

---

**Big Homie** - The autonomous agent that truly works for you. 🏠
