# Changelog

All notable changes to Big Homie will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Consolidated documentation into `docs/` with category-based navigation.
- `CHANGELOG.md` to track releases.
- GitHub Actions CI workflow (`.github/workflows/ci.yml`) with linting, security scanning, and pytest.
- Unit tests for `governance.py`, `cost_guards.py`, `memory.py`, and `router.py`.
- Renamed `Big Homie` system-prompt file to `big_homie/persona.md`.

### Changed
- README rewritten with repository organization guide and differentiator showcase.
- ~35 root-level markdown files moved into `docs/` subdirectories.

## [0.1.0] - 2026-04-17

### Added
- **Core Agent**: `cognitive_core.py`, `autonomous_loop.py`, `sub_agents.py`, `swarm_intelligence.py`.
- **LLM Gateway**: Multi-provider interface (`llm_gateway.py`) supporting Anthropic, OpenAI, OpenRouter, Ollama, Groq, and GitHub Copilot.
- **Smart Router**: Role-based model routing (`router.py`) with Architect / Worker / Coder / Researcher specialization.
- **Memory**: SQLite-backed key-value memory (`memory.py`), ChromaDB vector memory (`vector_memory.py`), and dream consolidation system (`dream_system.py`).
- **Self-Improvement**: RL feedback loop (`rl_feedback.py`), skill acquisition (`skill_acquisition.py`), correction ledger (`correction_ledger.py`), Karpathy-inspired methods (`karpathy_methods.py`).
- **Governance & Safety**: Human-in-the-loop gates, audit trail, sandboxed execution, kill switch (`governance.py`), cost guards (`cost_guards.py`).
- **MCP Integration**: 62KB Model Context Protocol tool layer (`mcp_integration.py`, `mcp_server.py`).
- **Autonomous Heartbeat**: Proactive 45-minute wake cycle (`heartbeat.py`).
- **Browser Automation**: Playwright-based headless browsing (`browser_skill.py`).
- **Media Generation**: Image, video, and rap video engine (`media_generation.py`, `rap_video_engine.py`).
- **Revenue Engine**: SaaS spinner, site builder, content factory (`revenue_engine.py`, `saas_spinner.py`, `site_builder.py`, `content_factory.py`).
- **Integrations**: Stripe, Shopify, Cloudflare, Vercel, Twilio, Plaid, DraftKings, PrizePicks, Coinbase, Binance, Google Cloud, Perplexity.
- **Full-Stack UI**: Next.js / TypeScript frontend with Tailwind CSS.
- **Desktop App**: PyQt6 native GUI.
- **Persistent SOUL**: Agent identity and ethical guardrails (`SOUL.md`).

[Unreleased]: https://github.com/ncsound919/Big-Homie/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/ncsound919/Big-Homie/releases/tag/v0.1.0
