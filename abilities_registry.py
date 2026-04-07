"""
Abilities Registry - Central integration point for all 28 agent abilities
across 7 power tiers. Provides unified access, status, and management.
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from loguru import logger
from config import settings


@dataclass
class AbilityInfo:
    """Information about a registered ability"""
    name: str
    tier: int
    tier_name: str
    category: str
    description: str
    power_score: int
    module: str
    enabled: bool = True
    tags: List[str] = field(default_factory=list)


class AbilitiesRegistry:
    """
    Central registry of all 28 agent abilities across 7 tiers.

    Provides:
    - Unified access to all abilities
    - Status dashboard
    - Tier-based ability discovery
    - Lazy initialization of modules
    """

    def __init__(self):
        self._modules: Dict[str, Any] = {}
        self._abilities: Dict[str, AbilityInfo] = {}
        self._register_all_abilities()

    def _register_all_abilities(self):
        """Register all 28 abilities"""

        # ===== TIER 1: Cognitive Core =====
        self._register("chain_of_thought", AbilityInfo(
            name="Chain-of-Thought Reasoning", tier=1, tier_name="Cognitive Core",
            category="CORE", description="Decomposes problems into explicit intermediate steps",
            power_score=95, module="cognitive_core", tags=["cot", "step-by-step", "accuracy"]
        ))
        self._register("react_loop", AbilityInfo(
            name="ReAct Loop", tier=1, tier_name="Cognitive Core",
            category="CORE", description="Think → Act → Observe iterative cycle",
            power_score=98, module="cognitive_core", tags=["react", "grounded", "iterative"]
        ))
        self._register("tree_of_thought", AbilityInfo(
            name="Tree-of-Thought Planning", tier=1, tier_name="Cognitive Core",
            category="ADVANCED", description="Explores multiple reasoning branches with backtracking",
            power_score=92, module="cognitive_core", tags=["tot", "branching", "backtrack"]
        ))
        self._register("self_consistency", AbilityInfo(
            name="Self-Consistency Verification", tier=1, tier_name="Cognitive Core",
            category="ADVANCED", description="Multi-path consensus voting for reliable answers",
            power_score=89, module="cognitive_core", tags=["cot-sc", "consensus", "reliability"]
        ))

        # ===== TIER 2: Memory Systems =====
        self._register("episodic_memory", AbilityInfo(
            name="Episodic Memory", tier=2, tier_name="Memory Systems",
            category="MEMORY", description="Stores and retrieves records of past interactions",
            power_score=88, module="memory", tags=["past-events", "rag", "vector-db"]
        ))
        self._register("semantic_knowledge", AbilityInfo(
            name="Semantic Knowledge Base", tier=2, tier_name="Memory Systems",
            category="MEMORY", description="Persistent structured repository of domain facts",
            power_score=91, module="vector_memory", tags=["knowledge-graph", "facts", "domain"]
        ))
        self._register("procedural_skills", AbilityInfo(
            name="Procedural Skill Cache", tier=2, tier_name="Memory Systems",
            category="MEMORY", description="Reusable procedures for multi-step sequences",
            power_score=85, module="skill_acquisition", tags=["automation", "workflows", "efficiency"]
        ))
        self._register("context_manager", AbilityInfo(
            name="Context Window Manager", tier=2, tier_name="Memory Systems",
            category="MEMORY", description="Intelligent context trimming and compression",
            power_score=83, module="context_manager", tags=["compression", "summarization", "context"]
        ))

        # ===== TIER 3: Perception =====
        self._register("multimodal_perception", AbilityInfo(
            name="Multimodal Perception", tier=3, tier_name="Perception",
            category="SENSE", description="Process text, images, PDFs, audio in unified context",
            power_score=97, module="vision_analysis",
            enabled=settings.enable_vision, tags=["vision", "audio", "documents"]
        ))
        self._register("web_search", AbilityInfo(
            name="Real-Time Web Search", tier=3, tier_name="Perception",
            category="SENSE", description="Queries live internet data with source attribution",
            power_score=94, module="mcp_integration", tags=["live-data", "grounding", "citations"]
        ))
        self._register("document_intelligence", AbilityInfo(
            name="Document Intelligence", tier=3, tier_name="Perception",
            category="SENSE", description="Parses PDFs, spreadsheets, code repos with semantic understanding",
            power_score=90, module="document_intelligence",
            enabled=settings.enable_document_intelligence,
            tags=["pdf", "excel", "code-repos"]
        ))
        self._register("environment_sensing", AbilityInfo(
            name="Environment Sensing", tier=3, tier_name="Perception",
            category="SENSE", description="Monitors system state, file changes, API responses",
            power_score=86, module="environment_sensing",
            enabled=settings.enable_environment_monitoring,
            tags=["events", "monitoring", "reactive"]
        ))

        # ===== TIER 4: Tool Use & Action =====
        self._register("code_execution", AbilityInfo(
            name="Code Execution Engine", tier=4, tier_name="Tool Use & Action",
            category="ACTION", description="Writes, runs, debugs code in sandboxed environments",
            power_score=99, module="persistent_shell", tags=["python", "sandbox", "debug"]
        ))
        self._register("browser_automation", AbilityInfo(
            name="Browser Automation", tier=4, tier_name="Tool Use & Action",
            category="ACTION", description="Navigates, clicks, fills forms, extracts data from web",
            power_score=93, module="browser_skill", tags=["playwright", "scraping", "web-ui"]
        ))
        self._register("mcp_integration", AbilityInfo(
            name="MCP Tool Integration", tier=4, tier_name="Tool Use & Action",
            category="ACTION", description="Universal connector to external systems via MCP standard",
            power_score=96, module="mcp_integration", tags=["mcp", "apis", "plug-and-play"]
        ))
        self._register("database_ops", AbilityInfo(
            name="Database Operations", tier=4, tier_name="Tool Use & Action",
            category="ACTION", description="SQL, NoSQL, vector DB operations autonomously",
            power_score=87, module="database_ops",
            enabled=settings.enable_database_ops, tags=["sql", "vector-db", "crud"]
        ))

        # ===== TIER 5: Multi-Agent Orchestration =====
        self._register("sub_agent_spawning", AbilityInfo(
            name="Sub-Agent Spawning", tier=5, tier_name="Multi-Agent Orchestration",
            category="SWARM", description="Dynamically creates specialized child agents in parallel",
            power_score=100, module="sub_agents",
            enabled=settings.enable_sub_agents, tags=["parallel", "delegation", "scale"]
        ))
        self._register("hierarchical_coordination", AbilityInfo(
            name="Hierarchical Coordination", tier=5, tier_name="Multi-Agent Orchestration",
            category="SWARM", description="Orchestrates teams of specialist agents in concert",
            power_score=98, module="sub_agents",
            enabled=settings.enable_sub_agents, tags=["orchestration", "specialist"]
        ))
        self._register("a2a_protocol", AbilityInfo(
            name="Agent-to-Agent Protocol", tier=5, tier_name="Multi-Agent Orchestration",
            category="SWARM", description="Structured inter-agent messaging via A2A standard",
            power_score=91, module="a2a_protocol",
            enabled=settings.enable_swarm, tags=["a2a", "messaging", "discovery"]
        ))
        self._register("swarm_intelligence", AbilityInfo(
            name="Swarm Intelligence", tier=5, tier_name="Multi-Agent Orchestration",
            category="SWARM", description="Decentralized agent cluster with emergent behavior",
            power_score=94, module="swarm_intelligence",
            enabled=settings.enable_swarm, tags=["emergent", "decentralized", "resilient"]
        ))

        # ===== TIER 6: Autonomy & Self-Improvement =====
        self._register("autonomous_coding_loop", AbilityInfo(
            name="Autonomous Coding Loop", tier=6, tier_name="Autonomy & Self-Improvement",
            category="ELITE", description="Iterates on code until goal is fully met (Ralph pattern)",
            power_score=97, module="autonomous_loop", tags=["ralph", "self-debug", "loop"]
        ))
        self._register("evaluator_optimizer", AbilityInfo(
            name="Evaluator-Optimizer", tier=6, tier_name="Autonomy & Self-Improvement",
            category="ELITE", description="Generate → Critique → Refine quality assurance loop",
            power_score=93, module="autonomous_loop", tags=["self-critique", "refinement", "quality"]
        ))
        self._register("skill_acquisition", AbilityInfo(
            name="Dynamic Skill Acquisition", tier=6, tier_name="Autonomy & Self-Improvement",
            category="ELITE", description="Discovers, learns, and activates new capability modules",
            power_score=89, module="skill_acquisition",
            enabled=settings.enable_skill_learning, tags=["skills-api", "marketplace", "extensible"]
        ))
        self._register("rl_feedback", AbilityInfo(
            name="RL Feedback Traces", tier=6, tier_name="Autonomy & Self-Improvement",
            category="ELITE", description="Learns from decision outcomes via reinforcement signals",
            power_score=88, module="rl_feedback",
            enabled=settings.enable_rl_feedback, tags=["rl", "learning", "continuous"]
        ))

        # ===== TIER 7: Safety & Governance =====
        self._register("human_gate", AbilityInfo(
            name="Human-in-the-Loop Gates", tier=7, tier_name="Safety & Governance",
            category="SAFE", description="Pauses for human approval before high-stakes actions",
            power_score=85, module="governance",
            enabled=settings.enable_human_gate, tags=["approval", "interrupt", "high-stakes"]
        ))
        self._register("audit_trail", AbilityInfo(
            name="Observability & Audit Trail", tier=7, tier_name="Safety & Governance",
            category="SAFE", description="Logs every decision with timestamps and full context",
            power_score=90, module="governance",
            enabled=settings.enable_audit_trail, tags=["opentelemetry", "audit", "tracing"]
        ))
        self._register("sandbox", AbilityInfo(
            name="Sandboxed Execution", tier=7, tier_name="Safety & Governance",
            category="SAFE", description="Runs code in isolated containers with resource limits",
            power_score=88, module="governance",
            enabled=settings.enable_sandbox, tags=["isolation", "containers", "resource-limits"]
        ))
        self._register("kill_switch", AbilityInfo(
            name="Kill Switch Protocol", tier=7, tier_name="Safety & Governance",
            category="SAFE", description="Emergency halt with state preservation and rollback",
            power_score=86, module="governance",
            enabled=settings.enable_kill_switch, tags=["emergency-stop", "rollback", "state-save"]
        ))

    def _register(self, key: str, ability: AbilityInfo):
        """Register an ability"""
        self._abilities[key] = ability

    # ===== Access Methods =====

    def get_module(self, module_name: str) -> Any:
        """Lazy-load and return a module's primary instance"""
        if module_name in self._modules:
            return self._modules[module_name]

        try:
            if module_name == "cognitive_core":
                from cognitive_core import cognitive_core
                self._modules[module_name] = cognitive_core
            elif module_name == "context_manager":
                from context_manager import context_manager
                self._modules[module_name] = context_manager
            elif module_name == "document_intelligence":
                from document_intelligence import doc_intelligence
                self._modules[module_name] = doc_intelligence
            elif module_name == "environment_sensing":
                from environment_sensing import env_sensor
                self._modules[module_name] = env_sensor
            elif module_name == "database_ops":
                from database_ops import db_ops
                self._modules[module_name] = db_ops
            elif module_name == "swarm_intelligence":
                from swarm_intelligence import swarm
                self._modules[module_name] = swarm
            elif module_name == "a2a_protocol":
                from swarm_intelligence import a2a_protocol
                self._modules[module_name] = a2a_protocol
            elif module_name == "autonomous_loop":
                from autonomous_loop import autonomous_loop
                self._modules[module_name] = autonomous_loop
            elif module_name == "skill_acquisition":
                from skill_acquisition import skill_registry
                self._modules[module_name] = skill_registry
            elif module_name == "rl_feedback":
                from rl_feedback import rl_feedback
                self._modules[module_name] = rl_feedback
            elif module_name == "governance":
                from governance import human_gate, audit_trail, sandbox, kill_switch
                self._modules[module_name] = {
                    "human_gate": human_gate,
                    "audit_trail": audit_trail,
                    "sandbox": sandbox,
                    "kill_switch": kill_switch
                }
            elif module_name == "memory":
                from memory import memory
                self._modules[module_name] = memory
            elif module_name == "vector_memory":
                from vector_memory import get_vector_memory
                self._modules[module_name] = get_vector_memory()
            elif module_name == "sub_agents":
                from sub_agents import orchestrator
                self._modules[module_name] = orchestrator
            elif module_name == "mcp_integration":
                from mcp_integration import mcp
                self._modules[module_name] = mcp
            elif module_name == "browser_skill":
                from browser_skill import browser_skill
                self._modules[module_name] = browser_skill
            elif module_name == "persistent_shell":
                from persistent_shell import shell_manager
                self._modules[module_name] = shell_manager
            elif module_name == "vision_analysis":
                from vision_analysis import vision_analyzer
                self._modules[module_name] = vision_analyzer
            else:
                logger.warning(f"Unknown module: {module_name}")
                return None

        except ImportError as e:
            logger.warning(f"Module {module_name} not available: {e}")
            return None

        return self._modules.get(module_name)

    def get_ability(self, key: str) -> Optional[AbilityInfo]:
        """Get ability info by key"""
        return self._abilities.get(key)

    def get_abilities_by_tier(self, tier: int) -> List[AbilityInfo]:
        """Get all abilities in a specific tier"""
        return [a for a in self._abilities.values() if a.tier == tier]

    def get_enabled_abilities(self) -> List[AbilityInfo]:
        """Get all enabled abilities"""
        return [a for a in self._abilities.values() if a.enabled]

    def get_abilities_by_category(self, category: str) -> List[AbilityInfo]:
        """Get abilities by category"""
        return [a for a in self._abilities.values() if a.category == category]

    # ===== Status & Dashboard =====

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all abilities"""
        tier_names = {
            1: "Cognitive Core",
            2: "Memory Systems",
            3: "Perception",
            4: "Tool Use & Action",
            5: "Multi-Agent Orchestration",
            6: "Autonomy & Self-Improvement",
            7: "Safety & Governance"
        }

        tiers = {}
        for tier_num, tier_name in tier_names.items():
            tier_abilities = self.get_abilities_by_tier(tier_num)
            tiers[f"tier_{tier_num}"] = {
                "name": tier_name,
                "abilities": [
                    {
                        "name": a.name,
                        "category": a.category,
                        "power_score": a.power_score,
                        "enabled": a.enabled,
                        "tags": a.tags
                    }
                    for a in tier_abilities
                ],
                "total": len(tier_abilities),
                "enabled": len([a for a in tier_abilities if a.enabled])
            }

        total = len(self._abilities)
        enabled = len([a for a in self._abilities.values() if a.enabled])
        avg_power = sum(a.power_score for a in self._abilities.values()) / max(total, 1)

        return {
            "total_abilities": total,
            "enabled_abilities": enabled,
            "total_tiers": len(tier_names),
            "average_power_score": round(avg_power, 1),
            "autonomy_level": "L6",
            "tiers": tiers
        }

    def get_dashboard(self) -> str:
        """Get a formatted text dashboard of all abilities"""
        status = self.get_status()

        lines = [
            "╔══════════════════════════════════════════════════════════╗",
            "║           BIG HOMIE ABILITIES DASHBOARD                 ║",
            "╠══════════════════════════════════════════════════════════╣",
            f"║  Total Abilities: {status['total_abilities']:>3}    Enabled: {status['enabled_abilities']:>3}              ║",
            f"║  Power Tiers: {status['total_tiers']}        Avg Power: {status['average_power_score']:.0f}             ║",
            f"║  Autonomy Level: {status['autonomy_level']}                                  ║",
            "╠══════════════════════════════════════════════════════════╣",
        ]

        for tier_key, tier_data in status["tiers"].items():
            tier_num = tier_key.split("_")[1]
            lines.append(
                f"║  TIER {tier_num}: {tier_data['name']:<35} "
                f"[{tier_data['enabled']}/{tier_data['total']}] ║"
            )
            for ability in tier_data["abilities"]:
                status_icon = "✅" if ability["enabled"] else "❌"
                lines.append(
                    f"║    {status_icon} {ability['name']:<40} "
                    f"P:{ability['power_score']:>3} ║"
                )

        lines.append("╚══════════════════════════════════════════════════════════╝")

        return "\n".join(lines)


# Global registry instance
abilities = AbilitiesRegistry()
