# 🏠 Big Homie - The Definitive Integrated AI Agent Platform

**Big Homie** now uses the new `master` integrated web platform as the primary release—**AgentBrowser**, **Big Homie Agent**, and **Claw Protect**—while retaining the standout original Big Homie additions from `main`, including the rap video engine and related autonomous feature modules.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ What Makes Big Homie Different

🫀 **Autonomous Heartbeat** - Wakes up every 45 minutes to work proactively
🧠 **Persistent Identity (SOUL)** - Remembers who it is across all sessions
🎯 **Multi-Model Orchestration** - Routes tasks to specialized AI models
🤖 **Sub-Agent Spawning** - Breaks complex work into parallel workflows
🔧 **MCP Tool Integration** - Connects to external APIs and services
🌐 **Browser Automation** - Headless web scraping and interaction
📚 **Vector Memory** - Semantic search across all past interactions
🔍 **Self-Improvement** - Reviews its own logs and gets better over time
💰 **Cost Optimization** - Always chooses the right model for the job
🚀 **Deep Integrations** - Cloudflare, Vercel, Stripe, Base L2, Perplexity, and more

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/tap919/Big-Homie.git
cd Big-Homie
```

### 2. Start the primary integrated web platform (`master` release)

```bash
npm install
npm run dev
```

Visit `http://localhost:3000` to use the AgentBrowser + Claw Protect powered interface.

### 3. Use the retained original Big Homie modules when needed

```bash
# Linux/Mac
chmod +x quick_start.sh
./quick_start.sh

# Windows
quick_start.bat
```

Or install the Python dependencies directly:

```bash
pip install -r requirements.txt
```

### 4. Configure API Keys

Edit `.env` file with your API keys:

```bash
# Required: At least one LLM provider
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx
OPENROUTER_API_KEY=sk-xxx

# Optional: External services
GITHUB_TOKEN=ghp_xxx
SERP_API_KEY=xxx
```

### 5. Run the desktop/agent app

```bash
python main.py
```

The integrated web platform is now the main release surface, with the original Big Homie modules still available in-repo for advanced workflows.

### Retained original Big Homie additions

- `rap_video_engine.py` - rap video generation workflows
- `content_factory.py` - content production workflows
- `site_builder.py` - site generation flows
- `gsd_router.py` / `gsd_dispatcher.py` - original GSD orchestration
- `opencode_provider.py` / `free_api_stack.py` - original provider and free-stack support

---

## 🎯 Core Features

### 1. Autonomous Heartbeat

Big Homie wakes up automatically every 30-60 minutes to:
- ✅ Monitor systems and check health
- ✅ Scan for action items
- ✅ Process tasks autonomously
- ✅ Review error logs
- ✅ Notify you of important updates

```python
from heartbeat import heartbeat, HeartbeatConfig

config = HeartbeatConfig(
    interval_minutes=45,
    max_autonomous_cost=5.0,  # $5/day budget
    quiet_hours_start=time(23, 0),
    quiet_hours_end=time(6, 0)
)

heartbeat.config = config
heartbeat.start()  # Runs in background
```

**See:** `HEARTBEAT.md` for full documentation

### 2. Smart Model Routing

Automatically routes tasks to the best model based on complexity:

| Task Type | Default Model | Cost/1M tokens | Use Case |
|-----------|---------------|----------------|----------|
| Simple | Claude Haiku | $0.25 | Lists, summaries |
| General | Claude Sonnet 4.5 | $3.00 | Most tasks |
| Complex | Claude Opus 4.5 | $15.00 | Strategy, planning |
| Coding | GPT-4 | $30.00 | Development |

```python
from router import router

decision, result = await router.execute_with_routing(
    task="Design a scalable microservices architecture",
    context={"requires_reasoning": True}
)
# Automatically routes to Claude Opus for complex reasoning
```

**See:** `router.py` for implementation

### 3. Sub-Agent Workflows

Complex tasks decompose into specialized sub-agents running in parallel:

```python
from sub_agents import orchestrator

result = await orchestrator.execute_task_with_sub_agents(
    task="Research top 5 AI agents, compare features, create report",
    parallel=True
)

# Spawns:
# - 5 Researcher sub-agents (parallel)
# - 1 Worker sub-agent (summarize)
# - 1 Architect sub-agent (final report)
```

**See:** `AUTONOMOUS_GUIDE.md` for workflows

### 4. MCP Tool Integration

Connect to external services via Model Context Protocol:

