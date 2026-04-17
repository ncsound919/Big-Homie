"""
Correction Ledger for Big Homie
Learns from user corrections to avoid repeating mistakes
"""

import json
from datetime import datetime
from typing import Optional

from loguru import logger

from config import settings


class CorrectionLedger:
    """Tracks and learns from user corrections"""

    def __init__(self):
        self.ledger_path = settings.data_dir / "correction_ledger.json"
        self.corrections: list[dict] = []
        self.load()

    def load(self):
        """Load existing corrections from disk"""
        if self.ledger_path.exists():
            try:
                with open(self.ledger_path, encoding="utf-8") as f:
                    self.corrections = json.load(f)
                logger.info(f"Loaded {len(self.corrections)} corrections from ledger")
            except Exception as e:
                logger.error(f"Failed to load correction ledger: {e}")
                self.corrections = []
        else:
            self.corrections = []

    def save(self):
        """Save corrections to disk"""
        try:
            with open(self.ledger_path, "w", encoding="utf-8") as f:
                json.dump(self.corrections, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved {len(self.corrections)} corrections to ledger")
        except Exception as e:
            logger.error(f"Failed to save correction ledger: {e}")

    def add_correction(
        self,
        mistake: str,
        correction: str,
        category: str = "general",
        context: Optional[str] = None,
    ):
        """Record a correction made by the user"""
        entry = {
            "id": len(self.corrections) + 1,
            "timestamp": datetime.now().isoformat(),
            "mistake": mistake,
            "correction": correction,
            "category": category,
            "context": context,
            "occurrences": 1,
        }

        # Check if similar correction already exists
        existing = self._find_similar_correction(mistake, category)
        if existing:
            existing["occurrences"] += 1
            existing["last_corrected"] = datetime.now().isoformat()
            logger.info(f"Updated existing correction (now {existing['occurrences']} occurrences)")
        else:
            self.corrections.append(entry)
            logger.info(f"Added new correction to ledger: {category}")

        self.save()

    def _find_similar_correction(self, mistake: str, category: str) -> Optional[dict]:
        """Find a similar existing correction"""
        mistake_lower = mistake.lower()
        for correction in self.corrections:
            if (
                correction["category"] == category
                and correction["mistake"].lower() == mistake_lower
            ):
                return correction
        return None

    def get_corrections_for_category(self, category: str) -> list[dict]:
        """Get all corrections for a specific category"""
        return [c for c in self.corrections if c["category"] == category]

    def get_common_mistakes(self, limit: int = 10) -> list[dict]:
        """Get the most common mistakes"""
        sorted_corrections = sorted(
            self.corrections, key=lambda x: x.get("occurrences", 1), reverse=True
        )
        return sorted_corrections[:limit]

    def search_corrections(self, query: str) -> list[dict]:
        """Search corrections by keyword"""
        query_lower = query.lower()
        results = []
        for correction in self.corrections:
            if (
                query_lower in correction["mistake"].lower()
                or query_lower in correction["correction"].lower()
                or query_lower in correction.get("context", "").lower()
            ):
                results.append(correction)
        return results

    def get_learnings_summary(self) -> str:
        """Generate a summary of learned corrections"""
        if not self.corrections:
            return "No corrections learned yet."

        categories = {}
        for correction in self.corrections:
            cat = correction["category"]
            categories[cat] = categories.get(cat, 0) + 1

        summary = (
            f"Learned {len(self.corrections)} corrections across {len(categories)} categories:\n\n"
        )
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            summary += f"- {cat}: {count} corrections\n"

        common = self.get_common_mistakes(5)
        if common:
            summary += "\nMost common mistakes:\n"
            for i, mistake in enumerate(common, 1):
                summary += f"{i}. {mistake['mistake']} ({mistake.get('occurrences', 1)}x)\n"

        return summary

    def apply_corrections_to_context(self) -> str:
        """Generate context string for LLM to avoid past mistakes"""
        if not self.corrections:
            return ""

        recent = sorted(self.corrections, key=lambda x: x.get("timestamp", ""), reverse=True)[:20]

        context = "# Previously Corrected Mistakes (Learn from these):\n\n"
        for correction in recent:
            context += f"- **Mistake**: {correction['mistake']}\n"
            context += f"  **Correction**: {correction['correction']}\n"
            if correction.get("context"):
                context += f"  **Context**: {correction['context']}\n"
            context += "\n"

        return context


# Global correction ledger instance
correction_ledger = CorrectionLedger()
