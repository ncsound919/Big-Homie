"""
Tone Analyzer & Preference Tracker for Big Homie
Analyzes user communication style and tracks preferences
"""

import re
from datetime import datetime
from typing import Optional

from loguru import logger

from memory import memory


class ToneAnalyzer:
    """Analyzes user communication style and adapts responses"""

    def __init__(self):
        self.recent_messages: list[dict] = []
        self.max_history = 20

    def analyze_message(self, message: str) -> dict:
        """Analyze a user message for tone characteristics"""
        words = message.split()
        sentences = re.split(r"[.!?]+", message)
        sentences = [s.strip() for s in sentences if s.strip()]

        analysis = {
            "length": len(message),
            "word_count": len(words),
            "sentence_count": len(sentences),
            "avg_sentence_length": len(words) / max(len(sentences), 1),
            "brevity_score": self._calculate_brevity(message),
            "formality_score": self._calculate_formality(message),
            "technical_score": self._calculate_technicality(message),
            "urgency_score": self._calculate_urgency(message),
            "timestamp": datetime.now().isoformat(),
        }

        self.recent_messages.append(analysis)
        if len(self.recent_messages) > self.max_history:
            self.recent_messages.pop(0)

        return analysis

    def _calculate_brevity(self, message: str) -> float:
        """Calculate brevity score (0-1, higher = more brief)"""
        word_count = len(message.split())
        if word_count <= 5:
            return 1.0
        elif word_count <= 15:
            return 0.7
        elif word_count <= 30:
            return 0.4
        else:
            return 0.1

    def _calculate_formality(self, message: str) -> float:
        """Calculate formality score (0-1, higher = more formal)"""
        informal_markers = ["gonna", "wanna", "gotta", "yeah", "yep", "nope", "lol", "btw"]
        formal_markers = ["please", "kindly", "would", "could", "appreciate"]

        message_lower = message.lower()
        informal_count = sum(1 for marker in informal_markers if marker in message_lower)
        formal_count = sum(1 for marker in formal_markers if marker in message_lower)

        if informal_count > formal_count:
            return max(0.0, 0.5 - (informal_count * 0.1))
        else:
            return min(1.0, 0.5 + (formal_count * 0.1))

    def _calculate_technicality(self, message: str) -> float:
        """Calculate technical language score (0-1)"""
        technical_markers = [
            "api",
            "function",
            "class",
            "method",
            "variable",
            "database",
            "algorithm",
            "implementation",
            "infrastructure",
            "deployment",
            "architecture",
            "optimization",
            "performance",
            "scalability",
        ]

        message_lower = message.lower()
        tech_count = sum(1 for marker in technical_markers if marker in message_lower)
        return min(1.0, tech_count * 0.15)

    def _calculate_urgency(self, message: str) -> float:
        """Calculate urgency score (0-1)"""
        urgency_markers = ["asap", "urgent", "immediately", "now", "quick", "fast", "!", "critical"]
        message_lower = message.lower()
        urgency_count = sum(1 for marker in urgency_markers if marker in message_lower)
        exclamation_count = message.count("!")
        return min(1.0, (urgency_count * 0.2) + (exclamation_count * 0.1))

    def get_average_style(self) -> dict:
        """Get average communication style from recent messages"""
        if not self.recent_messages:
            return {
                "brevity": 0.5,
                "formality": 0.5,
                "technical": 0.5,
                "urgency": 0.3,
                "avg_word_count": 20,
            }

        return {
            "brevity": sum(m["brevity_score"] for m in self.recent_messages)
            / len(self.recent_messages),
            "formality": sum(m["formality_score"] for m in self.recent_messages)
            / len(self.recent_messages),
            "technical": sum(m["technical_score"] for m in self.recent_messages)
            / len(self.recent_messages),
            "urgency": sum(m["urgency_score"] for m in self.recent_messages)
            / len(self.recent_messages),
            "avg_word_count": sum(m["word_count"] for m in self.recent_messages)
            / len(self.recent_messages),
        }

    def suggest_response_style(self) -> str:
        """Suggest how to style the response based on user's tone"""
        style = self.get_average_style()

        suggestions = []

        if style["brevity"] > 0.6:
            suggestions.append("Keep responses concise and to the point")
        elif style["brevity"] < 0.3:
            suggestions.append("Provide detailed, comprehensive responses")

        if style["formality"] > 0.6:
            suggestions.append("Use formal, professional language")
        elif style["formality"] < 0.4:
            suggestions.append("Use casual, conversational tone")

        if style["technical"] > 0.5:
            suggestions.append("Include technical details and implementation specifics")

        if style["urgency"] > 0.5:
            suggestions.append("Prioritize speed and direct solutions")

        target_length = int(style["avg_word_count"] * 3)  # Response ~3x user message length
        suggestions.append(f"Target response length: ~{target_length} words")

        return " | ".join(suggestions)


class PreferenceTracker:
    """Tracks and learns user preferences over time"""

    def __init__(self):
        self.preferences: dict[str, dict] = {}
        self.load_preferences()

    def load_preferences(self):
        """Load preferences from memory"""
        stored = memory.search_memory(category="preference")
        for item in stored:
            self.preferences[item["key"]] = {
                "value": item["value"],
                "confidence": item["importance"] / 10.0,
                "occurrences": item.get("access_count", 1),
            }
        logger.info(f"Loaded {len(self.preferences)} preferences")

    def record_preference(
        self, key: str, value: str, confidence: float = 1.0, context: Optional[str] = None
    ):
        """Record a user preference"""
        if key in self.preferences:
            pref = self.preferences[key]
            pref["occurrences"] += 1
            pref["confidence"] = min(1.0, pref["confidence"] + 0.1)
            pref["value"] = value  # Update to latest
        else:
            self.preferences[key] = {
                "value": value,
                "confidence": confidence,
                "occurrences": 1,
                "context": context,
            }

        # Save to long-term memory
        memory.store(
            key=key,
            value=value,
            category="preference",
            importance=int(min(10, self.preferences[key]["confidence"] * 10)),
        )
        logger.info(f"Recorded preference: {key} = {value}")

    def get_preference(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a user preference"""
        if key in self.preferences:
            return self.preferences[key]["value"]
        return default

    def get_all_preferences(self) -> dict[str, str]:
        """Get all preferences as a simple dict"""
        return {k: v["value"] for k, v in self.preferences.items()}

    def get_preferences_summary(self) -> str:
        """Generate a summary of learned preferences"""
        if not self.preferences:
            return "No preferences learned yet."

        sorted_prefs = sorted(
            self.preferences.items(), key=lambda x: x[1]["confidence"], reverse=True
        )

        summary = f"Learned {len(self.preferences)} user preferences:\n\n"
        for key, pref in sorted_prefs[:10]:
            confidence_pct = int(pref["confidence"] * 100)
            summary += f"- {key}: {pref['value']} ({confidence_pct}% confidence)\n"

        return summary

    def apply_preferences_to_context(self) -> str:
        """Generate context string for LLM with user preferences"""
        if not self.preferences:
            return ""

        high_confidence = {k: v for k, v in self.preferences.items() if v["confidence"] > 0.5}

        if not high_confidence:
            return ""

        context = "# User Preferences (apply these when relevant):\n\n"
        for key, pref in sorted(
            high_confidence.items(), key=lambda x: x[1]["confidence"], reverse=True
        ):
            context += f"- **{key}**: {pref['value']}\n"

        return context


# Global instances
tone_analyzer = ToneAnalyzer()
preference_tracker = PreferenceTracker()
