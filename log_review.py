"""
Self-Correction & Log Review System
Enables Big Homie to analyze its own error logs and improve autonomously
"""

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from config import settings


@dataclass
class ErrorPattern:
    """An identified error pattern"""

    pattern: str
    count: int
    first_seen: datetime
    last_seen: datetime
    severity: str
    category: str
    examples: list[str]
    suggested_fix: Optional[str] = None


@dataclass
class LogAnalysis:
    """Analysis results from log review"""

    total_errors: int
    total_warnings: int
    error_patterns: list[ErrorPattern]
    improvement_suggestions: list[str]
    success_metrics: dict[str, Any]
    timestamp: datetime


class LogReviewSystem:
    """
    Autonomous log review and self-correction system

    Daily Review Tasks:
    1. Analyze error logs for patterns
    2. Identify most common failures
    3. Categorize errors by type
    4. Generate improvement suggestions
    5. Propose code fixes
    6. Track success rates over time
    """

    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or settings.data_dir / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.analysis_history: list[LogAnalysis] = []

    def get_log_file_path(self, log_type: str = "main") -> Path:
        """Get path to log file"""
        return self.log_dir / f"{log_type}.log"

    def read_logs(
        self, log_type: str = "main", since: Optional[datetime] = None, limit: int = 10000
    ) -> list[str]:
        """
        Read log entries

        Args:
            log_type: Type of log (main, heartbeat, etc.)
            since: Only read logs after this time
            limit: Max lines to read

        Returns:
            List of log lines
        """
        log_path = self.get_log_file_path(log_type)

        if not log_path.exists():
            return []

        try:
            with open(log_path) as f:
                lines = f.readlines()

            # Filter by time if requested
            if since:
                filtered = []
                for line in lines:
                    # Loguru default format: "YYYY-MM-DD HH:MM:SS.mmm | LEVEL | ..."
                    # Also accept plain "YYYY-MM-DD HH:MM:SS" without milliseconds.
                    match = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(?:\.\d+)?", line)
                    if match:
                        try:
                            timestamp = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
                            if timestamp >= since:
                                filtered.append(line)
                        except ValueError:
                            logger.debug(
                                f"log_review: skipping line with "
                                f"unparseable timestamp: {line[:80]!r}"
                            )
                lines = filtered

            return lines[-limit:] if len(lines) > limit else lines

        except Exception as e:
            logger.error(f"Failed to read logs: {e}")
            return []

    def analyze_errors(self, lines: list[str], min_pattern_count: int = 3) -> list[ErrorPattern]:
        """
        Analyze log lines to identify error patterns

        Args:
            lines: Log lines to analyze
            min_pattern_count: Minimum occurrences to identify pattern

        Returns:
            List of ErrorPattern objects
        """
        # Extract errors and warnings
        errors = []
        warnings = []

        for line in lines:
            if "ERROR" in line:
                errors.append(line)
            elif "WARNING" in line:
                warnings.append(line)

        # Identify patterns in errors
        error_signatures = defaultdict(list)

        for error in errors:
            # Extract error signature (remove specific values like timestamps, IDs, paths)
            signature = re.sub(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", "TIMESTAMP", error)
            signature = re.sub(
                r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
                "UUID",
                signature,
            )
            signature = re.sub(r"/[\w/.-]+", "PATH", signature)
            signature = re.sub(r"\d+", "NUM", signature)

            error_signatures[signature].append(error)

        # Create ErrorPattern objects for frequent patterns
        patterns = []

        for signature, examples in error_signatures.items():
            if len(examples) >= min_pattern_count:
                # Extract timestamp from first and last occurrence
                first_timestamp = self._extract_timestamp(examples[0])
                last_timestamp = self._extract_timestamp(examples[-1])

                # Categorize error
                category = self._categorize_error(signature)

                # Generate suggested fix
                suggested_fix = self._suggest_fix(signature, category)

                patterns.append(
                    ErrorPattern(
                        pattern=signature[:200],
                        count=len(examples),
                        first_seen=first_timestamp or datetime.now(),
                        last_seen=last_timestamp or datetime.now(),
                        severity=self._determine_severity(signature),
                        category=category,
                        examples=examples[:3],  # Keep first 3 examples
                        suggested_fix=suggested_fix,
                    )
                )

        # Sort by count (most frequent first)
        patterns.sort(key=lambda p: p.count, reverse=True)

        return patterns

    def _extract_timestamp(self, log_line: str) -> Optional[datetime]:
        """Extract timestamp from log line"""
        # Match Loguru-style "YYYY-MM-DD HH:MM:SS" with optional ".mmm" milliseconds
        # Use re.search so leading metadata/level prefixes are ignored.
        match = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(?:\.\d+)?", log_line)
        if match:
            try:
                return datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
        return None

    def _categorize_error(self, error_signature: str) -> str:
        """Categorize error by type"""
        categories = {
            "api": ["API", "request", "response", "http", "status"],
            "llm": ["LLM", "model", "anthropic", "openai", "completion"],
            "memory": ["memory", "database", "sqlite", "chroma"],
            "file": ["file", "path", "directory", "read", "write"],
            "network": ["connection", "timeout", "network", "socket"],
            "parsing": ["json", "parse", "decode", "format"],
            "config": ["config", "settings", "env", "key"],
            "browser": ["playwright", "browser", "page", "selector"],
        }

        error_lower = error_signature.lower()

        for category, keywords in categories.items():
            if any(kw in error_lower for kw in keywords):
                return category

        return "unknown"

    def _determine_severity(self, error_signature: str) -> str:
        """Determine error severity"""
        critical_keywords = ["crash", "fatal", "shutdown", "corrupt"]
        high_keywords = ["failed", "exception", "error", "denied"]

        error_lower = error_signature.lower()

        if any(kw in error_lower for kw in critical_keywords):
            return "critical"
        elif any(kw in error_lower for kw in high_keywords):
            return "high"
        else:
            return "medium"

    def _suggest_fix(self, error_signature: str, category: str) -> str:
        """Generate suggested fix for error pattern"""
        fixes = {
            "api": (
                "Check API key configuration and rate limits. "
                "Add retry logic with exponential backoff."
            ),
            "llm": (
                "Verify model availability and API key. "
                "Check token limits and request formatting."
            ),
            "memory": (
                "Check database file permissions. "
                "Verify ChromaDB installation and storage path."
            ),
            "file": (
                "Verify file paths exist. "
                "Add proper error handling for file operations."
            ),
            "network": (
                "Add timeout and retry logic. "
                "Check network connectivity and firewall settings."
            ),
            "parsing": (
                "Add JSON validation before parsing. "
                "Handle malformed responses gracefully."
            ),
            "config": (
                "Verify .env file exists and contains required keys. "
                "Check settings validation."
            ),
            "browser": (
                "Check Playwright installation. "
                "Add wait conditions before interacting "
                "with elements."
            ),
        }

        return fixes.get(category, "Review error context and add appropriate error handling.")

    def calculate_success_metrics(self, lines: list[str]) -> dict[str, Any]:
        """
        Calculate success metrics from logs

        Returns:
            Dict with success rates, task completion, costs, etc.
        """
        total_tasks = 0
        completed_tasks = 0
        failed_tasks = 0
        total_cost = 0.0

        for line in lines:
            if "Task completed" in line:
                completed_tasks += 1
                total_tasks += 1
            elif "Task failed" in line:
                failed_tasks += 1
                total_tasks += 1

            # Extract cost information
            cost_match = re.search(r"\$(\d+\.\d+)", line)
            if cost_match:
                total_cost += float(cost_match.group(1))

        success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": round(success_rate, 2),
            "total_cost": round(total_cost, 4),
            "avg_cost_per_task": round(total_cost / total_tasks, 4) if total_tasks > 0 else 0,
        }

    def generate_improvement_suggestions(
        self, patterns: list[ErrorPattern], metrics: dict[str, Any]
    ) -> list[str]:
        """
        Generate actionable improvement suggestions

        Args:
            patterns: Identified error patterns
            metrics: Success metrics

        Returns:
            List of improvement suggestions
        """
        suggestions = []

        # Analyze most frequent errors
        if patterns:
            top_error = patterns[0]
            suggestions.append(
                f"Priority Fix: '{top_error.category}' errors ({top_error.count} occurrences). "
                f"{top_error.suggested_fix}"
            )

        # Check success rate
        if metrics["success_rate"] < 90:
            suggestions.append(
                f"Success rate is {metrics['success_rate']}%. "
                f"Review failed tasks and add better error recovery."
            )

        # Check cost efficiency
        if metrics["total_tasks"] > 0:
            avg_cost = metrics["avg_cost_per_task"]
            if avg_cost > 0.10:
                suggestions.append(
                    f"Average cost per task is ${avg_cost:.4f}. "
                    f"Consider routing more tasks to cheaper models."
                )

        # Check for critical errors
        critical_patterns = [p for p in patterns if p.severity == "critical"]
        if critical_patterns:
            suggestions.append(
                f"Found {len(critical_patterns)} critical error patterns. "
                f"These should be fixed immediately."
            )

        # Generic improvement if no specific issues
        if not suggestions:
            suggestions.append("System running well. Continue monitoring for new patterns.")

        return suggestions

    def perform_daily_review(self) -> LogAnalysis:
        """
        Perform comprehensive daily log review

        Returns:
            LogAnalysis with findings and suggestions
        """
        logger.info("Starting daily log review...")

        # Read logs from last 24 hours
        since = datetime.now() - timedelta(days=1)
        lines = self.read_logs(since=since)

        # Count errors and warnings
        total_errors = sum(1 for line in lines if "ERROR" in line)
        total_warnings = sum(1 for line in lines if "WARNING" in line)

        # Analyze error patterns
        patterns = self.analyze_errors(lines)

        # Calculate success metrics
        metrics = self.calculate_success_metrics(lines)

        # Generate improvements
        suggestions = self.generate_improvement_suggestions(patterns, metrics)

        # Create analysis
        analysis = LogAnalysis(
            total_errors=total_errors,
            total_warnings=total_warnings,
            error_patterns=patterns,
            improvement_suggestions=suggestions,
            success_metrics=metrics,
            timestamp=datetime.now(),
        )

        # Store in history
        self.analysis_history.append(analysis)

        # Log summary
        logger.info("Daily Review Complete:")
        logger.info(f"  Errors: {total_errors}, Warnings: {total_warnings}")
        logger.info(f"  Patterns identified: {len(patterns)}")
        logger.info(f"  Success rate: {metrics['success_rate']}%")
        logger.info(f"  Suggestions: {len(suggestions)}")

        return analysis

    def export_analysis(self, analysis: LogAnalysis, path: Optional[Path] = None) -> Path:
        """Export analysis to JSON file"""
        if not path:
            path = self.log_dir / f"analysis_{analysis.timestamp.strftime('%Y%m%d_%H%M%S')}.json"

        data = {
            "timestamp": analysis.timestamp.isoformat(),
            "total_errors": analysis.total_errors,
            "total_warnings": analysis.total_warnings,
            "error_patterns": [
                {
                    "pattern": p.pattern,
                    "count": p.count,
                    "severity": p.severity,
                    "category": p.category,
                    "suggested_fix": p.suggested_fix,
                }
                for p in analysis.error_patterns
            ],
            "improvement_suggestions": analysis.improvement_suggestions,
            "success_metrics": analysis.success_metrics,
        }

        path.write_text(json.dumps(data, indent=2))
        logger.info(f"Analysis exported to: {path}")

        return path


# Global log review instance
log_reviewer = LogReviewSystem()
