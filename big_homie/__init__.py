"""
Big Homie - The Ultimate Single Agent

Invented tools:
  - AgentBrowser  : big_homie.tools.browser
  - Big Homie OG  : big_homie.core
  - Claw Protect  : big_homie.security
"""

__version__ = "1.0.0"
__author__ = "ncsound919"
__description__ = "Autonomous AI agent with heartbeat, sub-agents, and MCP server"

# Package-level convenience imports
from big_homie.core import CognitiveCore, AutonomousLoop, Heartbeat  # noqa: F401
from big_homie.security import governance  # noqa: F401

__all__ = [
    "CognitiveCore",
    "AutonomousLoop",
    "Heartbeat",
    "governance",
    "__version__",
]