**Built-in Tools:**
- `github_search_repos` - Search GitHub
- `github_create_issue` - Create issues
- `browser_navigate` - Visit webpages
- `browser_screenshot` - Capture screenshots
- `file_read` / `file_write` - File operations
- `shell_execute` - Run commands

```python
from llm_gateway import llm

response = await llm.complete_with_tools(
    messages=[{"role": "user", "content": "Find trending Python repos"}],
    max_tool_rounds=5  # Auto-executes tools
)
```

**See:** `mcp_integration.py` for all tools

### 5. Vector Memory

Semantic search across all conversations, skills, and knowledge:

```python
from vector_memory import vector_memory

# Store
vector_memory.add_conversation(
    content="User prefers minimal UI design",
    role="user",
    metadata={"category": "preference"}
)

# Search semantically
results = vector_memory.search_conversations(
    query="What are the user's design preferences?",
    n_results=5
)
```

**Features:**
- Thread isolation (separate coding, research, logistics contexts)
- Automatic embedding generation
- Cosine similarity search
- ChromaDB persistence

**See:** `vector_memory.py` for API

### 6. Browser Automation

Headless browser control with Playwright:

```python
from browser_skill import quick_scrape

data = await quick_scrape(
    url="https://news.ycombinator.com",
    selectors={
        "headlines": ".titleline > a",
        "points": ".score"
    }
)
```

**Capabilities:**
- Navigate to URLs
- Fill forms and click buttons
- Extract data
- Take screenshots
- Execute JavaScript
- Handle authentication

**See:** `browser_skill.py` for full API

### 7. Self-Improvement

Reviews error logs daily and proposes fixes:

```python
from log_review import log_reviewer

analysis = log_reviewer.perform_daily_review()

# Output:
# - Error patterns identified
# - Success rate calculated
# - Improvement suggestions
# - Critical fixes proposed
```

**Automatic Daily Review (3 AM):**
1. Analyzes last 24 hours of logs
2. Identifies error patterns
3. Categorizes by severity
4. Proposes code fixes
5. Tracks success metrics

**See:** `log_review.py` for details

### 8. Persistent SOUL

Big Homie has a persistent identity defined in `SOUL.md`:

**Core Directives:**
- Autonomy with alignment
- Continuous learning
- Multi-domain excellence
- Transparent operation

**Ethical Guardrails:**
- No financial transactions without permission
- No communications without review
- No data deletion without confirmation
- Always explains reasoning

**See:** `SOUL.md` for full identity

---

## 📖 Documentation

- **[AUTONOMOUS_GUIDE.md](AUTONOMOUS_GUIDE.md)** - Complete guide to autonomous features
- **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)** - Integration patterns and examples
- **[DEEP_INTEGRATIONS.md](docs/DEEP_INTEGRATIONS.md)** - Cloudflare, Vercel, Stripe, Blockchain, and more
- **[HEARTBEAT.md](HEARTBEAT.md)** - Autonomous heartbeat system
- **[SOUL.md](SOUL.md)** - Big Homie's persistent identity
- **[README_APP.md](README_APP.md)** - Desktop application guide

---

## 🛠️ Architecture

```
Big Homie
├── SOUL.md                 # Persistent identity
├── main.py                 # PyQt6 GUI application
├── llm_gateway.py          # Multi-provider LLM interface
├── router.py               # Smart model routing
├── sub_agents.py           # Multi-agent orchestration
├── heartbeat.py            # Autonomous execution
├── memory.py               # Traditional memory (SQLite)
├── vector_memory.py        # Semantic memory (ChromaDB)
├── mcp_integration.py      # Tool integration layer
├── browser_skill.py        # Web automation
└── log_review.py           # Self-improvement system
```

---

## 💻 Development

### Install Dependencies

```bash
npm install
pip install -r requirements.txt
```

### Run Checks

```bash
npm run typecheck
npm run lint
```

### Run Tests

```bash
npm test
pytest
```

### Build Executable

```bash
# Linux/Mac
./build.sh

# Windows
build.bat
```

Executable will be in `dist/BigHomie`

---

## 🔧 Configuration

### Basic `.env` Settings

