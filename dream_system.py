"""
autoDream - Background Memory Consolidation Engine
Performs overnight memory reorganization and optimization while the user is offline.

The Dream System operates during idle periods to:
- Consolidate and organize memories
- Identify patterns and connections
- Compress and deduplicate context
- Build and optimize knowledge graphs
- Prune stale or low-value memories
"""
import asyncio
import json
import uuid
from datetime import datetime, timedelta, time as dt_time
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from pathlib import Path
from loguru import logger
from config import settings
from memory import memory


class DreamPhase(str, Enum):
    """Phases of the dream consolidation process"""
    INITIALIZATION = "initialization"
    COLLECTION = "collection"
    ANALYSIS = "analysis"
    CONSOLIDATION = "consolidation"
    COMPRESSION = "compression"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    PRUNING = "pruning"
    FINALIZATION = "finalization"
    COMPLETED = "completed"


class MemoryCluster(str, Enum):
    """Types of memory clusters"""
    FACTS = "facts"
    SKILLS = "skills"
    PREFERENCES = "preferences"
    CONTEXT = "context"
    INTERACTIONS = "interactions"
    INSIGHTS = "insights"


@dataclass
class MemoryNode:
    """A node in the knowledge graph"""
    id: str
    content: str
    category: str
    importance: float
    access_count: int
    connections: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None


@dataclass
class MemoryConnection:
    """A connection between memory nodes"""
    source_id: str
    target_id: str
    relationship: str
    strength: float  # 0.0 to 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DreamCycle:
    """A complete dream consolidation cycle"""
    id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    phase: DreamPhase = DreamPhase.INITIALIZATION
    memories_processed: int = 0
    memories_consolidated: int = 0
    memories_pruned: int = 0
    connections_created: int = 0
    space_saved_bytes: int = 0
    insights_generated: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DreamConfig:
    """Configuration for the dream system"""
    enabled: bool = True
    # Scheduling
    dream_hours_start: dt_time = dt_time(2, 0)   # 2 AM
    dream_hours_end: dt_time = dt_time(5, 0)     # 5 AM
    min_idle_minutes: int = 30  # Minimum idle time before dreaming
    # Consolidation settings
    consolidation_threshold: int = 100  # Min memories before consolidation
    max_memories_per_cycle: int = 500
    importance_decay_rate: float = 0.1  # Per day decay for unused memories
    min_importance_to_keep: float = 1.0  # Minimum importance score
    # Compression settings
    enable_compression: bool = True
    compression_similarity_threshold: float = 0.85
    # Knowledge graph settings
    enable_knowledge_graph: bool = True
    max_connections_per_node: int = 10
    min_connection_strength: float = 0.3
    # Resource limits
    max_cycle_duration_seconds: int = 3600  # 1 hour max
    max_cost_per_cycle: float = 1.0  # USD


