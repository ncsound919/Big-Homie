"""
Vector Memory System using ChromaDB
Enables semantic search and retrieval of past conversations, skills, and knowledge
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from loguru import logger
from config import settings


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
    """
    Split long text into overlapping chunks for better retrieval precision.

    Args:
        text: The text to split
        chunk_size: Maximum number of characters per chunk
        overlap: Number of overlapping characters between consecutive chunks

    Returns:
        List of text chunks
    """
    if not text or chunk_size <= 0:
        return []
    if len(text) <= chunk_size:
        return [text]
    if overlap >= chunk_size:
        overlap = chunk_size // 4

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = end - overlap
    return chunks

@dataclass
class MemoryEntry:
    """A single memory entry"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    timestamp: Optional[datetime] = None

class VectorMemory:
    """
    Vector-based semantic memory system

    Features:
    - Semantic search across all past interactions
    - Automatic embedding generation
    - Thread isolation (separate collections per context)
    - Efficient similarity retrieval
    """

    def __init__(self, persist_directory: Optional[Path] = None):
        """Initialize vector memory with ChromaDB"""

        self.persist_dir = persist_directory or settings._normalize_path(settings.vector_db_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Initialize embedding model (384-dimensional, fast)
        logger.info("Loading sentence transformer model...")
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Embedding model loaded")

        # Collections for different memory types
        self.conversations = self._get_or_create_collection("conversations")
        self.skills = self._get_or_create_collection("skills")
        self.knowledge = self._get_or_create_collection("knowledge")

        # Thread-specific collections (created on demand)
        self.threads: Dict[str, Any] = {}

    def _get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection"""
        try:
            return self.client.get_collection(name=name)
        except Exception:
            return self.client.create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )

    def get_thread_collection(self, thread_name: str):
        """Get or create a thread-specific collection"""
        if thread_name not in self.threads:
            collection_name = f"thread_{thread_name}"
            self.threads[thread_name] = self._get_or_create_collection(collection_name)
        return self.threads[thread_name]

    def add_conversation(
        self,
        content: str,
        role: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Add a conversation turn to memory

        Args:
            content: The message content
            role: user, assistant, or system
            metadata: Additional metadata (task_type, cost, etc.)

        Returns:
            Memory entry ID
        """
        entry_id = f"conv_{datetime.now().timestamp()}"

        # Generate embedding
        embedding = self.embedder.encode(content).tolist()

        # Prepare metadata
        meta = metadata or {}
        meta.update({
            "role": role,
            "timestamp": datetime.now().isoformat(),
            "type": "conversation",
            "importance_score": meta.get("importance_score", 0.5),
            "access_count": meta.get("access_count", 0),
            "last_accessed": meta.get("last_accessed", datetime.now().isoformat()),
        })

        # Store in ChromaDB
        self.conversations.add(
            ids=[entry_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[meta]
        )

        logger.debug(f"Added conversation memory: {entry_id}")
        return entry_id

    def add_skill(
        self,
        name: str,
        description: str,
        workflow: List[Dict],
        success_rate: float = 0.0
    ) -> str:
        """
        Add a learned skill to memory

        Args:
            name: Skill name
            description: What the skill does
            workflow: Sequence of steps
            success_rate: Historical success rate

        Returns:
            Memory entry ID
        """
        entry_id = f"skill_{name}"

        # Create searchable content
        content = f"{name}: {description}\nWorkflow: {workflow}"

        # Generate embedding
        embedding = self.embedder.encode(content).tolist()

        # Store metadata
        meta = {
            "name": name,
            "description": description,
            "success_rate": success_rate,
            "timestamp": datetime.now().isoformat(),
            "type": "skill",
            "importance_score": 0.5,
            "access_count": 0,
            "last_accessed": datetime.now().isoformat(),
        }

        self.skills.upsert(  # Upsert to update existing skills
            ids=[entry_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[meta]
        )

        logger.info(f"Added/updated skill: {name}")
        return entry_id

    def add_knowledge(
        self,
        content: str,
        category: str,
        source: Optional[str] = None
    ) -> str:
        """
        Add knowledge/fact to memory

        Args:
            content: The knowledge content
            category: Category (e.g., "finance", "coding", "user_preference")
            source: Where this knowledge came from

        Returns:
            Memory entry ID
        """
        entry_id = f"knowledge_{datetime.now().timestamp()}"

        # Generate embedding
        embedding = self.embedder.encode(content).tolist()

        # Store metadata
        meta = {
            "category": category,
            "source": source or "unknown",
            "timestamp": datetime.now().isoformat(),
            "type": "knowledge",
            "importance_score": 0.5,
            "access_count": 0,
            "last_accessed": datetime.now().isoformat(),
        }

        self.knowledge.add(
            ids=[entry_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[meta]
        )

        logger.debug(f"Added knowledge: {category}")
        return entry_id

    def add_to_thread(
        self,
        thread_name: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Add memory to a specific thread (e.g., "coding", "research", "logistics")

        Thread isolation ensures different contexts don't pollute each other
        """
        collection = self.get_thread_collection(thread_name)
        entry_id = f"{thread_name}_{datetime.now().timestamp()}"

        embedding = self.embedder.encode(content).tolist()

        meta = metadata or {}
        meta.update({
            "thread": thread_name,
            "timestamp": datetime.now().isoformat(),
            "importance_score": meta.get("importance_score", 0.5),
            "access_count": meta.get("access_count", 0),
            "last_accessed": meta.get("last_accessed", datetime.now().isoformat()),
        })

        collection.add(
            ids=[entry_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[meta]
        )

        logger.debug(f"Added to thread '{thread_name}': {entry_id}")
        return entry_id

    def search_conversations(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Semantic search across conversation history

        Args:
            query: Search query
            n_results: Number of results to return
            filter_metadata: Filter by metadata (e.g., {"role": "assistant"})

        Returns:
            List of matching conversation entries
        """
        query_embedding = self.embedder.encode(query).tolist()

        results = self.conversations.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata
        )

        return self._format_results(results, collection=self.conversations)

    def search_skills(
        self,
        query: str,
        n_results: int = 3
    ) -> List[Dict]:
        """
        Find relevant skills for a task

        Args:
            query: Task description
            n_results: Number of skills to return

        Returns:
            List of relevant skills with success rates
        """
        query_embedding = self.embedder.encode(query).tolist()

        results = self.skills.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        return self._format_results(results, collection=self.skills)

    def search_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict]:
        """
        Search knowledge base

        Args:
            query: What to search for
            category: Optional category filter
            n_results: Number of results

        Returns:
            List of relevant knowledge entries
        """
        query_embedding = self.embedder.encode(query).tolist()

        where = {"category": category} if category else None

        results = self.knowledge.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )

        return self._format_results(results, collection=self.knowledge)

    def search_thread(
        self,
        thread_name: str,
        query: str,
        n_results: int = 5
    ) -> List[Dict]:
        """
        Search within a specific thread

        Useful for finding relevant context within isolated workstreams
        """
        if thread_name not in self.threads:
            return []

        collection = self.get_thread_collection(thread_name)
        query_embedding = self.embedder.encode(query).tolist()

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        return self._format_results(results, collection=collection)

    def _format_results(self, chroma_results: Dict, collection=None) -> List[Dict]:
        """Format ChromaDB results into clean list, boosted by importance score"""
        if not chroma_results["ids"] or not chroma_results["ids"][0]:
            return []

        formatted = []
        for i in range(len(chroma_results["ids"][0])):
            entry = {
                "id": chroma_results["ids"][0][i],
                "content": chroma_results["documents"][0][i],
                "metadata": chroma_results["metadatas"][0][i],
                "distance": chroma_results["distances"][0][i] if "distances" in chroma_results else None,
            }
            # Compute importance-boosted score (lower distance = better match)
            importance = float(entry["metadata"].get("importance_score", 0.5))
            if entry["distance"] is not None:
                entry["boosted_score"] = entry["distance"] * (1.0 - 0.5 * importance)
            else:
                entry["boosted_score"] = None
            formatted.append(entry)

        # Sort by boosted_score (ascending — lower is better) when available
        if formatted and formatted[0]["boosted_score"] is not None:
            formatted.sort(key=lambda x: x["boosted_score"])

        # Update access tracking for returned results
        if collection is not None:
            self._update_access_metadata(collection, formatted)

        return formatted

    def _update_access_metadata(self, collection, results: List[Dict]):
        """Update access_count and last_accessed for retrieved results"""
        now = datetime.now().isoformat()
        ids = []
        updated_metas = []
        for r in results:
            meta = dict(r["metadata"])
            meta["access_count"] = int(meta.get("access_count", 0)) + 1
            meta["last_accessed"] = now
            ids.append(r["id"])
            updated_metas.append(meta)
            # Also update the in-place metadata so callers see current values
            r["metadata"] = meta
        if ids:
            try:
                collection.update(ids=ids, metadatas=updated_metas)
            except Exception as e:
                logger.warning(f"Failed to update access metadata: {e}")

    def decay_memories(self, decay_rate: float = 0.01, archive_threshold: float = 0.1) -> List[str]:
        """
        Reduce importance_score over time for all memories.

        Memories accessed more frequently or recently decay slower.
        Memories whose importance_score drops below archive_threshold
        are flagged for archival (returned as a list of IDs).

        Args:
            decay_rate: Base rate to reduce importance per call (0.0-1.0)
            archive_threshold: Importance below which memories are flagged

        Returns:
            List of memory IDs flagged for archival
        """
        flagged: List[str] = []
        now = datetime.now()

        for collection in [self.conversations, self.skills, self.knowledge,
                           *self.threads.values()]:
            all_items = collection.get(include=["metadatas"])
            if not all_items["ids"]:
                continue

            ids_to_update: List[str] = []
            metas_to_update: List[Dict] = []

            for idx, entry_id in enumerate(all_items["ids"]):
                meta = dict(all_items["metadatas"][idx])
                importance = float(meta.get("importance_score", 0.5))
                access_count = int(meta.get("access_count", 0))

                # Reduce effective decay for frequently-accessed memories
                access_shield = min(access_count * 0.002, 0.5)
                effective_decay = max(decay_rate - access_shield, 0.0)

                # Reduce effective decay for recently-accessed memories
                last_accessed_str = meta.get("last_accessed")
                if last_accessed_str:
                    try:
                        last_accessed = datetime.fromisoformat(last_accessed_str)
                        hours_since = (now - last_accessed).total_seconds() / 3600
                        if hours_since < 24:
                            effective_decay *= 0.5
                    except (ValueError, TypeError):
                        pass

                new_importance = max(importance - effective_decay, 0.0)
                meta["importance_score"] = round(new_importance, 4)

                if new_importance < archive_threshold:
                    meta["flagged_for_archival"] = "true"
                    flagged.append(entry_id)

                ids_to_update.append(entry_id)
                metas_to_update.append(meta)

            if ids_to_update:
                try:
                    collection.update(ids=ids_to_update, metadatas=metas_to_update)
                except Exception as e:
                    logger.warning(f"Failed to decay memories in collection: {e}")

        logger.info(f"Decayed memories. {len(flagged)} flagged for archival.")
        return flagged

    def store_with_chunking(
        self,
        content: str,
        collection_name: str = "knowledge",
        metadata: Optional[Dict] = None,
        chunk_size: int = 512,
        overlap: int = 50,
    ) -> List[str]:
        """
        Automatically chunk long text and store each chunk as a separate memory.

        Args:
            content: The full text to store
            collection_name: Target collection ("conversations", "skills", "knowledge")
            metadata: Shared metadata applied to every chunk
            chunk_size: Characters per chunk
            overlap: Overlap between consecutive chunks

        Returns:
            List of stored memory entry IDs
        """
        chunks = chunk_text(content, chunk_size=chunk_size, overlap=overlap)
        if not chunks:
            return []

        collection_map = {
            "conversations": self.conversations,
            "skills": self.skills,
            "knowledge": self.knowledge,
        }
        collection = collection_map.get(collection_name, self.knowledge)

        entry_ids = []
        base_ts = datetime.now().timestamp()
        for i, chunk in enumerate(chunks):
            entry_id = f"{collection_name}_chunk_{base_ts}_{i}"
            embedding = self.embedder.encode(chunk).tolist()

            meta = dict(metadata) if metadata else {}
            meta.update({
                "timestamp": datetime.now().isoformat(),
                "type": collection_name,
                "importance_score": meta.get("importance_score", 0.5),
                "access_count": 0,
                "last_accessed": datetime.now().isoformat(),
                "chunk_index": i,
                "total_chunks": len(chunks),
                "is_chunked": "true",
            })

            collection.add(
                ids=[entry_id],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[meta],
            )
            entry_ids.append(entry_id)

        logger.info(f"Stored {len(entry_ids)} chunks in '{collection_name}'")
        return entry_ids

    def search(
        self,
        query: str,
        collection_name: str = "knowledge",
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Unified search across a named collection with importance boosting
        and automatic access tracking.

        Args:
            query: Search query
            collection_name: Which collection to search
            n_results: Max results to return
            filter_metadata: Optional metadata filter

        Returns:
            List of results sorted by importance-boosted relevance
        """
        collection_map = {
            "conversations": self.conversations,
            "skills": self.skills,
            "knowledge": self.knowledge,
        }
        collection = collection_map.get(collection_name, self.knowledge)

        query_embedding = self.embedder.encode(query).tolist()

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata,
        )

        return self._format_results(results, collection=collection)

    def get_recent_context(
        self,
        limit: int = 10,
        thread: Optional[str] = None
    ) -> List[Dict]:
        """
        Get recent conversation context

        Args:
            limit: Number of recent entries
            thread: Optional thread filter

        Returns:
            Recent conversation entries
        """
        collection = self.get_thread_collection(thread) if thread else self.conversations

        # Fetch all items so we can sort by timestamp and return the truly most-recent ones.
        # ChromaDB's get() has no ordering guarantee, so fetching only `limit` items can
        # silently omit newer entries.
        all_results = collection.get(
            include=["documents", "metadatas"]
        )

        if not all_results["ids"]:
            return []

        # Convert to list of dicts
        entries = [
            {
                "id": all_results["ids"][i],
                "content": all_results["documents"][i],
                "metadata": all_results["metadatas"][i]
            }
            for i in range(len(all_results["ids"]))
        ]

        # Sort by timestamp (most recent first) then return top `limit`
        entries.sort(
            key=lambda x: x["metadata"].get("timestamp", ""),
            reverse=True
        )

        return entries[:limit]

    def clear_thread(self, thread_name: str):
        """Clear all memories from a specific thread"""
        if thread_name in self.threads:
            collection = self.get_thread_collection(thread_name)
            self.client.delete_collection(f"thread_{thread_name}")
            del self.threads[thread_name]
            logger.info(f"Cleared thread: {thread_name}")

    def get_stats(self) -> Dict:
        """Get memory statistics"""
        return {
            "conversations": self.conversations.count(),
            "skills": self.skills.count(),
            "knowledge": self.knowledge.count(),
            "threads": {
                name: collection.count()
                for name, collection in self.threads.items()
            },
            "total_entries": (
                self.conversations.count() +
                self.skills.count() +
                self.knowledge.count() +
                sum(c.count() for c in self.threads.values())
            )
        }

# Global vector memory instance (lazily initialized to avoid heavy import-time work)
_vector_memory_instance: Optional[VectorMemory] = None

def get_vector_memory() -> VectorMemory:
    """Get the shared VectorMemory instance, creating it on first use."""
    global _vector_memory_instance
    if _vector_memory_instance is None:
        _vector_memory_instance = VectorMemory()
    return _vector_memory_instance

class _LazyVectorMemoryProxy:
    """Proxy that defers VectorMemory initialization until first attribute access."""

    def __getattr__(self, name: str):
        return getattr(get_vector_memory(), name)

vector_memory = _LazyVectorMemoryProxy()
