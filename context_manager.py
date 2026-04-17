"""
Context Window Manager - Tier 2 Memory System
Intelligent context trimming, summarization, and compression
with sliding-window summarization and working memory tier.
"""

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from loguru import logger


@dataclass
class ContextBlock:
    """A block of context with metadata for importance scoring"""

    content: str
    role: str
    token_count: int
    timestamp: str
    importance: float = 0.5
    is_summary: bool = False
    original_message_count: int = 1


@dataclass
class ContextState:
    """Current state of the managed context window"""

    blocks: list[ContextBlock]
    total_tokens: int
    max_tokens: int
    compression_ratio: float
    summaries_created: int


@dataclass
class WorkingMemoryItem:
    """A single item in working memory with importance and TTL metadata."""

    key: str
    value: Any
    importance: float  # 0.0-1.0
    created_at: str
    last_accessed: str
    access_count: int = 0
    ttl_seconds: Optional[int] = None


class WorkingMemory:
    """
    Short-term working memory tier that sits between the live conversation
    and long-term vector/database storage.  Items are scored by importance
    and automatically evicted when they expire or capacity is reached.
    """

    def __init__(self, max_items: int = 50):
        self.items: dict[str, WorkingMemoryItem] = {}
        self.max_items = max_items

    def store(
        self,
        key: str,
        value: Any,
        importance: float = 0.5,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """Store or update an item in working memory."""
        now = datetime.now(timezone.utc).isoformat()
        importance = max(0.0, min(1.0, importance))

        if key in self.items:
            item = self.items[key]
            item.value = value
            item.importance = importance
            item.last_accessed = now
            item.access_count += 1
            if ttl_seconds is not None:
                item.ttl_seconds = ttl_seconds
        else:
            self.evict_expired()
            if len(self.items) >= self.max_items:
                self.evict_lowest()
            self.items[key] = WorkingMemoryItem(
                key=key,
                value=value,
                importance=importance,
                created_at=now,
                last_accessed=now,
                access_count=0,
                ttl_seconds=ttl_seconds,
            )

    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve a value by key, updating access metadata."""
        self.evict_expired()
        item = self.items.get(key)
        if item is None:
            return None
        item.last_accessed = datetime.now(timezone.utc).isoformat()
        item.access_count += 1
        return item.value

    def get_context_block(self) -> str:
        """Format all working-memory items as a context block for the LLM."""
        self.evict_expired()
        if not self.items:
            return ""

        sorted_items = sorted(
            self.items.values(),
            key=lambda it: it.importance,
            reverse=True,
        )
        lines = ["[Working Memory]"]
        for item in sorted_items:
            val_repr = str(item.value)
            if len(val_repr) > 200:
                val_repr = val_repr[:200] + "..."
            lines.append(
                f"- {item.key} (importance={item.importance:.2f}, "
                f"accesses={item.access_count}): {val_repr}"
            )
        return "\n".join(lines)

    def evict_expired(self) -> None:
        """Remove items whose TTL has elapsed."""
        now = datetime.now(timezone.utc)
        expired_keys = []
        for key, item in self.items.items():
            if item.ttl_seconds is not None:
                created = datetime.fromisoformat(item.created_at)
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
                elapsed = (now - created).total_seconds()
                if elapsed >= item.ttl_seconds:
                    expired_keys.append(key)
        for key in expired_keys:
            del self.items[key]

    def evict_lowest(self) -> None:
        """Remove the lowest-importance item to free capacity."""
        if not self.items:
            return
        lowest_key = min(
            self.items,
            key=lambda k: (self.items[k].importance, self.items[k].access_count),
        )
        del self.items[lowest_key]


class ContextWindowManager:
    """
    Intelligently manages the context window to prevent "context rot"
    while preserving the most relevant information.

    Features:
    - Token-aware context tracking
    - Importance-based message retention
    - Automatic summarization of old messages
    - Sliding window with smart compression
    - Preserves system prompts and recent exchanges
    """

    def __init__(self, max_context_tokens: int = 100000):
        self.max_context_tokens = max_context_tokens
        self.reserve_tokens = 4096  # Reserve for output
        self.effective_limit = max_context_tokens - self.reserve_tokens
        self.summaries_created = 0
        self._cost_guard = None
        self.working_memory = WorkingMemory()

    def _get_cost_guard(self):
        """Lazy-load cost guard for token counting"""
        if self._cost_guard is None:
            from cost_guards import cost_guard

            self._cost_guard = cost_guard
        return self._cost_guard

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return self._get_cost_guard().count_tokens(text)

    # ------------------------------------------------------------------
    # Sliding-window summarization
    # ------------------------------------------------------------------

    async def _summarize_window(
        self,
        messages: list[dict],
        llm=None,
    ) -> str:
        """
        Produce a concise summary of a chunk of messages.

        If an LLM gateway instance is provided (or can be imported), it is
        used to generate an abstractive summary.  Otherwise we fall back to
        extractive summarization (picking key sentences from the content).
        """

        # ---- build raw text from the messages ----
        raw_parts: list[str] = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            raw_parts.append(f"{role}: {content}")
        raw_text = "\n".join(raw_parts)

        # ---- attempt LLM-based abstractive summary ----
        gateway = llm
        if gateway is None:
            try:
                from llm_gateway import LLMGateway

                gateway = LLMGateway()
            except Exception:
                gateway = None

        if gateway is not None:
            try:
                prompt = (
                    "Summarize the following conversation excerpt in 2-4 concise "
                    "sentences.  Preserve any decisions, facts, code references, "
                    "and action items.\n\n" + raw_text
                )
                result = await gateway.complete(
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=256,
                )
                summary = result.get("content", "").strip()
                if summary:
                    return summary
            except Exception as exc:
                logger.debug(f"LLM summarization failed, using extractive: {exc}")

        # ---- fallback: extractive summarization ----
        return self._extractive_summary(raw_text)

    @staticmethod
    def _extractive_summary(text: str, max_sentences: int = 5) -> str:
        """Pick the most informative sentences from *text*."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        if not sentences:
            return "Previous conversation context"

        scored: list[tuple[str, float]] = []
        importance_words = {
            "important",
            "critical",
            "must",
            "error",
            "decision",
            "conclusion",
            "result",
            "answer",
            "plan",
            "goal",
            "code",
            "fix",
            "deploy",
            "build",
            "issue",
        }
        for sent in sentences:
            if len(sent.strip()) < 10:
                continue
            score = 0.0
            lower = sent.lower()
            score += sum(0.15 for w in importance_words if w in lower)
            if "```" in sent or "http" in sent:
                score += 0.2
            # Prefer medium-length sentences
            word_count = len(sent.split())
            if 5 <= word_count <= 40:
                score += 0.1
            scored.append((sent.strip(), score))

        scored.sort(key=lambda x: x[1], reverse=True)
        picked = [s for s, _ in scored[:max_sentences]]
        return " | ".join(picked) if picked else "Previous conversation context"

    def manage_context(
        self, messages: list[dict[str, str]], max_tokens: Optional[int] = None
    ) -> list[dict[str, str]]:
        """
        Main entry point: manage a conversation's context window.

        Applies intelligent trimming and summarization to keep the context
        within token limits while preserving the most important information.

        Args:
            messages: Full conversation history
            max_tokens: Override max token limit

        Returns:
            Optimized message list within token limits
        """
        limit = max_tokens or self.effective_limit

        # Calculate current token usage
        total_tokens = sum(self.count_tokens(m.get("content", "")) for m in messages)

        if total_tokens <= limit:
            return messages  # No management needed

        logger.info(f"Context management triggered: {total_tokens} tokens > {limit} limit")

        # Strategy 1: Separate messages by role importance
        system_messages = [m for m in messages if m.get("role") == "system"]
        conversation = [m for m in messages if m.get("role") != "system"]

        # Always preserve system messages
        system_tokens = sum(self.count_tokens(m.get("content", "")) for m in system_messages)
        remaining_budget = limit - system_tokens

        # Handle case where system messages alone exceed the limit
        if remaining_budget <= 0:
            logger.warning(
                f"System messages ({system_tokens} tokens) exceed context limit ({limit}). "
                f"Truncating system messages to fit."
            )
            # Keep system messages but cap them; preserve at least some conversation
            min_conversation_budget_ratio = 0.1  # Reserve 10% of limit for conversation
            min_conversation_tokens = 512  # Absolute minimum conversation budget
            remaining_budget = max(
                int(limit * min_conversation_budget_ratio), min_conversation_tokens
            )
            # Trim system messages to leave room
            system_budget = limit - remaining_budget
            trimmed_system = []
            used = 0
            for m in system_messages:
                m_tokens = self.count_tokens(m.get("content", ""))
                if used + m_tokens <= system_budget:
                    trimmed_system.append(m)
                    used += m_tokens
                else:
                    # Summarize remaining system content
                    content = m.get("content", "")
                    available_chars = max(
                        100, int((system_budget - used) * 3)
                    )  # ~3 chars/token estimate
                    trimmed = {**m, "content": content[:available_chars] + "... [truncated]"}
                    trimmed_system.append(trimmed)
                    break
            system_messages = trimmed_system

        # Strategy 2: Score and prioritize messages
        scored = self._score_messages(conversation)

        # Strategy 3: Apply compression strategy
        optimized = self._compress_context(scored, remaining_budget)

        # Include working-memory context if available
        wm_block = self.working_memory.get_context_block()
        wm_messages: list[dict[str, str]] = []
        if wm_block:
            wm_tokens = self.count_tokens(wm_block)
            total_optimized = sum(self.count_tokens(m.get("content", "")) for m in optimized)
            budget_remaining = remaining_budget - total_optimized
            if budget_remaining >= wm_tokens:
                wm_messages = [{"role": "system", "content": wm_block}]
            else:
                logger.debug("Working-memory block skipped: would exceed token budget")

        # Rebuild message list
        result = system_messages + wm_messages + optimized

        final_tokens = sum(self.count_tokens(m.get("content", "")) for m in result)
        logger.info(
            f"Context optimized: {total_tokens} → {final_tokens} tokens "
            f"({((total_tokens - final_tokens) / total_tokens * 100):.1f}% reduction)"
        )

        return result

    def _score_messages(self, messages: list[dict]) -> list[tuple[dict, float]]:
        """Score messages by importance for retention priority"""
        scored = []
        total = len(messages)

        for i, msg in enumerate(messages):
            score = 0.5  # Base score
            content = msg.get("content", "")
            role = msg.get("role", "")

            # Recency boost (newer messages are more important)
            recency = (i + 1) / total
            score += recency * 0.3

            # Role-based scoring
            if role == "user":
                score += 0.1  # User messages slightly more important
            if role == "assistant" and i == total - 1:
                score += 0.2  # Last assistant message is important

            # Content-based scoring
            content_lower = content.lower()

            # Important content indicators
            important_indicators = [
                "important",
                "critical",
                "must",
                "required",
                "error",
                "decision",
                "conclusion",
                "summary",
                "result",
                "answer",
            ]
            for indicator in important_indicators:
                if indicator in content_lower:
                    score += 0.05

            # Code blocks are important
            if "```" in content:
                score += 0.15

            # URLs and references
            if "http" in content or "file:" in content:
                score += 0.05

            # Length penalty for very long messages (they're expensive)
            tokens = self.count_tokens(content)
            if tokens > 2000:
                score -= 0.1

            scored.append((msg, min(1.0, max(0.0, score))))

        return scored

    def _compress_context(
        self, scored_messages: list[tuple[dict, float]], token_budget: int
    ) -> list[dict]:
        """Compress context to fit within token budget"""
        if not scored_messages:
            return []

        # Always keep the last few exchanges (critical for coherence)
        preserve_last = min(6, len(scored_messages))
        preserved = [m for m, _ in scored_messages[-preserve_last:]]
        preserved_tokens = sum(self.count_tokens(m.get("content", "")) for m in preserved)

        remaining_budget = token_budget - preserved_tokens

        if remaining_budget <= 0:
            # Even preserved messages exceed budget, truncate them
            return self._truncate_messages(preserved, token_budget)

        # Older messages to potentially summarize or drop
        older = scored_messages[:-preserve_last]

        if not older:
            return preserved

        # Group older messages into chunks for summarization
        chunks = self._chunk_messages(older, chunk_size=8)

        summaries = []
        for chunk in chunks:
            chunk_tokens = sum(self.count_tokens(m.get("content", "")) for m, _ in chunk)

            if remaining_budget <= 0:
                break

            # Create summary of the chunk
            summary = self._create_local_summary(chunk)
            summary_tokens = self.count_tokens(summary)

            if summary_tokens < chunk_tokens and summary_tokens <= remaining_budget:
                summaries.append({"role": "system", "content": f"[Context Summary] {summary}"})
                remaining_budget -= summary_tokens
                self.summaries_created += 1
            elif remaining_budget >= chunk_tokens:
                # Keep original if summary wouldn't save space
                for msg, _ in chunk:
                    summaries.append(msg)
                remaining_budget -= chunk_tokens

        return summaries + preserved

    def _create_local_summary(self, messages: list[tuple[dict, float]]) -> str:
        """Create a concise summary of a group of messages"""
        key_points = []

        for msg, _score in messages:
            content = msg.get("content", "")
            role = msg.get("role", "user")

            # Extract key points based on role
            if role == "user":
                # Summarize user requests
                if len(content) > 100:
                    key_points.append(f"User asked about: {content[:100]}...")
                else:
                    key_points.append(f"User: {content}")
            elif role == "assistant":
                # Summarize assistant responses
                if "```" in content:
                    key_points.append("Assistant provided code")
                elif len(content) > 200:
                    key_points.append(f"Assistant responded: {content[:150]}...")
                else:
                    key_points.append(f"Assistant: {content}")

        summary = " | ".join(key_points[:5])
        return summary if summary else "Previous conversation context"

    def _chunk_messages(
        self, messages: list[tuple[dict, float]], chunk_size: int = 8
    ) -> list[list[tuple[dict, float]]]:
        """Split messages into chunks for batch processing"""
        return [messages[i : i + chunk_size] for i in range(0, len(messages), chunk_size)]

    def _truncate_messages(self, messages: list[dict], token_budget: int) -> list[dict]:
        """Truncate messages to fit within budget, keeping newest"""
        result = []
        tokens_used = 0

        for msg in reversed(messages):
            msg_tokens = self.count_tokens(msg.get("content", ""))
            if tokens_used + msg_tokens <= token_budget:
                result.insert(0, msg)
                tokens_used += msg_tokens
            else:
                # Truncate this message to fit remaining budget
                remaining = token_budget - tokens_used
                if remaining > 100:  # Only include if meaningful
                    content = msg.get("content", "")
                    # Rough truncation (4 chars per token approximation)
                    truncated = content[: remaining * 4]
                    result.insert(
                        0,
                        {"role": msg.get("role", "user"), "content": truncated + "... [truncated]"},
                    )
                break

        return result

    def get_state(self, messages: list[dict]) -> ContextState:
        """Get current context window state"""
        blocks = []
        total_tokens = 0

        for msg in messages:
            content = msg.get("content", "")
            tokens = self.count_tokens(content)
            total_tokens += tokens

            blocks.append(
                ContextBlock(
                    content=content[:200] + "..." if len(content) > 200 else content,
                    role=msg.get("role", "unknown"),
                    token_count=tokens,
                    timestamp=datetime.now().isoformat(),
                    is_summary="[Context Summary]" in content,
                )
            )

        return ContextState(
            blocks=blocks,
            total_tokens=total_tokens,
            max_tokens=self.effective_limit,
            compression_ratio=total_tokens / self.effective_limit
            if self.effective_limit > 0
            else 0,
            summaries_created=self.summaries_created,
        )


# Global context manager instance
context_manager = ContextWindowManager()
