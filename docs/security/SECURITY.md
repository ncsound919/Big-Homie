# Security Policy

## Big Homie Security Architecture

Big Homie is built on three security-first inventions:

- **AgentBrowser** — sandboxed browser automation with CSP enforcement
- **Big Homie Agent** — autonomous agent with cost guards, kill switch, and human-in-the-loop gates
- **Claw Protect** (`governance.py`) — tamper-evident audit trail, sandboxed execution, 4-tier risk classification, and cascade kill switch

---

## Supported Versions

| Version | Supported |
|---------|----------|
| `main` (latest) | Yes |
| `< 1.0.0` | No |

---

## Reporting a Vulnerability

We take security vulnerabilities seriously. **Please do NOT open a public GitHub issue for security vulnerabilities.**

### How to Report

1. **Email**: Send details to the repository owner via GitHub's private reporting feature
2. **GitHub Private Reporting**: Use [GitHub's Security Advisories](https://github.com/ncsound919/Big-Homie/security/advisories/new) to report privately
3. **Response time**: We aim to respond within 48 hours
4. **Fix timeline**: Critical issues patched within 7 days, high within 14 days

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Suggested fix (optional)

---

## Security Controls (Claw Protect)

### AuditTrail
- SHA-256 hash-chained entries — tamper-evident log
- Every agent action is recorded with timestamp + forward hash
- `verify_integrity()` detects any post-hoc modifications

### HumanInTheLoop
- 4-tier risk classification: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
- Auto-approve only for `LOW` risk when configured
- `HIGH` and `CRITICAL` actions always require explicit human approval
- Financial transactions, data deletion, and external communications are `HIGH+`

### SandboxedExecution
- Shell command allowlist — only pre-approved commands execute
- Environment variable scrubbing — `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `STRIPE_API_KEY` etc. are never passed to subprocesses
- Import blocklist — dangerous Python modules blocked at execution time
- **Note**: Sandbox is advisory (Python-level), not OS-level. For production deployments, wrap with `gVisor` or `Firejail`.

### KillSwitch
- Immediate cascade halt of all sub-agents and background processes
- State capture to disk before halt — enables forensic recovery
- `trigger()` → `recover()` lifecycle with full history
- Idempotent: safe to trigger multiple times

---

## CI Security Gates

Every commit and PR runs:

| Tool | Purpose |
|------|---------|
| `bandit` | SAST — detects `shell=True`, hardcoded secrets, unsafe deserialization |
| `pip-audit` | CVE scanning of all Python dependencies |
| `truffleHog` | Secret scanning — blocks committed API keys/tokens |
| `ruff` | Linting — catches unsafe code patterns |

---

## Known Limitations

1. **Sandbox is advisory** — Python-level isolation only; OS-level isolation (`gVisor`) is recommended for production
2. **LLM API keys** are required for operation; ensure `.env` is in `.gitignore` (it is by default)
3. **Autonomous heartbeat** should have network egress limited in production environments
4. **MCP server** (`mcp_server.py`) should be behind authentication if exposed externally

---

## Dependency Security

- Dependencies are pinned in `pyproject.toml`
- Run `pip-audit` locally: `pip install pip-audit && pip-audit`
- Run `bandit` locally: `pip install bandit && bandit -r . --exclude .venv,node_modules`

---

## License

MIT — See [LICENSE](./LICENSE)
