"""
Document Intelligence - Tier 3 Perception
Parse and extract structured information from PDFs, spreadsheets, code repos, and more
"""

import csv
import io
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from loguru import logger


@dataclass
class DocumentChunk:
    """A chunk of extracted document content"""

    content: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    chunk_type: str = "text"  # text, table, code, heading, metadata
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentAnalysis:
    """Complete analysis of a document"""

    source: str
    doc_type: str
    total_pages: Optional[int] = None
    chunks: list[DocumentChunk] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    summary: Optional[str] = None
    error: Optional[str] = None


class DocumentIntelligence:
    """
    Parse and extract structured information from documents with semantic understanding.

    Supported formats:
    - PDF documents
    - CSV/TSV spreadsheets
    - JSON/JSONL data files
    - Plain text and Markdown
    - Source code files
    - HTML documents
    """

    def __init__(self):
        self._capabilities = self._detect_capabilities()

    def _detect_capabilities(self) -> dict[str, bool]:
        """Detect available parsing libraries"""
        caps = {}

        try:
            import PyPDF2  # noqa: F401

            caps["pdf_pypdf2"] = True
        except ImportError:
            caps["pdf_pypdf2"] = False

        try:
            import pdfplumber  # noqa: F401

            caps["pdf_plumber"] = True
        except ImportError:
            caps["pdf_plumber"] = False

        try:
            from bs4 import BeautifulSoup  # noqa: F401

            caps["html"] = True
        except ImportError:
            caps["html"] = False

        try:
            import pytesseract  # noqa: F401

            caps["ocr"] = True
        except ImportError:
            caps["ocr"] = False

        logger.info(f"Document Intelligence capabilities: {caps}")
        return caps

    async def analyze(self, source: str, content: Optional[bytes] = None) -> DocumentAnalysis:
        """
        Analyze a document from a file path or raw content.

        Args:
            source: File path or URL
            content: Optional raw bytes (if not reading from path)

        Returns:
            DocumentAnalysis with extracted content and metadata
        """
        doc_type = self._detect_type(source)

        try:
            if doc_type == "pdf":
                return await self._analyze_pdf(source, content)
            elif doc_type == "csv":
                return await self._analyze_csv(source, content)
            elif doc_type == "json":
                return await self._analyze_json(source, content)
            elif doc_type == "markdown":
                return await self._analyze_markdown(source, content)
            elif doc_type == "html":
                return await self._analyze_html(source, content)
            elif doc_type == "code":
                return await self._analyze_code(source, content)
            elif doc_type == "text":
                return await self._analyze_text(source, content)
            else:
                return await self._analyze_text(source, content)

        except Exception as e:
            logger.error(f"Document analysis failed for {source}: {e}")
            return DocumentAnalysis(source=source, doc_type=doc_type, error=str(e))

    def _detect_type(self, source: str) -> str:
        """Detect document type from file extension"""
        ext = Path(source).suffix.lower()

        type_map = {
            ".pdf": "pdf",
            ".csv": "csv",
            ".tsv": "csv",
            ".json": "json",
            ".jsonl": "json",
            ".md": "markdown",
            ".markdown": "markdown",
            ".html": "html",
            ".htm": "html",
            ".py": "code",
            ".js": "code",
            ".ts": "code",
            ".java": "code",
            ".go": "code",
            ".rs": "code",
            ".c": "code",
            ".cpp": "code",
            ".rb": "code",
            ".txt": "text",
            ".log": "text",
            ".xml": "text",
            ".yaml": "text",
            ".yml": "text",
            ".toml": "text",
            ".ini": "text",
        }

        return type_map.get(ext, "text")

    def _read_content(self, source: str, content: Optional[bytes] = None) -> bytes:
        """Read content from file or use provided bytes"""
        if content is not None:
            return content
        with open(source, "rb") as f:
            return f.read()

    def _read_text_content(self, source: str, content: Optional[bytes] = None) -> str:
        """Read text content from file"""
        raw = self._read_content(source, content)
        return raw.decode("utf-8", errors="replace")

    # ===== PDF Analysis =====

    async def _analyze_pdf(self, source: str, content: Optional[bytes] = None) -> DocumentAnalysis:
        """Extract text and structure from PDF"""
        analysis = DocumentAnalysis(source=source, doc_type="pdf")

        raw = self._read_content(source, content)

        if self._capabilities.get("pdf_plumber"):
            return await self._analyze_pdf_plumber(source, raw, analysis)
        elif self._capabilities.get("pdf_pypdf2"):
            return await self._analyze_pdf_pypdf2(source, raw, analysis)
        else:
            analysis.error = "No PDF library available. Install pdfplumber or PyPDF2."
            return analysis

    async def _analyze_pdf_plumber(
        self, source: str, raw: bytes, analysis: DocumentAnalysis
    ) -> DocumentAnalysis:
        """Analyze PDF using pdfplumber (better table extraction)"""
        import pdfplumber

        with pdfplumber.open(io.BytesIO(raw)) as pdf:
            analysis.total_pages = len(pdf.pages)
            analysis.metadata["page_count"] = len(pdf.pages)

            for i, page in enumerate(pdf.pages):
                # Extract text
                text = page.extract_text() or ""
                if text.strip():
                    analysis.chunks.append(
                        DocumentChunk(content=text, page_number=i + 1, chunk_type="text")
                    )

                # Extract tables
                tables = page.extract_tables()
                for j, table in enumerate(tables):
                    if table:
                        table_text = self._format_table(table)
                        analysis.chunks.append(
                            DocumentChunk(
                                content=table_text,
                                page_number=i + 1,
                                chunk_type="table",
                                metadata={"table_index": j},
                            )
                        )

        return analysis

    async def _analyze_pdf_pypdf2(
        self, source: str, raw: bytes, analysis: DocumentAnalysis
    ) -> DocumentAnalysis:
        """Analyze PDF using PyPDF2 (basic text extraction)"""
        import PyPDF2

        reader = PyPDF2.PdfReader(io.BytesIO(raw))
        analysis.total_pages = len(reader.pages)

        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                analysis.chunks.append(
                    DocumentChunk(content=text, page_number=i + 1, chunk_type="text")
                )

        # Extract metadata
        if reader.metadata:
            analysis.metadata.update(
                {
                    "title": reader.metadata.get("/Title", ""),
                    "author": reader.metadata.get("/Author", ""),
                    "subject": reader.metadata.get("/Subject", ""),
                }
            )

        return analysis

    # ===== CSV Analysis =====

    async def _analyze_csv(self, source: str, content: Optional[bytes] = None) -> DocumentAnalysis:
        """Analyze CSV/TSV file"""
        analysis = DocumentAnalysis(source=source, doc_type="csv")
        text = self._read_text_content(source, content)

        # Detect delimiter
        delimiter = "\t" if source.endswith(".tsv") else ","

        reader = csv.reader(io.StringIO(text), delimiter=delimiter)
        rows = list(reader)

        if not rows:
            return analysis

        headers = rows[0]
        data_rows = rows[1:]

        analysis.metadata["columns"] = headers
        analysis.metadata["row_count"] = len(data_rows)
        analysis.metadata["column_count"] = len(headers)

        # Extract header info
        analysis.chunks.append(
            DocumentChunk(
                content=f"Columns: {', '.join(headers)}",
                chunk_type="metadata",
                metadata={"headers": headers},
            )
        )

        # Sample data (first 20 rows)
        sample_size = min(20, len(data_rows))
        sample = data_rows[:sample_size]

        table_data = [headers] + sample
        analysis.chunks.append(
            DocumentChunk(
                content=self._format_table(table_data),
                chunk_type="table",
                metadata={"sample_size": sample_size, "total_rows": len(data_rows)},
            )
        )

        # Basic statistics for numeric columns
        stats = self._compute_csv_stats(headers, data_rows)
        if stats:
            analysis.chunks.append(
                DocumentChunk(
                    content=f"Statistics:\n{json.dumps(stats, indent=2)}",
                    chunk_type="metadata",
                    metadata={"stats": stats},
                )
            )

        return analysis

    def _compute_csv_stats(self, headers: list[str], rows: list[list[str]]) -> dict:
        """Compute basic statistics for numeric columns"""
        stats = {}
        for col_idx, header in enumerate(headers):
            values = []
            for row in rows:
                if col_idx < len(row):
                    try:
                        values.append(float(row[col_idx]))
                    except (ValueError, TypeError):
                        continue

            if len(values) >= 2:
                stats[header] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "mean": sum(values) / len(values),
                }

        return stats

    # ===== JSON Analysis =====

    async def _analyze_json(self, source: str, content: Optional[bytes] = None) -> DocumentAnalysis:
        """Analyze JSON/JSONL file"""
        analysis = DocumentAnalysis(source=source, doc_type="json")
        text = self._read_text_content(source, content)

        if source.endswith(".jsonl"):
            # Parse JSONL
            records = []
            for line in text.strip().split("\n"):
                if line.strip():
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

            analysis.metadata["record_count"] = len(records)
            analysis.metadata["format"] = "jsonl"

            if records:
                # Analyze structure from first record
                first = records[0]
                analysis.chunks.append(
                    DocumentChunk(
                        content=f"Schema: {json.dumps(self._infer_schema(first), indent=2)}",
                        chunk_type="metadata",
                    )
                )

                # Sample records
                sample = records[:5]
                analysis.chunks.append(
                    DocumentChunk(
                        content=json.dumps(sample, indent=2),
                        chunk_type="text",
                        metadata={"sample_size": len(sample)},
                    )
                )
        else:
            # Parse JSON
            data = json.loads(text)
            analysis.metadata["format"] = "json"

            if isinstance(data, list):
                analysis.metadata["record_count"] = len(data)
                analysis.chunks.append(
                    DocumentChunk(content=f"Array with {len(data)} elements", chunk_type="metadata")
                )
                if data:
                    analysis.chunks.append(
                        DocumentChunk(
                            content=f"Schema: {json.dumps(self._infer_schema(data[0]), indent=2)}",
                            chunk_type="metadata",
                        )
                    )
            elif isinstance(data, dict):
                analysis.metadata["keys"] = list(data.keys())
                analysis.chunks.append(
                    DocumentChunk(
                        content=f"Object with keys: {', '.join(data.keys())}", chunk_type="metadata"
                    )
                )

            # Full content (truncated if large)
            content_str = json.dumps(data, indent=2)
            if len(content_str) > 10000:
                content_str = content_str[:10000] + "\n... [truncated]"
            analysis.chunks.append(DocumentChunk(content=content_str, chunk_type="text"))

        return analysis

    def _infer_schema(self, obj: Any) -> dict:
        """Infer a simple schema from a JSON object"""
        if isinstance(obj, dict):
            return {k: type(v).__name__ for k, v in obj.items()}
        elif isinstance(obj, list):
            if obj:
                return {"type": "array", "items": type(obj[0]).__name__}
            return {"type": "array", "items": "unknown"}
        return {"type": type(obj).__name__}

    # ===== Markdown Analysis =====

    async def _analyze_markdown(
        self, source: str, content: Optional[bytes] = None
    ) -> DocumentAnalysis:
        """Analyze Markdown document"""
        analysis = DocumentAnalysis(source=source, doc_type="markdown")
        text = self._read_text_content(source, content)

        # Extract headings
        headings = re.findall(r"^(#{1,6})\s+(.+)$", text, re.MULTILINE)
        analysis.metadata["headings"] = [{"level": len(h[0]), "text": h[1]} for h in headings]

        # Split by sections
        sections = re.split(r"^(#{1,6}\s+.+)$", text, flags=re.MULTILINE)

        current_heading = "Introduction"
        for _i, section in enumerate(sections):
            if re.match(r"^#{1,6}\s+", section):
                current_heading = section.strip().lstrip("#").strip()
            elif section.strip():
                # Check for code blocks
                code_blocks = re.findall(r"```(\w*)\n(.*?)```", section, re.DOTALL)
                if code_blocks:
                    for lang, code in code_blocks:
                        analysis.chunks.append(
                            DocumentChunk(
                                content=code.strip(),
                                section=current_heading,
                                chunk_type="code",
                                metadata={"language": lang or "unknown"},
                            )
                        )

                # Add text content
                clean_text = re.sub(r"```\w*\n.*?```", "", section, flags=re.DOTALL).strip()
                if clean_text:
                    analysis.chunks.append(
                        DocumentChunk(
                            content=clean_text, section=current_heading, chunk_type="text"
                        )
                    )

        return analysis

    # ===== HTML Analysis =====

    async def _analyze_html(self, source: str, content: Optional[bytes] = None) -> DocumentAnalysis:
        """Analyze HTML document"""
        analysis = DocumentAnalysis(source=source, doc_type="html")
        text = self._read_text_content(source, content)

        if self._capabilities.get("html"):
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(text, "html.parser")

            # Extract title
            title_tag = soup.find("title")
            if title_tag:
                analysis.metadata["title"] = title_tag.get_text()

            # Extract headings
            for level in range(1, 7):
                for heading in soup.find_all(f"h{level}"):
                    analysis.chunks.append(
                        DocumentChunk(
                            content=heading.get_text(),
                            chunk_type="heading",
                            metadata={"level": level},
                        )
                    )

            # Extract main text content
            for tag in soup.find_all(["p", "li", "td", "th"]):
                text_content = tag.get_text(strip=True)
                if text_content and len(text_content) > 10:
                    analysis.chunks.append(DocumentChunk(content=text_content, chunk_type="text"))

            # Extract tables
            for table in soup.find_all("table"):
                rows = []
                for tr in table.find_all("tr"):
                    cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                    if cells:
                        rows.append(cells)
                if rows:
                    analysis.chunks.append(
                        DocumentChunk(content=self._format_table(rows), chunk_type="table")
                    )

            # Extract links
            links = []
            for a in soup.find_all("a", href=True):
                links.append({"text": a.get_text(strip=True), "href": a["href"]})
            if links:
                analysis.metadata["links"] = links[:50]  # Limit

        else:
            # Fallback: basic text extraction
            clean = re.sub(r"<[^>]+>", " ", text)
            clean = re.sub(r"\s+", " ", clean).strip()
            analysis.chunks.append(DocumentChunk(content=clean, chunk_type="text"))

        return analysis

    # ===== Code Analysis =====

    async def _analyze_code(self, source: str, content: Optional[bytes] = None) -> DocumentAnalysis:
        """Analyze source code file"""
        analysis = DocumentAnalysis(source=source, doc_type="code")
        text = self._read_text_content(source, content)

        ext = Path(source).suffix.lower()
        language = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".c": "c",
            ".cpp": "cpp",
            ".rb": "ruby",
        }.get(ext, "unknown")

        analysis.metadata["language"] = language
        analysis.metadata["line_count"] = text.count("\n") + 1
        analysis.metadata["char_count"] = len(text)

        # Extract structure based on language
        if language == "python":
            # Extract classes and functions
            classes = re.findall(r"^class\s+(\w+)", text, re.MULTILINE)
            functions = re.findall(r"^def\s+(\w+)", text, re.MULTILINE)
            imports = re.findall(r"^(?:from\s+\S+\s+)?import\s+(.+)$", text, re.MULTILINE)

            analysis.metadata["classes"] = classes
            analysis.metadata["functions"] = functions
            analysis.metadata["imports"] = [i.strip() for i in imports]

            analysis.chunks.append(
                DocumentChunk(
                    content=f"Classes: {', '.join(classes)}\nFunctions: {', '.join(functions)}",
                    chunk_type="metadata",
                )
            )

        elif language in ("javascript", "typescript"):
            # Extract exports, classes, functions
            exports = re.findall(
                r"export\s+(?:default\s+)?(?:class|function|const|let|var)\s+(\w+)", text
            )
            classes = re.findall(r"class\s+(\w+)", text)
            functions = re.findall(
                r"(?:function|const|let|var)\s+(\w+)\s*(?:=\s*(?:async\s*)?\(|[\(])", text
            )

            analysis.metadata["exports"] = exports
            analysis.metadata["classes"] = classes
            analysis.metadata["functions"] = functions

        # Add full source as a code chunk
        analysis.chunks.append(
            DocumentChunk(content=text, chunk_type="code", metadata={"language": language})
        )

        return analysis

    # ===== Text Analysis =====

    async def _analyze_text(self, source: str, content: Optional[bytes] = None) -> DocumentAnalysis:
        """Analyze plain text file"""
        analysis = DocumentAnalysis(source=source, doc_type="text")
        text = self._read_text_content(source, content)

        analysis.metadata["line_count"] = text.count("\n") + 1
        analysis.metadata["char_count"] = len(text)
        analysis.metadata["word_count"] = len(text.split())

        # Split into paragraphs
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        for i, para in enumerate(paragraphs):
            analysis.chunks.append(
                DocumentChunk(content=para, chunk_type="text", metadata={"paragraph_index": i})
            )

        return analysis

    # ===== Utility Methods =====

    def _format_table(self, rows: list[list[str]]) -> str:
        """Format table rows into readable text"""
        if not rows:
            return ""

        # Calculate column widths
        col_widths = [0] * max(len(row) for row in rows)
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell or "")))

        # Format rows
        lines = []
        for i, row in enumerate(rows):
            cells = [str(cell or "").ljust(col_widths[j]) for j, cell in enumerate(row)]
            lines.append(" | ".join(cells))
            if i == 0:
                lines.append("-+-".join("-" * w for w in col_widths))

        return "\n".join(lines)

    async def analyze_directory(
        self,
        directory: str,
        extensions: Optional[list[str]] = None,
        recursive: bool = True,
        max_files: int = 100,
    ) -> list[DocumentAnalysis]:
        """
        Analyze all documents in a directory.

        Args:
            directory: Directory path
            extensions: File extensions to include (None = all supported)
            recursive: Search recursively
            max_files: Maximum files to analyze

        Returns:
            List of DocumentAnalysis for each file
        """
        path = Path(directory)
        if not path.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        supported_extensions = extensions or [
            ".pdf",
            ".csv",
            ".json",
            ".jsonl",
            ".md",
            ".html",
            ".py",
            ".js",
            ".ts",
            ".txt",
            ".yaml",
            ".yml",
        ]

        files = []
        pattern = "**/*" if recursive else "*"
        for file_path in path.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                files.append(str(file_path))
                if len(files) >= max_files:
                    break

        results = []
        for file_path in files:
            try:
                analysis = await self.analyze(file_path)
                results.append(analysis)
            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")

        logger.info(f"Analyzed {len(results)}/{len(files)} files in {directory}")
        return results


# Global document intelligence instance
doc_intelligence = DocumentIntelligence()