```bash
# LLM Providers (at least one required)
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx
OPENROUTER_API_KEY=sk-xxx

# Models (optional customization)
DEFAULT_MODEL=claude-sonnet-4-5
REASONING_MODEL=claude-opus-4-5
FAST_MODEL=claude-haiku
CODING_MODEL=gpt-4

# Heartbeat
HEARTBEAT_ENABLED=true
HEARTBEAT_INTERVAL=45          # minutes
MAX_AUTONOMOUS_COST=5.0        # USD per day
SPEND_WARNING_THRESHOLD=0.25   # warn before an expensive request is sent
QUIET_HOURS_START=23:00
QUIET_HOURS_END=06:00

# Sub-Agents
ENABLE_SUB_AGENTS=true
MAX_PARALLEL_SUB_AGENTS=3

# Self-Improvement
DAILY_LOG_REVIEW=true
LOG_REVIEW_TIME=03:00

# External Services (optional)
GITHUB_TOKEN=ghp_xxx
SERP_API_KEY=xxx
ALPACA_API_KEY=xxx            # For trading
```

---

## 🎓 Usage Examples

### Example 1: Autonomous Research

```python
from router import router
from sub_agents import orchestrator

# Complex research task
result = await orchestrator.execute_task_with_sub_agents(
    task="""
    Research the latest quantum computing breakthroughs,
    analyze their impact on AI,
    and create a comprehensive technical report
    """,
    parallel=True
)

print(result["report"])
print(f"Cost: ${result['total_cost']:.4f}")
```

### Example 2: Web Automation

```python
from browser_skill import BrowserSkill

async with BrowserSkill() as browser:
    # Navigate and extract
    await browser.navigate("https://example.com")
    title = await browser.extract_text("h1")

    # Fill form
    await browser.fill("#email", "user@example.com")
    await browser.click("button[type=submit]")

    # Screenshot result
    await browser.screenshot("result.png")
```

### Example 3: Tool-Powered Agent

```python
from llm_gateway import llm, TaskType

messages = [
    {
        "role": "user",
        "content": """
        Search GitHub for trending TypeScript repos,
        visit the top 3,
        extract their README files,
        and summarize the key features
        """
    }
]

response = await llm.complete_with_tools(
    messages=messages,
    task_type=TaskType.GENERAL,
    max_tool_rounds=10
)
```

---

## 📊 Cost Tracking

Big Homie tracks all costs automatically:

```python
from llm_gateway import llm
from heartbeat import heartbeat

# Session costs
session_cost = llm.get_total_cost()

# Autonomous costs (daily)
autonomous_cost = heartbeat.daily_cost

print(f"Session: ${session_cost:.4f}")
print(f"Autonomous: ${autonomous_cost:.4f}")
```

**Budget Controls:**
- Session alerts at configurable threshold
- Daily autonomous budget enforcement
- Per-task cost estimation
- Model cost optimization

---

## 🔒 Safety & Privacy

- **No data leaves your machine** except API calls to LLM providers
- **Local storage** - SQLite and ChromaDB on disk
- **Permission levels** for autonomous actions
- **Rate limiting** on heartbeat execution
- **Quiet hours** configuration
- **Cost budgets** prevent runaway spending

---

## 🌟 Comparison

| Feature | Big Homie | OpenClaw | Hermes |
|---------|-----------|----------|--------|
| Autonomous Heartbeat | ✅ 45min | ❌ | ❌ |
| Multi-Model Routing | ✅ 4 roles | ❌ Single | ✅ Limited |
| Sub-Agent Spawning | ✅ Full | ✅ Plugins | ❌ |
| MCP Integration | ✅ Built-in | ✅ Servers | ❌ |
| Vector Memory | ✅ ChromaDB | ❌ | ✅ Pinecone |
| Browser Automation | ✅ Playwright | ❌ | ❌ |
| Self-Improvement | ✅ Daily | ✅ Manual | ✅ Auto |
| Desktop GUI | ✅ Native | ❌ Web | ❌ CLI |
| Cost Optimization | ✅ Auto | ❌ | ❌ |
| Persistent Soul | ✅ SOUL.md | ❌ | ✅ Memory |

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file

---

## 🙏 Acknowledgments

Built with:
- [Anthropic Claude](https://anthropic.com) - Advanced reasoning
- [OpenAI GPT](https://openai.com) - Coding assistance
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [Playwright](https://playwright.dev/) - Browser automation

---

## 📧 Support

- **Issues:** [GitHub Issues](https://github.com/tap919/Big-Homie/issues)
- **Discussions:** [GitHub Discussions](https://github.com/tap919/Big-Homie/discussions)

---

**Big Homie** - The autonomous agent that truly works for you. 🏠
