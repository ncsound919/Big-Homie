"""
Content Utilities for Big Homie
Smart truncation, markdown export, and content formatting
"""
import re
from typing import List, Tuple, Optional
from datetime import datetime
from pathlib import Path
from loguru import logger
from config import settings

class SmartTruncator:
    """Intelligently truncates long content while preserving context"""

    MAX_LINES_FULL = 50  # Show full content if under this
    CONTEXT_LINES = 5    # Lines of context around changes

    @staticmethod
    def truncate_code(content: str, changed_lines: Optional[List[int]] = None) -> str:
        """
        Truncate code to show only relevant portions

        Args:
            content: Full code content
            changed_lines: Line numbers that changed (1-indexed)

        Returns:
            Truncated content with context
        """
        lines = content.split('\n')
        total_lines = len(lines)

        # If small enough, return as-is
        if total_lines <= SmartTruncator.MAX_LINES_FULL:
            return content

        # If no changed lines specified, show beginning and end
        if not changed_lines:
            return SmartTruncator._truncate_generic(lines, total_lines)

        # Show changed lines with context
        return SmartTruncator._show_changed_sections(lines, changed_lines, total_lines)

    @staticmethod
    def _truncate_generic(lines: List[str], total_lines: int) -> str:
        """Truncate by showing beginning and end"""
        show_lines = SmartTruncator.MAX_LINES_FULL // 2
        beginning = lines[:show_lines]
        end = lines[-show_lines:]

        truncated = '\n'.join(beginning)
        truncated += f"\n\n... [{total_lines - (2 * show_lines)} lines omitted] ...\n\n"
        truncated += '\n'.join(end)
        return truncated

    @staticmethod
    def _show_changed_sections(
        lines: List[str],
        changed_lines: List[int],
        total_lines: int
    ) -> str:
        """Show only sections with changes plus context"""
        sections = []
        context = SmartTruncator.CONTEXT_LINES

        # Group changed lines into sections
        changed_set = set(changed_lines)
        sections_to_show = []
        current_section = None

        for line_num in sorted(changed_set):
            start = max(1, line_num - context)
            end = min(total_lines, line_num + context)

            if current_section and start <= current_section[1] + 1:
                # Merge with previous section
                current_section = (current_section[0], max(current_section[1], end))
            else:
                if current_section:
                    sections_to_show.append(current_section)
                current_section = (start, end)

        if current_section:
            sections_to_show.append(current_section)

        # Build truncated output
        result = []
        for i, (start, end) in enumerate(sections_to_show):
            if i > 0:
                prev_end = sections_to_show[i-1][1]
                omitted = start - prev_end - 1
                if omitted > 0:
                    result.append(f"\n... [{omitted} lines omitted] ...\n")

            # Add line numbers
            for line_num in range(start, end + 1):
                line_idx = line_num - 1
                if line_idx < len(lines):
                    marker = "* " if line_num in changed_set else "  "
                    result.append(f"{marker}{line_num:4d} | {lines[line_idx]}")

        header = f"Showing changed sections (total: {total_lines} lines)\n"
        header += "Lines marked with * were modified\n\n"
        return header + '\n'.join(result)

    @staticmethod
    def truncate_text(text: str, max_length: int = 500) -> str:
        """Truncate plain text intelligently"""
        if len(text) <= max_length:
            return text

        # Try to break at sentence
        truncated = text[:max_length]
        last_period = truncated.rfind('.')
        last_newline = truncated.rfind('\n')

        break_point = max(last_period, last_newline)
        if break_point > max_length * 0.7:  # At least 70% of target
            truncated = text[:break_point + 1]

        return truncated + f"\n\n[... {len(text) - len(truncated)} chars truncated]"


class MarkdownExporter:
    """Exports thoughts, analysis, and content to markdown files"""

    def __init__(self):
        self.export_dir = settings.data_dir / "markdown_exports"
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def export_thought(
        self,
        title: str,
        content: str,
        category: str = "general",
        metadata: Optional[dict] = None
    ) -> Path:
        """Export a thought or analysis to markdown"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = self._sanitize_filename(title)
        filename = f"{timestamp}_{safe_title}.md"
        filepath = self.export_dir / filename

        markdown = self._format_markdown(title, content, category, metadata)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown)

        logger.info(f"Exported thought to {filepath}")
        return filepath

    def export_conversation(
        self,
        messages: List[dict],
        title: str = "Conversation Export"
    ) -> Path:
        """Export a conversation to markdown"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_conversation.md"
        filepath = self.export_dir / filename

        markdown = f"# {title}\n\n"
        markdown += f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        markdown += "---\n\n"

        for msg in messages:
            role = msg.get("role", "unknown").capitalize()
            content = msg.get("content", "")
            timestamp_str = msg.get("timestamp", "")

            markdown += f"## {role}"
            if timestamp_str:
                markdown += f" - {timestamp_str}"
            markdown += "\n\n"
            markdown += f"{content}\n\n"
            markdown += "---\n\n"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown)

        logger.info(f"Exported conversation to {filepath}")
        return filepath

    def export_analysis(
        self,
        title: str,
        sections: dict
    ) -> Path:
        """Export structured analysis to markdown"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = self._sanitize_filename(title)
        filename = f"{timestamp}_{safe_title}.md"
        filepath = self.export_dir / filename

        markdown = f"# {title}\n\n"
        markdown += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        markdown += "---\n\n"

        for section_title, section_content in sections.items():
            markdown += f"## {section_title}\n\n"
            if isinstance(section_content, list):
                for item in section_content:
                    markdown += f"- {item}\n"
                markdown += "\n"
            elif isinstance(section_content, dict):
                for key, value in section_content.items():
                    markdown += f"**{key}**: {value}\n\n"
            else:
                markdown += f"{section_content}\n\n"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown)

        logger.info(f"Exported analysis to {filepath}")
        return filepath

    def _format_markdown(
        self,
        title: str,
        content: str,
        category: str,
        metadata: Optional[dict]
    ) -> str:
        """Format content as markdown with frontmatter"""
        md = f"# {title}\n\n"
        md += f"**Category**: {category}\n"
        md += f"**Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        if metadata:
            md += "## Metadata\n\n"
            for key, value in metadata.items():
                md += f"- **{key}**: {value}\n"
            md += "\n"

        md += "## Content\n\n"
        md += content
        md += "\n"

        return md

    @staticmethod
    def _sanitize_filename(title: str) -> str:
        """Create safe filename from title"""
        # Remove/replace unsafe characters
        safe = re.sub(r'[^\w\s-]', '', title)
        safe = re.sub(r'[\s]+', '_', safe)
        safe = safe[:50]  # Limit length
        return safe.lower()


# Global instances
smart_truncator = SmartTruncator()
markdown_exporter = MarkdownExporter()
