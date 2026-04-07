"""
Context Window Manager - Tier 2 Memory System
Intelligent context trimming, summarization, and compression
"""
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger
from config import settings


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
    blocks: List[ContextBlock]
    total_tokens: int
    max_tokens: int
    compression_ratio: float
    summaries_created: int


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

    def _get_cost_guard(self):
        """Lazy-load cost guard for token counting"""
        if self._cost_guard is None:
            from cost_guards import cost_guard
            self._cost_guard = cost_guard
        return self._cost_guard

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return self._get_cost_guard().count_tokens(text)

    def manage_context(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None
    ) -> List[Dict[str, str]]:
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

        logger.info(
            f"Context management triggered: {total_tokens} tokens > {limit} limit"
        )

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
            MIN_CONVERSATION_BUDGET_RATIO = 0.1  # Reserve 10% of limit for conversation
            MIN_CONVERSATION_TOKENS = 512  # Absolute minimum conversation budget
            remaining_budget = max(int(limit * MIN_CONVERSATION_BUDGET_RATIO), MIN_CONVERSATION_TOKENS)
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
                    available_chars = max(100, int((system_budget - used) * 3))  # ~3 chars/token estimate
                    trimmed = {**m, "content": content[:available_chars] + "... [truncated]"}
                    trimmed_system.append(trimmed)
                    break
            system_messages = trimmed_system

        # Strategy 2: Score and prioritize messages
        scored = self._score_messages(conversation)

        # Strategy 3: Apply compression strategy
        optimized = self._compress_context(scored, remaining_budget)

        # Rebuild message list
        result = system_messages + optimized

        final_tokens = sum(self.count_tokens(m.get("content", "")) for m in result)
        logger.info(
            f"Context optimized: {total_tokens} → {final_tokens} tokens "
            f"({((total_tokens - final_tokens) / total_tokens * 100):.1f}% reduction)"
        )

        return result

    def _score_messages(self, messages: List[Dict]) -> List[Tuple[Dict, float]]:
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
                "important", "critical", "must", "required", "error",
                "decision", "conclusion", "summary", "result", "answer"
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
        self,
        scored_messages: List[Tuple[Dict, float]],
        token_budget: int
    ) -> List[Dict]:
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
                summaries.append({
                    "role": "system",
                    "content": f"[Context Summary] {summary}"
                })
                remaining_budget -= summary_tokens
                self.summaries_created += 1
            elif remaining_budget >= chunk_tokens:
                # Keep original if summary wouldn't save space
                for msg, _ in chunk:
                    summaries.append(msg)
                remaining_budget -= chunk_tokens

        return summaries + preserved

    def _create_local_summary(self, messages: List[Tuple[Dict, float]]) -> str:
        """Create a concise summary of a group of messages"""
        key_points = []

        for msg, score in messages:
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
        self,
        messages: List[Tuple[Dict, float]],
        chunk_size: int = 8
    ) -> List[List[Tuple[Dict, float]]]:
        """Split messages into chunks for batch processing"""
        return [messages[i:i + chunk_size] for i in range(0, len(messages), chunk_size)]

    def _truncate_messages(
        self,
        messages: List[Dict],
        token_budget: int
    ) -> List[Dict]:
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
                    truncated = content[:remaining * 4]
                    result.insert(0, {
                        "role": msg.get("role", "user"),
                        "content": truncated + "... [truncated]"
                    })
                break

        return result

    def get_state(self, messages: List[Dict]) -> ContextState:
        """Get current context window state"""
        blocks = []
        total_tokens = 0

        for msg in messages:
            content = msg.get("content", "")
            tokens = self.count_tokens(content)
            total_tokens += tokens

            blocks.append(ContextBlock(
                content=content[:200] + "..." if len(content) > 200 else content,
                role=msg.get("role", "unknown"),
                token_count=tokens,
                timestamp=datetime.now().isoformat(),
                is_summary="[Context Summary]" in content
            ))

        return ContextState(
            blocks=blocks,
            total_tokens=total_tokens,
            max_tokens=self.effective_limit,
            compression_ratio=total_tokens / self.effective_limit if self.effective_limit > 0 else 0,
            summaries_created=self.summaries_created
        )


# Global context manager instance
context_manager = ContextWindowManager()
