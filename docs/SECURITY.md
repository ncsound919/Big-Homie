# Security Documentation

## Overview
ClawProtect Browser integrates Claw Protect security into AgentBrowser for secure agentic browsing and development.

## Security Features

### Security Levels
- **Passive**: Warns of threats but doesn't block actions
- **Active** (default): Blocks dangerous actions
- **Configurable**: User can set per-mode security

### Security Checks
- **Prompt Injection**: Detects manipulation attempts in prompts
- **Secrets Detection**: Prevents API keys/passwords from exposure
- **Command Validation**: Validates shell commands before execution

### Agent Security Tiers
- **Full**: All validations enabled (default for untrusted agents)
- **Reduced**: Basic checks only (for verified internal agents)
- **Custom**: User-defined rules

## Integration Points
- Pipeline phases: Each phase runs security validation
- Agent execution: Custom agents run with their tier's security level
- Claw Protect API: Connected at http://localhost:3333

## Troubleshooting
- If Claw Protect unavailable, security fails open (allows action)
- Check Security tab for event logs
- Adjust security level in Settings
