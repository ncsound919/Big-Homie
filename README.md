# 🏠 Big Homie — Autonomous AI Agent Platform

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/ncsound919/Big-Homie/actions/workflows/ci.yml/badge.svg)](https://github.com/ncsound919/Big-Homie/actions/workflows/ci.yml)

Big Homie is an autonomous AI agent that wakes up on its own, routes tasks across multiple LLM providers, spawns sub-agent swarms, remembers everything via vector memory, and improves itself through reinforcement learning — all behind a single Python + Next.js full-stack interface.

---

## 🔥 What Only Big Homie Has

These capabilities are **not found** in OpenClaw, Hermes Agent, or comparable open-source agents:

| Capability | Module | Why It Matters |
|---|---|---|
| **Karpathy-Inspired Self-Tuning** | [`karpathy_methods.py`](karpathy_methods.py) (51 KB) | Temperature calibration, loss-landscape analysis, and training-loop introspection applied to live agent decisions. |
| **Swarm Intelligence** | [`swarm_intelligence.py`](swarm_intelligence.py) | Multi-agent emergent coordination — agents vote, merge context, and converge on solutions collectively. |
| **Dream Consolidation** | [`dream_system.py`](dream_system.py) (31 KB) | Offline memory replay inspired by biological sleep — compresses, prunes, and strengthens knowledge between sessions. |
| **RL Feedback Loop** | [`rl_feedback.py`](rl_feedback.py) + [`correction_ledger.py`](correction_ledger.py) | Records every correction, learns from mistakes, and auto-adjusts routing/temperature over time. |
| **Rap Video Engine** | [`rap_video_engine.py`](rap_video_engine.py) | End-to-end lyric → video pipeline — a creative capability no other agent ships. |
| **Revenue Engine** | [`revenue_engine.py`](revenue_engine.py), [`saas_spinner.py`](saas_spinner.py), [`site_builder.py`](site_builder.py) | Autonomous SaaS project scaffolding, site generation, and monetization workflows. |
| **Governance + Cost Guards** | [`governance.py`](governance.py) (43 KB) + [`cost_guards.py`](cost_guards.py) | Kill switch, sandboxed execution, human-in-the-loop gates, and per-request budget enforcement — baked into every tool call path. |

---

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/ncsound919/Big-Homie.git && cd Big-Homie

# 2. Web platform (Next.js)
npm install && npm run dev          # → http://localhost:3000

# 3. Python agent core
pip install -r requirements.txt
python main.py                      # PyQt6 desktop GUI
```

Copy `.env.example` → `.env` and add at least one LLM provider key (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, or `OPENROUTER_API_KEY`).

See **[docs/getting-started/INSTALL.md](docs/getting-started/INSTALL.md)** for full instructions.

---

## 🗂️ How This Repo Is Organized

```
Big-Homie/
│
├── src/                        # Next.js / TypeScript frontend (AgentBrowser + Claw Protect UI)
│   ├── app/                    #   App Router pages and API routes
│   └── components/             #   React components
│
├── big_homie/                  # Python package (importable library)
│   ├── core/                   #   CognitiveCore, AutonomousLoop, Heartbeat
│   ├── agents/                 #   Agent profiles and orchestration
│   ├── memory/                 #   Memory subsystem wrappers
│   ├── security/               #   Governance, kill switch, sandbox
│   ├── skills/                 #   Skill acquisition and registry
│   ├── tools/                  #   Browser, MCP tool wrappers
│   └── revenue/                #   Revenue engine, SaaS spinner
│
├── integrations/               # Third-party service adapters (Stripe, Shopify, Cloudflare, …)
│
├── tests/                      # Pytest test suite
│   ├── unit/                   #   Unit tests for governance, cost guards, memory, router
│   └── conftest.py             #   Shared fixtures
│
├── docs/                       # All documentation (see docs/README.md)
│   ├── getting-started/        #   Installation, MCP setup, verticals
│   ├── architecture/           #   Autonomous guide, heartbeat, SOUL
│   ├── security/               #   Security policy, defense-in-depth
│   ├── skills/                 #   Feature catalogues, multimodal, media
│   ├── integrations/           #   Integration patterns
│   └── reference/              #   Prompt templates, best practices, test reports
│
├── main.py                     # Desktop app entry point (PyQt6)
├── llm_gateway.py              # Multi-provider LLM interface
├── router.py                   # Smart model routing (Architect / Worker / Coder / Researcher)
├── cognitive_core.py           # Central reasoning engine
├── sub_agents.py               # Multi-agent orchestration
├── heartbeat.py                # 45-minute autonomous wake cycle
├── memory.py                   # SQLite key-value memory
├── vector_memory.py            # ChromaDB semantic memory
├── dream_system.py             # Offline memory consolidation
├── mcp_integration.py          # MCP tool layer (62 KB — largest module)
├── governance.py               # Safety: audit trail, sandbox, kill switch, human gates
├── cost_guards.py              # Per-request and daily budget enforcement
├── karpathy_methods.py         # Self-tuning via Karpathy-inspired techniques
├── swarm_intelligence.py       # Multi-agent emergent coordination
├── rl_feedback.py              # Reinforcement learning feedback
├── rap_video_engine.py         # Lyric → video creative pipeline
├── revenue_engine.py           # Autonomous monetization
│
├── big_homie/persona.md        # System prompt / agent personality (41 KB)
├── pyproject.toml              # Python project metadata, ruff/pytest config
├── package.json                # Node.js / Next.js metadata
├── requirements.txt            # Python dependencies
├── .github/workflows/ci.yml    # CI: lint, security scan, pytest
└── CHANGELOG.md                # Release history
```

**Primary languages:** Python (agent core, CLI, desktop) · TypeScript/Next.js (web UI).

**Entry points:**
- **Web UI** → `npm run dev`
- **Desktop / Agent** → `python main.py`
- **MCP Server** → `python mcp_server_main.py`

---

## 🎯 Core Features

### Autonomous Heartbeat
Wakes every 45 minutes to monitor systems, scan for action items, review error logs, and notify you — with configurable quiet hours and daily cost budgets.
→ [docs/architecture/HEARTBEAT.md](docs/architecture/HEARTBEAT.md)

### Smart Model Routing
Analyzes task complexity and routes to the best model: Haiku for cheap/fast, Sonnet for general, Opus for deep reasoning, GPT-4 for code.
→ [`router.py`](router.py)

### Sub-Agent Swarms
Complex tasks decompose into parallel Researcher, Worker, Architect, and Coder sub-agents that merge results.
→ [docs/architecture/AUTONOMOUS_GUIDE.md](docs/architecture/AUTONOMOUS_GUIDE.md)

### MCP Tool Integration
62 KB tool layer connecting GitHub, browser automation, file I/O, shell execution, and external APIs via the Model Context Protocol.
→ [`mcp_integration.py`](mcp_integration.py)

### Vector Memory + Dream System
ChromaDB semantic search across all conversations, plus an offline dream consolidation system that replays and strengthens knowledge between sessions.
→ [`vector_memory.py`](vector_memory.py) · [`dream_system.py`](dream_system.py)

### Self-Improvement
Daily log review, RL feedback loop, correction ledger, and Karpathy-inspired temperature/sampling calibration.
→ [`rl_feedback.py`](rl_feedback.py) · [`karpathy_methods.py`](karpathy_methods.py)

### Governance & Cost Guards
Human-in-the-loop approval gates, audit trail with hash-chained integrity, sandboxed execution, kill switch, and per-request + daily budget enforcement.
→ [`governance.py`](governance.py) · [`cost_guards.py`](cost_guards.py)

### Persistent SOUL
Agent identity, core directives, and ethical guardrails that persist across all sessions.
→ [docs/architecture/SOUL.md](docs/architecture/SOUL.md)

---

## 💻 Development

```bash
# Install all dependencies
npm install
pip install -r requirements.txt
pip install -e ".[dev]"

# Lint
npm run lint
ruff check .

# Test
npm test
pytest

# Build desktop executable
./build.sh   # or build.bat on Windows
```

---

## 📖 Documentation

All docs live in [`docs/`](docs/README.md):

| Section | Contents |
|---|---|
| [Getting Started](docs/getting-started/) | Installation, desktop app, MCP setup, vertical installs |
| [Architecture](docs/architecture/) | Autonomous guide, heartbeat, SOUL, creation log |
| [Security](docs/security/) | Security policy, defense-in-depth |
| [Skills & Features](docs/skills/) | Feature catalogue, multimodal, media generation, competitive comparison |
| [Integrations](docs/integrations/) | Integration patterns, deep integrations |
| [Reference](docs/reference/) | Prompt templates, best practices, test reports |

See also: **[CHANGELOG.md](CHANGELOG.md)** for release history.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Make your changes and add tests
4. Run `ruff check .` and `pytest`
5. Submit a pull request

---

## 📝 License

MIT — see [LICENSE](LICENSE).

---

**Big Homie** — the autonomous agent that truly works for you. 🏠
