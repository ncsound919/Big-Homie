"""
Fact Checker & Metadata Tagging for Big Homie
Self-reflection and automatic log categorization
"""
import re
from typing import Dict, List, Optional, Set
from datetime import datetime
from loguru import logger
from config import settings

class FactChecker:
    """Self-reflection system to identify uncertain claims"""

    # Uncertainty markers in text
    UNCERTAINTY_MARKERS = [
        "might", "maybe", "possibly", "probably", "likely", "could be",
        "i think", "i believe", "it seems", "appears to", "may",
        "approximately", "roughly", "about", "around", "~"
    ]

    # High confidence markers
    CONFIDENCE_MARKERS = [
        "definitely", "certainly", "always", "never", "must",
        "will", "guaranteed", "proven", "confirmed", "verified"
    ]

    @staticmethod
    def analyze_confidence(text: str) -> Dict:
        """
        Analyze a response for confidence level

        Returns:
            {
                "confidence_score": 0.0-1.0,
                "uncertain_claims": List[str],
                "high_confidence_claims": List[str],
                "flagged_sections": List[Dict]
            }
        """
        text_lower = text.lower()
        sentences = FactChecker._split_sentences(text)

        uncertainty_count = 0
        confidence_count = 0
        uncertain_claims = []
        flagged_sections = []

        for sentence in sentences:
            sentence_lower = sentence.lower()

            # Check for uncertainty markers
            uncertainty_found = []
            for marker in FactChecker.UNCERTAINTY_MARKERS:
                if marker in sentence_lower:
                    uncertainty_count += 1
                    uncertainty_found.append(marker)

            if uncertainty_found:
                uncertain_claims.append(sentence.strip())
                flagged_sections.append({
                    "text": sentence.strip(),
                    "reason": f"Contains uncertainty markers: {', '.join(uncertainty_found)}",
                    "confidence": "low"
                })

            # Check for high confidence markers (might be overconfident)
            for marker in FactChecker.CONFIDENCE_MARKERS:
                if marker in sentence_lower:
                    confidence_count += 1

        # Calculate overall confidence score
        total_markers = uncertainty_count + confidence_count
        if total_markers == 0:
            confidence_score = 0.7  # Neutral
        else:
            confidence_score = confidence_count / total_markers

        # Flag if too uncertain (< 60%)
        if confidence_score < 0.6:
            flagged_sections.append({
                "text": "[Overall Response]",
                "reason": f"Low confidence score: {int(confidence_score * 100)}%",
                "confidence": "low"
            })

        return {
            "confidence_score": confidence_score,
            "uncertain_claims": uncertain_claims,
            "uncertainty_marker_count": uncertainty_count,
            "flagged_sections": flagged_sections,
            "needs_verification": len(flagged_sections) > 0
        }

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    @staticmethod
    def format_fact_check_report(analysis: Dict) -> str:
        """Format fact-checking results as a readable report"""
        confidence_pct = int(analysis["confidence_score"] * 100)

        report = f"## Fact-Check Report\n\n"
        report += f"**Overall Confidence**: {confidence_pct}%\n\n"

        if not analysis["needs_verification"]:
            report += "✓ No significant uncertainty detected.\n"
            return report

        report += "⚠️ The following sections may need verification:\n\n"

        for i, section in enumerate(analysis["flagged_sections"], 1):
            report += f"{i}. **{section['text'][:100]}...**\n"
            report += f"   - {section['reason']}\n\n"

        return report


class MetadataTagger:
    """Automatically tags logs and content with metadata"""

    # Category keywords
    CATEGORY_KEYWORDS = {
        "coding": [
            "code", "function", "class", "method", "bug", "debug",
            "implementation", "algorithm", "python", "javascript",
            "api", "database", "sql", "git", "repository"
        ],
        "research": [
            "research", "analyze", "study", "investigate", "explore",
            "find", "search", "compare", "evaluate", "review",
            "article", "paper", "data", "statistics"
        ],
        "finance": [
            "stock", "trading", "portfolio", "investment", "market",
            "price", "ticker", "financial", "crypto", "bitcoin",
            "dividend", "return", "risk"
        ],
        "marketing": [
            "marketing", "campaign", "content", "social media", "seo",
            "advertising", "brand", "customer", "audience", "engagement"
        ],
        "web": [
            "website", "scraping", "browser", "html", "css", "dom",
            "webpage", "url", "http", "screenshot"
        ],
        "data": [
            "dataset", "analytics", "visualization", "chart", "graph",
            "statistics", "metrics", "dataframe", "csv", "analysis"
        ],
        "system": [
            "error", "warning", "critical", "log", "exception",
            "crash", "failure", "timeout", "performance"
        ]
    }

    @staticmethod
    def tag_content(content: str) -> Set[str]:
        """
        Automatically tag content based on keywords

        Returns:
            Set of relevant tags
        """
        content_lower = content.lower()
        tags = set()

        for category, keywords in MetadataTagger.CATEGORY_KEYWORDS.items():
            matches = sum(1 for keyword in keywords if keyword in content_lower)
            if matches >= 2:  # At least 2 keyword matches
                tags.add(category)

        # Add special tags
        if "?" in content:
            tags.add("question")

        if any(word in content_lower for word in ["error", "failed", "exception"]):
            tags.add("error")

        if any(word in content_lower for word in ["urgent", "critical", "asap"]):
            tags.add("urgent")

        return tags

    @staticmethod
    def tag_log_entry(log_text: str, level: str) -> Dict:
        """
        Tag a log entry with metadata

        Args:
            log_text: The log message
            level: Log level (INFO, WARNING, ERROR, etc.)

        Returns:
            Dictionary of metadata
        """
        tags = MetadataTagger.tag_content(log_text)

        metadata = {
            "tags": list(tags),
            "level": level,
            "timestamp": datetime.now().isoformat(),
            "length": len(log_text),
            "has_stacktrace": "Traceback" in log_text or "Error:" in log_text
        }

        # Add primary category (most relevant)
        if tags:
            category_scores = {}
            for category, keywords in MetadataTagger.CATEGORY_KEYWORDS.items():
                if category in tags:
                    matches = sum(1 for kw in keywords if kw in log_text.lower())
                    category_scores[category] = matches

            if category_scores:
                metadata["primary_category"] = max(category_scores, key=category_scores.get)

        return metadata

    @staticmethod
    def filter_logs_by_tags(logs: List[Dict], required_tags: Set[str]) -> List[Dict]:
        """Filter logs that contain any of the required tags"""
        filtered = []
        for log in logs:
            log_tags = set(log.get("tags", []))
            if log_tags.intersection(required_tags):
                filtered.append(log)
        return filtered


# Global instances
fact_checker = FactChecker()
metadata_tagger = MetadataTagger()
