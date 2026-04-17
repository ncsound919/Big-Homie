"""
Reinforcement Learning Feedback Traces - Tier 6 Self-Improvement
Learn from outcomes of decisions through reinforcement signals
"""

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from config import settings


@dataclass
class FeedbackSignal:
    """A reinforcement signal from a decision outcome"""

    signal_id: str
    decision_context: str
    action_taken: str
    outcome: str  # positive, negative, neutral
    reward: float  # -1.0 to 1.0
    reasoning: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionPattern:
    """A learned pattern from accumulated feedback"""

    pattern_id: str
    context_pattern: str
    recommended_action: str
    average_reward: float
    sample_count: int
    confidence: float
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())


class ReinforcementFeedback:
    """
    Learns from the outcomes of agent decisions through reinforcement signals.

    Good decisions are reinforced, poor ones are penalized,
    compounding performance improvements over time.

    Features:
    - Track decision → outcome pairs
    - Compute reward signals from outcomes
    - Build pattern library of successful strategies
    - Adjust routing and strategy selection based on learned patterns
    - Persistence across sessions via SQLite
    """

    def __init__(self):
        self.db_path = Path(settings.data_dir) / "rl_feedback.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self.session_signals: list[FeedbackSignal] = []
        self._correction_ledger = None

    def _get_correction_ledger(self):
        """Lazy-load the correction ledger to avoid circular imports"""
        if self._correction_ledger is None:
            from correction_ledger import correction_ledger

            self._correction_ledger = correction_ledger
        return self._correction_ledger

    def _conn(self):
        return sqlite3.connect(str(self.db_path))

    def _init_db(self):
        """Initialize the feedback database"""
        with self._conn() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS feedback_signals (
                    signal_id TEXT PRIMARY KEY,
                    decision_context TEXT,
                    action_taken TEXT,
                    outcome TEXT,
                    reward REAL,
                    reasoning TEXT,
                    timestamp TEXT,
                    metadata TEXT
                )
            """)

            db.execute("""
                CREATE TABLE IF NOT EXISTS decision_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    context_pattern TEXT UNIQUE,
                    recommended_action TEXT,
                    average_reward REAL,
                    sample_count INTEGER,
                    confidence REAL,
                    last_updated TEXT
                )
            """)

            db.execute("""
                CREATE TABLE IF NOT EXISTS strategy_scores (
                    strategy TEXT PRIMARY KEY,
                    total_reward REAL DEFAULT 0,
                    usage_count INTEGER DEFAULT 0,
                    average_reward REAL DEFAULT 0,
                    last_used TEXT
                )
            """)

            db.commit()

    # ===== Recording Feedback =====

    def record_feedback(
        self,
        decision_context: str,
        action_taken: str,
        outcome: str,
        reward: float,
        reasoning: str = "",
        metadata: Optional[dict] = None,
    ) -> FeedbackSignal:
        """
        Record a feedback signal for a decision.

        Args:
            decision_context: What the situation was
            action_taken: What action was chosen
            outcome: What happened (positive/negative/neutral)
            reward: Reward value (-1.0 to 1.0)
            reasoning: Why this outcome occurred
            metadata: Additional data

        Returns:
            The recorded FeedbackSignal
        """
        import uuid

        signal = FeedbackSignal(
            signal_id=str(uuid.uuid4()),
            decision_context=decision_context,
            action_taken=action_taken,
            outcome=outcome,
            reward=max(-1.0, min(1.0, reward)),
            reasoning=reasoning,
            metadata=metadata or {},
        )

        # Store in session
        self.session_signals.append(signal)

        # Persist to database
        with self._conn() as db:
            db.execute(
                """INSERT INTO feedback_signals
                   (signal_id, decision_context, action_taken, outcome, reward, reasoning, timestamp, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    signal.signal_id,
                    signal.decision_context,
                    signal.action_taken,
                    signal.outcome,
                    signal.reward,
                    signal.reasoning,
                    signal.timestamp,
                    json.dumps(signal.metadata),
                ),
            )
            db.commit()

        # Update patterns
        self._update_patterns(signal)

        # Auto-log negative feedback to correction ledger
        if signal.reward < 0:
            try:
                ledger = self._get_correction_ledger()
                ledger.add_correction(
                    mistake=signal.decision_context,
                    correction=signal.reasoning or "Negative outcome detected",
                    category=self._derive_category(signal.action_taken),
                    context=f"Action: {signal.action_taken} | Reward: {signal.reward:+.2f}",
                )
            except Exception as e:
                logger.warning(f"Failed to log correction for negative feedback: {e}")

        logger.debug(f"RL feedback recorded: {action_taken} → {outcome} (reward: {reward:+.2f})")

        return signal

    def record_task_outcome(
        self,
        task: str,
        strategy: str,
        success: bool,
        cost: float = 0.0,
        duration: float = 0.0,
        user_satisfaction: Optional[float] = None,
    ):
        """
        Convenience method to record a task outcome.

        Automatically computes reward based on success, cost, and duration.
        """
        # Compute reward
        reward = 0.0
        if success:
            reward += 0.5
            if cost < 0.10:
                reward += 0.2  # Cost efficient
            if duration < 10:
                reward += 0.1  # Fast
        else:
            reward -= 0.5
            if cost > 1.0:
                reward -= 0.2  # Expensive failure

        if user_satisfaction is not None:
            reward = reward * 0.5 + (user_satisfaction - 0.5) * 0.5

        self.record_feedback(
            decision_context=task[:200],
            action_taken=strategy,
            outcome="positive" if success else "negative",
            reward=reward,
            reasoning=f"Success: {success}, Cost: ${cost:.4f}, Duration: {duration:.1f}s",
            metadata={
                "success": success,
                "cost": cost,
                "duration": duration,
                "user_satisfaction": user_satisfaction,
            },
        )

        # Update strategy scores
        self._update_strategy_score(strategy, reward)

    # ===== Pattern Learning =====

    def _update_patterns(self, signal: FeedbackSignal):
        """Update decision patterns based on new feedback"""
        # Extract context keywords for pattern matching
        context_keywords = self._extract_keywords(signal.decision_context)
        pattern_key = "|".join(sorted(context_keywords[:5]))

        if not pattern_key:
            return

        with self._conn() as db:
            # Check if pattern exists
            row = db.execute(
                "SELECT average_reward, sample_count FROM decision_patterns WHERE context_pattern = ?",
                (pattern_key,),
            ).fetchone()

            if row:
                # Update existing pattern with exponential moving average
                old_avg = row[0]
                count = row[1] + 1
                new_avg = old_avg + (signal.reward - old_avg) / count
                confidence = min(1.0, count / 20)

                db.execute(
                    """UPDATE decision_patterns
                       SET average_reward = ?, sample_count = ?, confidence = ?,
                           recommended_action = CASE WHEN ? > average_reward THEN ? ELSE recommended_action END,
                           last_updated = ?
                       WHERE context_pattern = ?""",
                    (
                        new_avg,
                        count,
                        confidence,
                        signal.reward,
                        signal.action_taken,
                        datetime.now().isoformat(),
                        pattern_key,
                    ),
                )
            else:
                import uuid

                db.execute(
                    """INSERT INTO decision_patterns
                       (pattern_id, context_pattern, recommended_action, average_reward,
                        sample_count, confidence, last_updated)
                       VALUES (?, ?, ?, ?, 1, 0.1, ?)""",
                    (
                        str(uuid.uuid4()),
                        pattern_key,
                        signal.action_taken,
                        signal.reward,
                        datetime.now().isoformat(),
                    ),
                )

            db.commit()

    def _update_strategy_score(self, strategy: str, reward: float):
        """Update cumulative strategy scores"""
        with self._conn() as db:
            row = db.execute(
                "SELECT total_reward, usage_count FROM strategy_scores WHERE strategy = ?",
                (strategy,),
            ).fetchone()

            if row:
                total = row[0] + reward
                count = row[1] + 1
                avg = total / count

                db.execute(
                    """UPDATE strategy_scores
                       SET total_reward = ?, usage_count = ?, average_reward = ?, last_used = ?
                       WHERE strategy = ?""",
                    (total, count, avg, datetime.now().isoformat(), strategy),
                )
            else:
                db.execute(
                    """INSERT INTO strategy_scores
                       (strategy, total_reward, usage_count, average_reward, last_used)
                       VALUES (?, ?, 1, ?, ?)""",
                    (strategy, reward, reward, datetime.now().isoformat()),
                )

            db.commit()

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract meaningful keywords from text"""
        import re

        # Remove common stop words and extract meaningful tokens
        stop_words = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "can",
            "to",
            "of",
            "in",
            "for",
            "on",
            "with",
            "at",
            "by",
            "from",
            "it",
            "this",
            "that",
            "these",
            "those",
            "and",
            "or",
            "but",
            "not",
        }

        words = re.findall(r"\b[a-z]+\b", text.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        # Return most frequent keywords
        from collections import Counter

        counts = Counter(keywords)
        return [word for word, _ in counts.most_common(10)]

    # ===== Querying Learned Knowledge =====

    def get_recommendation(self, context: str) -> Optional[DecisionPattern]:
        """
        Get a recommendation based on learned patterns.

        Also checks correction ledger for relevant past mistakes
        and marks them as patterns to avoid.

        Args:
            context: The current decision context

        Returns:
            Best matching DecisionPattern or None
        """
        keywords = self._extract_keywords(context)
        if not keywords:
            return None

        with self._conn() as db:
            # Search for patterns matching current context keywords
            best_pattern = None
            best_score = 0.0

            rows = db.execute(
                "SELECT * FROM decision_patterns WHERE confidence > 0.3 ORDER BY average_reward DESC"
            ).fetchall()

            for row in rows:
                pattern_keywords = set(row[1].split("|"))
                context_keywords = set(keywords)

                overlap = len(pattern_keywords & context_keywords)
                if overlap == 0:
                    continue

                score = (overlap / max(len(pattern_keywords), 1)) * row[5]  # confidence

                if score > best_score:
                    best_score = score
                    best_pattern = DecisionPattern(
                        pattern_id=row[0],
                        context_pattern=row[1],
                        recommended_action=row[2],
                        average_reward=row[3],
                        sample_count=row[4],
                        confidence=row[5],
                        last_updated=row[6],
                    )

        # Enrich recommendation with correction ledger "avoid" patterns
        if best_pattern is not None:
            avoid_patterns = self._get_avoid_patterns(context)
            if avoid_patterns:
                best_pattern.recommended_action += " | AVOID: " + "; ".join(avoid_patterns)

        return best_pattern

    def _get_avoid_patterns(self, context: str) -> list[str]:
        """Check correction ledger for past mistakes relevant to this context"""
        try:
            ledger = self._get_correction_ledger()
            keywords = self._extract_keywords(context)
            avoid = []
            for keyword in keywords[:5]:
                matches = ledger.search_corrections(keyword)
                for match in matches:
                    entry = f"{match['mistake'][:80]} → {match['correction'][:80]}"
                    if entry not in avoid:
                        avoid.append(entry)
                    if len(avoid) >= 5:
                        return avoid
            return avoid
        except Exception as e:
            logger.warning(f"Failed to fetch avoid patterns from correction ledger: {e}")
            return []

    def _derive_category(self, action_taken: str) -> str:
        """Derive a correction category from the strategy/action name"""
        action_lower = action_taken.lower()
        category_map = {
            "code": "coding",
            "search": "research",
            "write": "content",
            "deploy": "deployment",
            "api": "integration",
            "test": "testing",
            "debug": "debugging",
            "plan": "planning",
        }
        for key, category in category_map.items():
            if key in action_lower:
                return category
        return "general"

    def get_strategy_rankings(self) -> list[dict[str, Any]]:
        """Get strategy rankings by average reward"""
        with self._conn() as db:
            rows = db.execute(
                """SELECT strategy, total_reward, usage_count, average_reward, last_used
                   FROM strategy_scores
                   ORDER BY average_reward DESC"""
            ).fetchall()

        return [
            {
                "strategy": r[0],
                "total_reward": r[1],
                "usage_count": r[2],
                "average_reward": r[3],
                "last_used": r[4],
            }
            for r in rows
        ]

    def get_feedback_summary(self, days: int = 7) -> dict[str, Any]:
        """Get summary of recent feedback signals"""
        from datetime import timedelta

        since = (datetime.now() - timedelta(days=days)).isoformat()

        with self._conn() as db:
            total = db.execute(
                "SELECT COUNT(*) FROM feedback_signals WHERE timestamp > ?", (since,)
            ).fetchone()[0]

            positive = db.execute(
                "SELECT COUNT(*) FROM feedback_signals WHERE timestamp > ? AND outcome = 'positive'",
                (since,),
            ).fetchone()[0]

            negative = db.execute(
                "SELECT COUNT(*) FROM feedback_signals WHERE timestamp > ? AND outcome = 'negative'",
                (since,),
            ).fetchone()[0]

            avg_reward = (
                db.execute(
                    "SELECT AVG(reward) FROM feedback_signals WHERE timestamp > ?", (since,)
                ).fetchone()[0]
                or 0.0
            )

        return {
            "period_days": days,
            "total_signals": total,
            "positive": positive,
            "negative": negative,
            "neutral": total - positive - negative,
            "average_reward": round(avg_reward, 4),
            "positive_rate": round(positive / max(total, 1) * 100, 1),
            "strategy_rankings": self.get_strategy_rankings()[:5],
        }

    # ===== Closed-Loop Learning =====

    def close_feedback_loop(
        self,
        task: str,
        strategy: str,
        success: bool,
        cost: float = 0.0,
        duration: float = 0.0,
        user_satisfaction: Optional[float] = None,
    ) -> float:
        """
        End-to-end closed-loop learning from a task result.

        Computes reward, records feedback, and if negative, logs a
        correction to the ledger automatically.

        Args:
            task: Description of the task performed
            strategy: Strategy/action used
            success: Whether the task succeeded
            cost: Monetary cost incurred
            duration: Time taken in seconds
            user_satisfaction: Optional 0.0-1.0 satisfaction score

        Returns:
            The computed reward value for transparency
        """
        # Compute reward signal
        reward = 0.0
        if success:
            reward += 0.5
            if cost < 0.10:
                reward += 0.2
            if duration < 10:
                reward += 0.1
        else:
            reward -= 0.5
            if cost > 1.0:
                reward -= 0.2

        if user_satisfaction is not None:
            reward = reward * 0.5 + (user_satisfaction - 0.5) * 0.5

        reward = max(-1.0, min(1.0, reward))

        outcome = "positive" if success else "negative"
        reasoning = f"Success: {success}, Cost: ${cost:.4f}, Duration: {duration:.1f}s"
        if user_satisfaction is not None:
            reasoning += f", Satisfaction: {user_satisfaction:.2f}"

        # Record feedback (this auto-logs to correction ledger if negative)
        self.record_feedback(
            decision_context=task[:200],
            action_taken=strategy,
            outcome=outcome,
            reward=reward,
            reasoning=reasoning,
            metadata={
                "success": success,
                "cost": cost,
                "duration": duration,
                "user_satisfaction": user_satisfaction,
                "closed_loop": True,
            },
        )

        # Update strategy scores
        self._update_strategy_score(strategy, reward)

        logger.info(f"Feedback loop closed: {strategy} → {outcome} (reward: {reward:+.2f})")

        return reward

    def score_task_outcome(self, task_type: str, result: dict[str, Any]) -> FeedbackSignal:
        """
        Score a task outcome and return a FeedbackSignal with computed reward.

        Args:
            task_type: Type of task (e.g. "code_generation", "research", "deployment")
            result: Dict with keys like "success", "cost", "duration",
                    "quality", "error", "user_satisfaction"

        Returns:
            FeedbackSignal with appropriate reward calculated from the result
        """
        success = result.get("success", False)
        cost = result.get("cost", 0.0)
        duration = result.get("duration", 0.0)
        quality = result.get("quality", None)
        error = result.get("error", None)
        user_satisfaction = result.get("user_satisfaction", None)

        # Base reward from success/failure
        reward = 0.5 if success else -0.5

        # Cost factor
        if cost > 1.0:
            reward -= 0.2
        elif cost < 0.10:
            reward += 0.1

        # Duration factor
        if duration < 10:
            reward += 0.1
        elif duration > 120:
            reward -= 0.1

        # Quality factor (0.0 - 1.0)
        if quality is not None:
            reward += (quality - 0.5) * 0.4

        # User satisfaction override blends in
        if user_satisfaction is not None:
            reward = reward * 0.6 + (user_satisfaction - 0.5) * 0.4

        reward = max(-1.0, min(1.0, reward))

        outcome = "positive" if reward > 0 else ("negative" if reward < 0 else "neutral")
        reasoning_parts = [f"Task type: {task_type}"]
        if error:
            reasoning_parts.append(f"Error: {error}")
        reasoning_parts.append(f"Success: {success}, Cost: ${cost:.4f}, Duration: {duration:.1f}s")
        if quality is not None:
            reasoning_parts.append(f"Quality: {quality:.2f}")

        return self.record_feedback(
            decision_context=f"[{task_type}] {result.get('description', task_type)[:180]}",
            action_taken=result.get("strategy", task_type),
            outcome=outcome,
            reward=reward,
            reasoning=" | ".join(reasoning_parts),
            metadata=result,
        )


# Global RL feedback instance
rl_feedback = ReinforcementFeedback()