class DreamSystem:
    """
    autoDream - Background Memory Consolidation Engine

    Operates during idle/overnight periods to:
    1. Collect all memories from the memory system
    2. Analyze patterns and relationships
    3. Consolidate similar memories
    4. Compress redundant information
    5. Build/update knowledge graph
    6. Prune stale memories
    7. Generate insights
    """

    def __init__(self, config: Optional[DreamConfig] = None):
        self.config = config or DreamConfig()
        self.is_dreaming = False
        self.current_cycle: Optional[DreamCycle] = None
        self.cycle_history: List[DreamCycle] = []

        # Knowledge graph
        self.nodes: Dict[str, MemoryNode] = {}
        self.connections: List[MemoryConnection] = []

        # Caches
        self._memory_cache: Dict[str, Any] = {}
        self._similarity_cache: Dict[Tuple[str, str], float] = {}

        # Router for LLM operations
        self._router = None

        logger.info("autoDream system initialized")

    def _get_router(self):
        """Lazy-load router"""
        if self._router is None:
            from router import router
            self._router = router
        return self._router

    def should_dream(self) -> bool:
        """Check if conditions are right for dreaming"""
        if not self.config.enabled:
            return False

        if self.is_dreaming:
            return False

        now = datetime.now()
        current_time = now.time()

        # Check if within dream hours
        start = self.config.dream_hours_start
        end = self.config.dream_hours_end

        in_dream_hours = False
        if start < end:
            in_dream_hours = start <= current_time < end
        else:  # Crosses midnight
            in_dream_hours = current_time >= start or current_time < end

        if not in_dream_hours:
            return False

        # Check last user activity (from memory preferences)
        last_activity = memory.get_preference("last_user_activity")
        if last_activity:
            try:
                last_time = datetime.fromisoformat(last_activity)
                idle_minutes = (now - last_time).total_seconds() / 60
                if idle_minutes < self.config.min_idle_minutes:
                    return False
            except (ValueError, TypeError):
                pass

        # Check if enough memories to consolidate
        all_memories = memory.search_memory(limit=10)
        if len(all_memories) < 5:  # Need some memories to work with
            return False

        return True

    async def dream(self) -> DreamCycle:
        """
        Execute a complete dream consolidation cycle.

        This is the main entry point for memory consolidation.
        """
        if self.is_dreaming:
            logger.warning("Dream cycle already in progress")
            return self.current_cycle

        self.is_dreaming = True
        self.current_cycle = DreamCycle(
            id=str(uuid.uuid4()),
            started_at=datetime.now()
        )

        logger.info("💤 autoDream: Starting memory consolidation cycle...")

        try:
            # Phase 1: Initialization
            self.current_cycle.phase = DreamPhase.INITIALIZATION
            await self._initialize_cycle()

            # Phase 2: Collection
            self.current_cycle.phase = DreamPhase.COLLECTION
            memories = await self._collect_memories()
            self.current_cycle.memories_processed = len(memories)

            # Phase 3: Analysis
            self.current_cycle.phase = DreamPhase.ANALYSIS
            analysis = await self._analyze_memories(memories)

            # Phase 4: Consolidation
            self.current_cycle.phase = DreamPhase.CONSOLIDATION
            consolidated = await self._consolidate_memories(memories, analysis)
            self.current_cycle.memories_consolidated = consolidated

            # Phase 5: Compression
            if self.config.enable_compression:
                self.current_cycle.phase = DreamPhase.COMPRESSION
                space_saved = await self._compress_memories()
                self.current_cycle.space_saved_bytes = space_saved

            # Phase 6: Knowledge Graph
            if self.config.enable_knowledge_graph:
                self.current_cycle.phase = DreamPhase.KNOWLEDGE_GRAPH
                connections = await self._update_knowledge_graph(memories)
                self.current_cycle.connections_created = connections

            # Phase 7: Pruning
            self.current_cycle.phase = DreamPhase.PRUNING
            pruned = await self._prune_memories()
            self.current_cycle.memories_pruned = pruned

            # Phase 8: Finalization
            self.current_cycle.phase = DreamPhase.FINALIZATION
            await self._finalize_cycle()

            self.current_cycle.phase = DreamPhase.COMPLETED
            self.current_cycle.completed_at = datetime.now()

            # Store cycle results
            self.cycle_history.append(self.current_cycle)
            memory.store(
                key=f"dream_cycle_{self.current_cycle.id}",
                value=self._cycle_to_dict(self.current_cycle),
                category="dream_system",
                importance=6
            )

            logger.info(
                f"💤 autoDream complete: "
                f"processed={self.current_cycle.memories_processed}, "
                f"consolidated={self.current_cycle.memories_consolidated}, "
                f"pruned={self.current_cycle.memories_pruned}"
            )

            return self.current_cycle

        except Exception as e:
            logger.error(f"Dream cycle error: {e}")
            self.current_cycle.errors.append(str(e))
            raise

        finally:
            self.is_dreaming = False
            cycle = self.current_cycle
            self.current_cycle = None
            return cycle

    async def _initialize_cycle(self):
        """Initialize the dream cycle"""
        # Clear caches
        self._memory_cache.clear()
        self._similarity_cache.clear()

        # Record cycle start
        memory.set_preference("last_dream_cycle_start", datetime.now().isoformat())

    async def _collect_memories(self) -> List[Dict[str, Any]]:
        """Collect all memories for processing"""
        memories = []

        # Collect from long-term memory
        all_facts = memory.search_memory(limit=self.config.max_memories_per_cycle)
        memories.extend(all_facts)

        # Collect skills
        skills = memory.list_skills()
        for skill in skills:
            memories.append({
                "key": f"skill_{skill['name']}",
                "value": skill,
                "category": "skill",
                "importance": 7,
                "access_count": skill.get("success_count", 0)
            })

        # Collect task history
        task_history = memory.get_task_history(limit=100)
        for i, task in enumerate(task_history):
            memories.append({
                "key": f"task_history_{i}",
                "value": task,
                "category": "task_history",
                "importance": 4,
                "access_count": 1
            })

        logger.info(f"Collected {len(memories)} memories for processing")
        return memories

    async def _analyze_memories(self, memories: List[Dict]) -> Dict[str, Any]:
        """Analyze patterns and relationships in memories"""
        analysis = {
            "categories": defaultdict(list),
            "importance_distribution": defaultdict(int),
            "access_patterns": defaultdict(int),
            "temporal_patterns": [],
            "potential_clusters": [],
            "redundant_memories": [],
        }

        # Categorize memories
        for mem in memories:
            category = mem.get("category", "general")
            analysis["categories"][category].append(mem["key"])

            importance = mem.get("importance", 5)
            analysis["importance_distribution"][importance] += 1

            access_count = mem.get("access_count", 0)
            if access_count == 0:
                analysis["access_patterns"]["unused"] += 1
            elif access_count < 3:
                analysis["access_patterns"]["low_use"] += 1
            elif access_count < 10:
                analysis["access_patterns"]["moderate_use"] += 1
            else:
                analysis["access_patterns"]["high_use"] += 1

        # Identify potential clusters using LLM
        if len(memories) > 10:
            clusters = await self._identify_clusters(memories[:50])  # Limit for LLM
            analysis["potential_clusters"] = clusters

        # Find potential redundant memories
        analysis["redundant_memories"] = await self._find_redundant(memories)

        return analysis

    async def _identify_clusters(self, memories: List[Dict]) -> List[Dict]:
        """Use LLM to identify memory clusters"""
        memory_summaries = [
            f"- {mem.get('key', 'unknown')}: {str(mem.get('value', ''))[:100]}"
            for mem in memories[:30]
        ]

        prompt = f"""Analyze these memories and identify logical clusters/groups.

Memories:
{chr(10).join(memory_summaries)}

Identify 3-5 clusters of related memories. For each cluster:
1. Give it a name
2. List the memory keys that belong to it
3. Describe what connects them

Respond in JSON:
{{
    "clusters": [
        {{
            "name": "Cluster Name",
            "memory_keys": ["key1", "key2"],
            "description": "What connects these memories"
        }}
    ]
}}"""

        try:
            decision, result = await self._get_router().execute_with_routing(
                task=prompt,
                context={"requires_reasoning": True}
            )

            content = result.get("content", "")
            start = content.find("{")
            end = content.rfind("}") + 1

            if start >= 0 and end > start:
                data = json.loads(content[start:end])
                return data.get("clusters", [])

        except Exception as e:
            logger.warning(f"Cluster identification failed: {e}")

        return []

    async def _find_redundant(self, memories: List[Dict]) -> List[Tuple[str, str]]:
        """Find potentially redundant memories"""
        redundant = []

        # Group by category first
        by_category = defaultdict(list)
        for mem in memories:
            by_category[mem.get("category", "general")].append(mem)

        # Check within categories for similar keys/values
        for category, mems in by_category.items():
            for i, m1 in enumerate(mems):
                for m2 in mems[i+1:]:
                    # Simple similarity check
                    v1 = str(m1.get("value", ""))[:200]
                    v2 = str(m2.get("value", ""))[:200]

                    # Check for high overlap using cached similarity
                    similarity = self._get_cached_similarity(m1["key"], m2["key"], v1, v2)
                    if similarity > self.config.compression_similarity_threshold:
                        redundant.append((m1["key"], m2["key"]))

        return redundant[:20]  # Limit results

    def _get_cached_similarity(self, key1: str, key2: str, v1: str, v2: str) -> float:
        """Get similarity from cache or calculate and cache it"""
        cache_key = (key1, key2) if key1 < key2 else (key2, key1)
        if cache_key in self._similarity_cache:
            return self._similarity_cache[cache_key]

        similarity = self._simple_similarity(v1, v2)
        self._similarity_cache[cache_key] = similarity
        return similarity

    def _simple_similarity(self, s1: str, s2: str) -> float:
        """Calculate simple word overlap similarity"""
        if not s1 or not s2:
            return 0.0

        words1 = set(s1.lower().split())
        words2 = set(s2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    async def _consolidate_memories(
        self,
        memories: List[Dict],
        analysis: Dict[str, Any]
    ) -> int:
        """Consolidate similar memories"""
        consolidated_count = 0

        # Merge redundant memories
        for key1, key2 in analysis.get("redundant_memories", []):
            mem1 = next((m for m in memories if m["key"] == key1), None)
            mem2 = next((m for m in memories if m["key"] == key2), None)

            if mem1 and mem2:
                # Keep the more important/accessed one
                keep = mem1 if (
                    mem1.get("importance", 0) >= mem2.get("importance", 0) and
                    mem1.get("access_count", 0) >= mem2.get("access_count", 0)
                ) else mem2

                remove = mem2 if keep == mem1 else mem1

                # Merge information
                merged_value = {
                    "consolidated_from": [mem1["key"], mem2["key"]],
                    "primary": keep.get("value"),
                    "secondary_notes": str(remove.get("value", ""))[:200],
                    "consolidated_at": datetime.now().isoformat()
                }

                # Update the kept memory
                memory.store(
                    key=keep["key"],
                    value=merged_value,
                    category=keep.get("category", "consolidated"),
                    importance=max(
                        keep.get("importance", 5),
                        remove.get("importance", 5)
                    )
                )

                consolidated_count += 1

        # Consolidate clusters
        for cluster in analysis.get("potential_clusters", []):
            if len(cluster.get("memory_keys", [])) >= 3:
                # Create a cluster summary
                cluster_name = cluster.get("name", "Unnamed Cluster")
                memory.store(
                    key=f"cluster_{cluster_name.lower().replace(' ', '_')}",
                    value={
                        "name": cluster_name,
                        "description": cluster.get("description", ""),
                        "members": cluster.get("memory_keys", []),
                        "created_at": datetime.now().isoformat()
                    },
                    category="memory_cluster",
                    importance=6
                )
                consolidated_count += 1

        return consolidated_count

    async def _compress_memories(self) -> int:
        """Compress memory storage"""
        space_saved = 0

        # Get verbose memories
        all_memories = memory.search_memory(limit=100)

        for mem in all_memories:
            value = mem.get("value")
            if isinstance(value, str) and len(value) > 500:
                # Compress long text memories
                compressed = await self._compress_text(value)
                if len(compressed) < len(value) * 0.7:
                    space_saved += len(value) - len(compressed)
                    memory.store(
                        key=mem["key"],
                        value={
                            "compressed": True,
                            "summary": compressed,
                            "original_length": len(value)
                        },
                        category=mem.get("category", "general"),
                        importance=mem.get("importance", 5)
                    )

        return space_saved

    async def _compress_text(self, text: str) -> str:
        """Compress text using LLM summarization"""
        if len(text) < 300:
            return text

        prompt = f"""Compress this text to its essential information. Keep key facts and remove redundancy.

Text:
{text[:2000]}

Provide a compressed version (max 200 words) that preserves all important information."""

        try:
            decision, result = await self._get_router().execute_with_routing(
                task=prompt,
                context={"simple_task": True}
            )
            return result.get("content", text[:500])

        except Exception as e:
            logger.warning(f"Text compression failed: {e}")
            return text[:500]

    async def _update_knowledge_graph(self, memories: List[Dict]) -> int:
        """Update the knowledge graph with new connections"""
        connections_created = 0

        # Create nodes from memories
        for mem in memories:
            node_id = mem["key"]
            if node_id not in self.nodes:
                self.nodes[node_id] = MemoryNode(
                    id=node_id,
                    content=str(mem.get("value", ""))[:500],
                    category=mem.get("category", "general"),
                    importance=mem.get("importance", 5),
                    access_count=mem.get("access_count", 0)
                )

        # Find connections using LLM
        if len(self.nodes) > 5:
            new_connections = await self._discover_connections(
                list(self.nodes.values())[:30]
            )
            connections_created = len(new_connections)

            for conn in new_connections:
                self.connections.append(conn)

                # Update node connections
                if conn.source_id in self.nodes:
                    self.nodes[conn.source_id].connections.append(conn.target_id)
                if conn.target_id in self.nodes:
                    self.nodes[conn.target_id].connections.append(conn.source_id)

        # Persist knowledge graph
        self._save_knowledge_graph()

        return connections_created

    async def _discover_connections(
        self,
        nodes: List[MemoryNode]
    ) -> List[MemoryConnection]:
        """Use LLM to discover connections between memory nodes"""
        node_summaries = [
            f"- {node.id}: [{node.category}] {node.content[:100]}"
            for node in nodes[:20]
        ]

        prompt = f"""Analyze these memory nodes and identify meaningful connections between them.

Memory Nodes:
{chr(10).join(node_summaries)}

Identify connections where:
- One memory relates to, supports, or extends another
- Memories share common themes or concepts
- One memory provides context for another

List up to 10 connections in JSON:
{{
    "connections": [
        {{
            "source": "node_id_1",
            "target": "node_id_2",
            "relationship": "relates_to|supports|extends|contradicts|provides_context",
            "strength": 0.8,
            "description": "Brief description of relationship"
        }}
    ]
}}"""

        connections = []

        try:
            decision, result = await self._get_router().execute_with_routing(
                task=prompt,
                context={"requires_reasoning": True}
            )

            content = result.get("content", "")
            start = content.find("{")
            end = content.rfind("}") + 1

            if start >= 0 and end > start:
                data = json.loads(content[start:end])

                for conn_data in data.get("connections", []):
                    source = conn_data.get("source", "")
                    target = conn_data.get("target", "")

                    # Validate nodes exist
                    if source in self.nodes and target in self.nodes:
                        connections.append(MemoryConnection(
                            source_id=source,
                            target_id=target,
                            relationship=conn_data.get("relationship", "relates_to"),
                            strength=min(1.0, max(0.0, conn_data.get("strength", 0.5))),
                            metadata={"description": conn_data.get("description", "")}
                        ))

        except Exception as e:
            logger.warning(f"Connection discovery failed: {e}")

        return connections

    async def _prune_memories(self) -> int:
        """Prune stale or low-value memories"""
        pruned_count = 0

        all_memories = memory.search_memory(limit=200)

        for mem in all_memories:
            importance = mem.get("importance", 5)
            access_count = mem.get("access_count", 0)
            category = mem.get("category", "general")

            # Don't prune system categories
            if category in ["skill", "dream_system", "memory_cluster", "preference"]:
                continue

            # Decay importance for unused memories
            if access_count < 2:
                new_importance = max(0, importance - self.config.importance_decay_rate)

                if new_importance < self.config.min_importance_to_keep:
                    # Memory is too low value - mark for potential removal
                    # (we don't actually delete, just mark as archived)
                    memory.store(
                        key=mem["key"],
                        value={
                            "archived": True,
                            "original_value": mem["value"],
                            "archived_at": datetime.now().isoformat(),
                            "reason": "low_importance_decay"
                        },
                        category="archived",
                        importance=0
                    )
                    pruned_count += 1
                elif new_importance < importance:
                    # Just decay importance
                    memory.store(
                        key=mem["key"],
                        value=mem["value"],
                        category=category,
                        importance=int(new_importance)
                    )

        return pruned_count

    async def _finalize_cycle(self):
        """Finalize the dream cycle"""
        # Generate insights from the cycle
        insights = await self._generate_insights()
        self.current_cycle.insights_generated = insights

        # Calculate metrics
        self.current_cycle.metrics = {
            "total_duration_seconds": (
                datetime.now() - self.current_cycle.started_at
            ).total_seconds(),
            "memories_per_second": (
                self.current_cycle.memories_processed /
                max(1, (datetime.now() - self.current_cycle.started_at).total_seconds())
            ),
            "consolidation_ratio": (
                self.current_cycle.memories_consolidated /
                max(1, self.current_cycle.memories_processed)
            ),
            "prune_ratio": (
                self.current_cycle.memories_pruned /
                max(1, self.current_cycle.memories_processed)
            ),
        }

        # Record completion time
        memory.set_preference("last_dream_cycle_complete", datetime.now().isoformat())
        memory.set_preference("last_dream_metrics", self.current_cycle.metrics)

    async def _generate_insights(self) -> List[Dict[str, Any]]:
        """Generate insights from the dream cycle"""
        insights = []

        # Insight: Memory usage patterns
        all_memories = memory.search_memory(limit=50)
        categories = defaultdict(int)
        for mem in all_memories:
            categories[mem.get("category", "general")] += 1

        insights.append({
            "type": "memory_distribution",
            "description": "Memory distribution by category",
            "data": dict(categories)
        })

        # Insight: Knowledge graph density
        if self.nodes:
            avg_connections = sum(
                len(n.connections) for n in self.nodes.values()
            ) / len(self.nodes)

            insights.append({
                "type": "knowledge_graph",
                "description": "Knowledge graph statistics",
                "data": {
                    "total_nodes": len(self.nodes),
                    "total_connections": len(self.connections),
                    "average_connections": round(avg_connections, 2)
                }
            })

        return insights

    def _save_knowledge_graph(self):
        """Save knowledge graph to memory"""
        graph_data = {
            "nodes": {
                nid: {
                    "content": node.content[:200],
                    "category": node.category,
                    "importance": node.importance,
                    "connections": node.connections[:10]
                }
                for nid, node in list(self.nodes.items())[:100]
            },
            "connections_count": len(self.connections),
            "updated_at": datetime.now().isoformat()
        }

        memory.store(
            key="knowledge_graph",
            value=graph_data,
            category="dream_system",
            importance=8
        )

    def _cycle_to_dict(self, cycle: DreamCycle) -> Dict[str, Any]:
        """Convert cycle to dictionary for storage"""
        return {
            "id": cycle.id,
            "started_at": cycle.started_at.isoformat(),
            "completed_at": cycle.completed_at.isoformat() if cycle.completed_at else None,
            "phase": cycle.phase.value,
            "memories_processed": cycle.memories_processed,
            "memories_consolidated": cycle.memories_consolidated,
            "memories_pruned": cycle.memories_pruned,
            "connections_created": cycle.connections_created,
            "space_saved_bytes": cycle.space_saved_bytes,
            "insights_generated": cycle.insights_generated,
            "errors": cycle.errors,
            "metrics": cycle.metrics
        }

    def get_status(self) -> Dict[str, Any]:
        """Get current dream system status"""
        return {
            "enabled": self.config.enabled,
            "is_dreaming": self.is_dreaming,
            "current_phase": self.current_cycle.phase.value if self.current_cycle else None,
            "total_cycles": len(self.cycle_history),
            "knowledge_graph_nodes": len(self.nodes),
            "knowledge_graph_connections": len(self.connections),
            "last_cycle": self.cycle_history[-1].id if self.cycle_history else None,
            "should_dream": self.should_dream()
        }

    def get_knowledge_graph_summary(self) -> Dict[str, Any]:
        """Get a summary of the knowledge graph"""
        if not self.nodes:
            return {"status": "empty", "nodes": 0, "connections": 0}

        # Get most connected nodes
        sorted_nodes = sorted(
            self.nodes.values(),
            key=lambda n: len(n.connections),
            reverse=True
        )[:10]

        return {
            "status": "active",
            "nodes": len(self.nodes),
            "connections": len(self.connections),
            "top_connected_nodes": [
                {
                    "id": n.id,
                    "category": n.category,
                    "connections": len(n.connections)
                }
                for n in sorted_nodes
            ],
            "categories": self._count_node_categories()
        }

    def _count_node_categories(self) -> Dict[str, int]:
        """Count nodes by category"""
        counts: Dict[str, int] = {}
        for node in self.nodes.values():
            category = node.category
            counts[category] = counts.get(category, 0) + 1
        return counts


# Global dream system instance
dream_system = DreamSystem()


async def run_dream_cycle() -> DreamCycle:
    """Convenience function to run a dream cycle"""
    return await dream_system.dream()


def should_dream() -> bool:
    """Check if conditions are right for dreaming"""
    return dream_system.should_dream()
