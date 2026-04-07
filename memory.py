"""
Big Homie Memory System
Three-layer architecture: Session, Long-term, Skills
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from loguru import logger
from config import settings

class MemorySystem:
    """Unified memory management for Big Homie"""

    def __init__(self):
        self.db_path = Path(settings.memory_db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def _conn(self):
        """Get database connection"""
        return sqlite3.connect(str(self.db_path))

    def init_db(self):
        """Initialize database schema"""
        with self._conn() as db:
            # Session memory - immediate context
            db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    timestamp TEXT,
                    role TEXT,
                    content TEXT,
                    metadata TEXT
                )
            """)

            # Long-term memory - facts, preferences, history
            db.execute("""
                CREATE TABLE IF NOT EXISTS long_term_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE,
                    value TEXT,
                    category TEXT,
                    importance INTEGER DEFAULT 5,
                    access_count INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)

            # Skills - learned workflows
            db.execute("""
                CREATE TABLE IF NOT EXISTS skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    description TEXT,
                    workflow TEXT,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    avg_duration REAL,
                    created_at TEXT,
                    last_used TEXT
                )
            """)

            # Task history
            db.execute("""
                CREATE TABLE IF NOT EXISTS task_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task TEXT,
                    domain TEXT,
                    status TEXT,
                    result TEXT,
                    cost REAL,
                    duration REAL,
                    timestamp TEXT
                )
            """)

            # User preferences
            db.execute("""
                CREATE TABLE IF NOT EXISTS preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT
                )
            """)

            db.commit()
            logger.info(f"Memory database initialized at {self.db_path}")

    # ===== Session Memory =====

    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """Add message to session memory"""
        with self._conn() as db:
            db.execute(
                "INSERT INTO sessions (session_id, timestamp, role, content, metadata) VALUES (?, ?, ?, ?, ?)",
                (session_id, datetime.utcnow().isoformat(), role, content, json.dumps(metadata or {}))
            )
            db.commit()

    def get_session_messages(self, session_id: str, limit: int = 50) -> List[Dict]:
        """Get recent messages from session"""
        with self._conn() as db:
            rows = db.execute(
                "SELECT role, content, metadata, timestamp FROM sessions WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, limit)
            ).fetchall()

        return [
            {
                "role": r[0],
                "content": r[1],
                "metadata": json.loads(r[2]),
                "timestamp": r[3]
            }
            for r in reversed(rows)
        ]

    def clear_session(self, session_id: str):
        """Clear session memory"""
        with self._conn() as db:
            db.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            db.commit()

    # ===== Long-term Memory =====

    def store(self, key: str, value: Any, category: str = "general", importance: int = 5):
        """Store long-term memory"""
        with self._conn() as db:
            now = datetime.utcnow().isoformat()
            db.execute(
                """INSERT OR REPLACE INTO long_term_memory
                   (key, value, category, importance, access_count, created_at, updated_at)
                   VALUES (?, ?, ?, ?,
                           COALESCE((SELECT access_count FROM long_term_memory WHERE key = ?), 0),
                           COALESCE((SELECT created_at FROM long_term_memory WHERE key = ?), ?),
                           ?)""",
                (key, json.dumps(value), category, importance, key, key, now, now)
            )
            db.commit()

    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve from long-term memory"""
        with self._conn() as db:
            # Increment access count
            db.execute("UPDATE long_term_memory SET access_count = access_count + 1 WHERE key = ?", (key,))
            db.commit()

            row = db.execute("SELECT value FROM long_term_memory WHERE key = ?", (key,)).fetchone()
            return json.loads(row[0]) if row else None

    def search_memory(self, category: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """Search long-term memory"""
        with self._conn() as db:
            if category:
                rows = db.execute(
                    "SELECT key, value, category, importance, access_count FROM long_term_memory WHERE category = ? ORDER BY importance DESC, access_count DESC LIMIT ?",
                    (category, limit)
                ).fetchall()
            else:
                rows = db.execute(
                    "SELECT key, value, category, importance, access_count FROM long_term_memory ORDER BY importance DESC, access_count DESC LIMIT ?",
                    (limit,)
                ).fetchall()

        return [
            {
                "key": r[0],
                "value": json.loads(r[1]),
                "category": r[2],
                "importance": r[3],
                "access_count": r[4]
            }
            for r in rows
        ]

    # ===== Skills =====

    def save_skill(self, name: str, description: str, workflow: List[Dict]):
        """Save a learned skill"""
        with self._conn() as db:
            now = datetime.utcnow().isoformat()
            db.execute(
                """INSERT OR REPLACE INTO skills
                   (name, description, workflow, success_count, created_at, last_used)
                   VALUES (?, ?, ?,
                           COALESCE((SELECT success_count FROM skills WHERE name = ?), 0),
                           COALESCE((SELECT created_at FROM skills WHERE name = ?), ?),
                           ?)""",
                (name, description, json.dumps(workflow), name, name, now, now)
            )
            db.commit()
            logger.info(f"Skill saved: {name}")

    def get_skill(self, name: str) -> Optional[Dict]:
        """Retrieve a skill"""
        with self._conn() as db:
            db.execute("UPDATE skills SET last_used = ? WHERE name = ?", (datetime.utcnow().isoformat(), name))
            db.commit()

            row = db.execute(
                "SELECT description, workflow, success_count FROM skills WHERE name = ?",
                (name,)
            ).fetchone()

            if row:
                return {
                    "name": name,
                    "description": row[0],
                    "workflow": json.loads(row[1]),
                    "success_count": row[2]
                }
            return None

    def list_skills(self) -> List[Dict]:
        """List all skills"""
        with self._conn() as db:
            rows = db.execute(
                "SELECT name, description, success_count, last_used FROM skills ORDER BY success_count DESC"
            ).fetchall()

        return [
            {
                "name": r[0],
                "description": r[1],
                "success_count": r[2],
                "last_used": r[3]
            }
            for r in rows
        ]

    def record_skill_result(self, name: str, success: bool, duration: float):
        """Record skill execution result"""
        with self._conn() as db:
            if success:
                db.execute(
                    "UPDATE skills SET success_count = success_count + 1, last_used = ? WHERE name = ?",
                    (datetime.utcnow().isoformat(), name)
                )
            else:
                db.execute(
                    "UPDATE skills SET failure_count = failure_count + 1 WHERE name = ?",
                    (name,)
                )
            db.commit()

    # ===== Task History =====

    def log_task(self, task: str, domain: str, status: str, result: Any, cost: float = 0.0, duration: float = 0.0):
        """Log task execution"""
        with self._conn() as db:
            db.execute(
                "INSERT INTO task_history (task, domain, status, result, cost, duration, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (task, domain, status, json.dumps(result), cost, duration, datetime.utcnow().isoformat())
            )
            db.commit()

    def get_task_history(self, limit: int = 50) -> List[Dict]:
        """Get recent task history"""
        with self._conn() as db:
            rows = db.execute(
                "SELECT task, domain, status, result, cost, duration, timestamp FROM task_history ORDER BY id DESC LIMIT ?",
                (limit,)
            ).fetchall()

        return [
            {
                "task": r[0],
                "domain": r[1],
                "status": r[2],
                "result": json.loads(r[3]),
                "cost": r[4],
                "duration": r[5],
                "timestamp": r[6]
            }
            for r in rows
        ]

    # ===== Preferences =====

    def set_preference(self, key: str, value: Any):
        """Set user preference"""
        with self._conn() as db:
            db.execute(
                "INSERT OR REPLACE INTO preferences (key, value, updated_at) VALUES (?, ?, ?)",
                (key, json.dumps(value), datetime.utcnow().isoformat())
            )
            db.commit()

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference"""
        with self._conn() as db:
            row = db.execute("SELECT value FROM preferences WHERE key = ?", (key,)).fetchone()
            return json.loads(row[0]) if row else default

# Global memory instance
memory = MemorySystem()
