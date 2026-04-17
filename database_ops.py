"""
Database Operations - Tier 4 Tool Use
Autonomous SQL/NoSQL/Vector database operations
"""

import json
import sqlite3
from dataclasses import dataclass, field
from typing import Any, Optional

from loguru import logger

from config import settings


@dataclass
class QueryResult:
    """Result of a database query"""

    success: bool
    data: Optional[list[dict]] = None
    columns: Optional[list[str]] = None
    row_count: int = 0
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    query: str = ""


@dataclass
class SchemaInfo:
    """Database schema information"""

    tables: list[dict[str, Any]] = field(default_factory=list)
    total_tables: int = 0
    database_type: str = ""
    database_path: str = ""


class DatabaseOperations:
    """
    Autonomous database operations for SQL, NoSQL, and vector databases.

    Capabilities:
    - Schema inspection
    - Complex SQL queries (SELECT, INSERT, UPDATE, DELETE)
    - Bulk operations
    - Transaction management
    - Query result formatting
    - Vector database queries via ChromaDB
    """

    def __init__(self):
        self._connections: dict[str, Any] = {}
        self.query_history: list[QueryResult] = []

    # ===== SQLite Operations =====

    def get_sqlite_connection(self, db_path: Optional[str] = None) -> sqlite3.Connection:
        """Get or create SQLite connection"""
        path = db_path or str(settings.memory_db_path)

        if path not in self._connections:
            conn = sqlite3.connect(path)
            conn.row_factory = sqlite3.Row
            self._connections[path] = conn

        return self._connections[path]

    def inspect_schema(self, db_path: Optional[str] = None) -> SchemaInfo:
        """
        Inspect database schema - tables, columns, types, indexes.

        Args:
            db_path: Path to SQLite database (uses default if None)

        Returns:
            SchemaInfo with complete schema details
        """
        conn = self.get_sqlite_connection(db_path)
        info = SchemaInfo(
            database_type="sqlite", database_path=db_path or str(settings.memory_db_path)
        )

        try:
            # Get all tables
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]

            for table_name in tables:
                # Get columns
                cursor = conn.execute(f"PRAGMA table_info('{table_name}')")
                columns = [
                    {
                        "name": row[1],
                        "type": row[2],
                        "not_null": bool(row[3]),
                        "default": row[4],
                        "primary_key": bool(row[5]),
                    }
                    for row in cursor.fetchall()
                ]

                # Get row count
                cursor = conn.execute(f"SELECT COUNT(*) FROM '{table_name}'")  # noqa: S608
                row_count = cursor.fetchone()[0]

                # Get indexes
                cursor = conn.execute(f"PRAGMA index_list('{table_name}')")
                indexes = [row[1] for row in cursor.fetchall()]

                info.tables.append(
                    {
                        "name": table_name,
                        "columns": columns,
                        "row_count": row_count,
                        "indexes": indexes,
                    }
                )

            info.total_tables = len(tables)

        except Exception as e:
            logger.error(f"Schema inspection failed: {e}")

        return info

    def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
        db_path: Optional[str] = None,
        read_only: bool = False,
    ) -> QueryResult:
        """
        Execute a SQL query.

        Args:
            query: SQL query string
            params: Query parameters (for parameterized queries)
            db_path: Database path
            read_only: If True, reject write operations

        Returns:
            QueryResult with data and metadata
        """
        import time

        start = time.time()

        result = QueryResult(success=False, query=query)

        # Safety check for read-only mode
        if read_only:
            query_upper = query.strip().upper()
            write_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE"]
            if any(query_upper.startswith(kw) for kw in write_keywords):
                result.error = "Write operations not allowed in read-only mode"
                return result

        try:
            conn = self.get_sqlite_connection(db_path)
            cursor = conn.execute(query, params or ())

            if query.strip().upper().startswith("SELECT"):
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []

                result.data = [dict(row) for row in rows]
                result.columns = columns
                result.row_count = len(rows)
            else:
                conn.commit()
                result.row_count = cursor.rowcount

            result.success = True

        except Exception as e:
            result.error = str(e)
            logger.error(f"Query failed: {e}\nQuery: {query}")

        result.execution_time_ms = (time.time() - start) * 1000

        # Log query
        self.query_history.append(result)
        if len(self.query_history) > 100:
            self.query_history = self.query_history[-50:]

        return result

    def bulk_insert(
        self, table: str, rows: list[dict[str, Any]], db_path: Optional[str] = None
    ) -> QueryResult:
        """
        Bulk insert rows into a table.

        Args:
            table: Table name
            rows: List of row dictionaries
            db_path: Database path

        Returns:
            QueryResult with insert count
        """
        if not rows:
            return QueryResult(success=True, row_count=0, query="bulk_insert")

        import time

        start = time.time()

        result = QueryResult(success=False, query=f"BULK INSERT INTO {table}")

        try:
            conn = self.get_sqlite_connection(db_path)

            columns = list(rows[0].keys())
            placeholders = ", ".join(["?"] * len(columns))
            column_names = ", ".join(columns)

            query = f"INSERT INTO {table} ({column_names}) VALUES ({placeholders})"  # noqa: S608
            values = [tuple(row.get(col) for col in columns) for row in rows]

            conn.executemany(query, values)
            conn.commit()

            result.success = True
            result.row_count = len(rows)

        except Exception as e:
            result.error = str(e)
            logger.error(f"Bulk insert failed: {e}")

        result.execution_time_ms = (time.time() - start) * 1000
        return result

    def execute_transaction(
        self, queries: list[dict[str, Any]], db_path: Optional[str] = None
    ) -> list[QueryResult]:
        """
        Execute multiple queries in a single transaction.

        Args:
            queries: List of {"query": "...", "params": (...)} dicts
            db_path: Database path

        Returns:
            List of QueryResult for each query
        """
        results = []
        conn = self.get_sqlite_connection(db_path)
        cursor = conn.cursor()

        try:
            conn.execute("BEGIN TRANSACTION")

            for q in queries:
                query = q["query"]
                params = q.get("params") or ()

                try:
                    cursor.execute(query, params)

                    if query.strip().upper().startswith("SELECT"):
                        rows = cursor.fetchall()
                        columns = (
                            [description[0] for description in cursor.description]
                            if cursor.description
                            else []
                        )
                        data = [dict(zip(columns, row)) for row in rows]
                        result = QueryResult(
                            success=True,
                            data=data,
                            columns=columns,
                            row_count=len(data),
                            query=query,
                        )
                    else:
                        result = QueryResult(
                            success=True,
                            row_count=cursor.rowcount if cursor.rowcount != -1 else 0,
                            query=query,
                        )

                    results.append(result)

                except Exception as e:
                    result = QueryResult(success=False, error=str(e), query=query)
                    results.append(result)
                    conn.execute("ROLLBACK")
                    logger.warning(f"Transaction rolled back due to: {result.error}")
                    return results

            conn.execute("COMMIT")
            logger.info(f"Transaction committed: {len(queries)} queries")

        except Exception as e:
            conn.execute("ROLLBACK")
            logger.error(f"Transaction failed: {e}")
            results.append(QueryResult(success=False, error=str(e), query="TRANSACTION"))

        return results

    # ===== PostgreSQL Operations =====

    async def execute_postgres(self, query: str, params: Optional[tuple] = None) -> QueryResult:
        """Execute query on configured PostgreSQL database"""
        import time

        start = time.time()

        result = QueryResult(success=False, query=query)

        if not settings.postgres_url:
            result.error = "PostgreSQL URL not configured. Set POSTGRES_URL in your .env file."
            return result

        try:
            import psycopg2

            conn = psycopg2.connect(settings.postgres_url)
            cursor = conn.cursor()

            cursor.execute(query, params)

            if query.strip().upper().startswith("SELECT"):
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                result.data = [dict(zip(columns, row)) for row in rows]
                result.columns = columns
                result.row_count = len(rows)
            else:
                conn.commit()
                result.row_count = cursor.rowcount

            result.success = True
            cursor.close()
            conn.close()

        except ImportError:
            result.error = "psycopg2 not installed"
        except Exception as e:
            result.error = str(e)
            logger.error(f"PostgreSQL query failed: {e}")

        result.execution_time_ms = (time.time() - start) * 1000
        return result

    # ===== Vector Database Operations =====

    def vector_search(
        self, query: str, collection: str = "knowledge", n_results: int = 10
    ) -> QueryResult:
        """
        Semantic search in vector database.

        Args:
            query: Search query
            collection: ChromaDB collection name
            n_results: Number of results

        Returns:
            QueryResult with matching documents
        """
        import time

        start = time.time()

        result = QueryResult(success=False, query=f"VECTOR_SEARCH({collection}): {query}")

        try:
            from vector_memory import get_vector_memory

            vm = get_vector_memory()

            search_func = {
                "conversations": vm.search_conversations,
                "skills": vm.search_skills,
                "knowledge": vm.search_knowledge,
            }.get(collection)

            if search_func:
                results = search_func(query, n_results=n_results)
                result.data = results
                result.row_count = len(results)
                result.success = True
            else:
                result.error = f"Unknown collection: {collection}"

        except Exception as e:
            result.error = str(e)
            logger.error(f"Vector search failed: {e}")

        result.execution_time_ms = (time.time() - start) * 1000
        return result

    # ===== Utility Methods =====

    def format_results(self, result: QueryResult, fmt: str = "table") -> str:
        """
        Format query results for display.

        Args:
            result: QueryResult to format
            format: Output format (table, json, csv)

        Returns:
            Formatted string
        """
        if not result.success:
            return f"Error: {result.error}"

        if not result.data:
            return f"No results ({result.row_count} rows affected)"

        if fmt == "json":
            return json.dumps(result.data, indent=2, default=str)

        elif fmt == "csv":
            if not result.columns:
                return json.dumps(result.data, default=str)
            lines = [",".join(result.columns)]
            for row in result.data:
                lines.append(",".join(str(row.get(c, "")) for c in result.columns))
            return "\n".join(lines)

        else:  # table format
            if not result.columns:
                return json.dumps(result.data, indent=2, default=str)

            # Calculate column widths
            widths = {c: len(c) for c in result.columns}
            for row in result.data[:50]:  # Limit for display
                for c in result.columns:
                    val = str(row.get(c, ""))
                    widths[c] = max(widths[c], min(len(val), 50))

            # Header
            header = " | ".join(c.ljust(widths[c]) for c in result.columns)
            separator = "-+-".join("-" * widths[c] for c in result.columns)

            # Rows
            rows = []
            for row in result.data[:50]:
                cells = []
                for c in result.columns:
                    val = str(row.get(c, ""))
                    if len(val) > 50:
                        val = val[:47] + "..."
                    cells.append(val.ljust(widths[c]))
                rows.append(" | ".join(cells))

            lines = [header, separator] + rows
            if len(result.data) > 50:
                lines.append(f"... and {len(result.data) - 50} more rows")

            return "\n".join(lines)

    def close_all(self):
        """Close all database connections"""
        for path, conn in self._connections.items():
            try:
                conn.close()
            except Exception as e:
                logger.warning(f"Failed to close connection {path}: {e}")
        self._connections.clear()


# Global database operations instance
db_ops = DatabaseOperations()
