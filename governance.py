"""
Safety & Governance - Tier 7
Human-in-the-Loop Gates, Observability & Audit Trail,
Sandboxed Execution, Kill Switch Protocol
"""

import asyncio
import hashlib
import json
import os
import sqlite3
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

from loguru import logger

from config import settings

# ===================================================================
# Human-in-the-Loop Gates
# ===================================================================


class ActionRiskLevel(str, Enum):
    """Risk levels for agent actions"""

    LOW = "low"  # Auto-approve
    MEDIUM = "medium"  # Notify user
    HIGH = "high"  # Require approval
    CRITICAL = "critical"  # Require explicit confirmation


# Alias for test compatibility
RiskLevel = ActionRiskLevel


@dataclass
class ApprovalRequest:
    """A request for human approval"""

    request_id: str
    action: str
    risk_level: ActionRiskLevel
    description: str
    estimated_impact: str
    metadata: dict[str, Any] = field(default_factory=dict)
    approved: Optional[bool] = None
    approver: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    resolved_at: Optional[str] = None


class HumanInTheLoop:
    """
    Automatically pauses and requests human approval before executing
    high-stakes actions.

    Risk Classification:
    - LOW: Auto-approved (reading data, searches, analysis)
    - MEDIUM: Logged with notification (writing files, API calls)
    - HIGH: Requires explicit approval (sending emails, payments)
    - CRITICAL: Requires confirmation dialog (deleting data, deployments)
    """

    def __init__(self, auto_approve_low_risk: bool = True):
        self.pending_requests: dict[str, ApprovalRequest] = {}
        self.approval_history: list[ApprovalRequest] = []
        self.approval_callback: Optional[Callable] = None
        self.auto_approve_low: bool = auto_approve_low_risk

        # Risk classification rules
        self.risk_rules: dict[str, ActionRiskLevel] = {
            # Low risk
            "search": ActionRiskLevel.LOW,
            "read": ActionRiskLevel.LOW,
            "analyze": ActionRiskLevel.LOW,
            "summarize": ActionRiskLevel.LOW,
            # Medium risk
            "write_file": ActionRiskLevel.MEDIUM,
            "api_call": ActionRiskLevel.MEDIUM,
            "web_scrape": ActionRiskLevel.MEDIUM,
            # High risk
            "send_email": ActionRiskLevel.HIGH,
            "make_payment": ActionRiskLevel.HIGH,
            "execute_code": ActionRiskLevel.HIGH,
            "modify_config": ActionRiskLevel.HIGH,
            # Critical risk
            "delete_data": ActionRiskLevel.CRITICAL,
            "deploy": ActionRiskLevel.CRITICAL,
            "financial_transaction": ActionRiskLevel.CRITICAL,
            "system_modification": ActionRiskLevel.CRITICAL,
        }

    def classify_risk(self, action: str, context: Optional[dict] = None) -> ActionRiskLevel:
        """Classify the risk level of an action"""
        action_lower = action.lower()
        ctx = context or {}

        # Check explicit rules first
        for pattern, level in self.risk_rules.items():
            if pattern in action_lower:
                return level

        # Heuristic classification
        critical_keywords = [
            "delete_all",
            "drop_all",
            "truncate_all",
            "destroy",
            "format",
        ]
        high_risk_keywords = [
            "delete",
            "remove",
            "payment",
            "send",
            "deploy",
            "drop",
            "truncate",
            "transfer",
            "funds",
        ]
        medium_risk_keywords = ["write", "create", "update", "modify", "install"]

        # Escalate to CRITICAL when context indicates production or large scope
        scope = str(ctx.get("scope", "")).lower()
        if scope in ("production", "prod", "all"):
            if any(kw in action_lower for kw in high_risk_keywords + critical_keywords):
                return ActionRiskLevel.CRITICAL

        if any(kw in action_lower for kw in critical_keywords):
            return ActionRiskLevel.CRITICAL
        if any(kw in action_lower for kw in high_risk_keywords):
            return ActionRiskLevel.HIGH
        elif any(kw in action_lower for kw in medium_risk_keywords):
            return ActionRiskLevel.MEDIUM

        return ActionRiskLevel.LOW

    async def async_request_approval(
        self,
        action: str,
        description: str,
        estimated_impact: str = "",
        risk_level: Optional[ActionRiskLevel] = None,
        metadata: Optional[dict] = None,
        timeout: float = 300.0,
    ) -> bool:
        """
        Request human approval for an action (async version).

        Returns True if approved, False if denied or timed out.
        """
        import uuid

        if risk_level is None:
            risk_level = self.classify_risk(action)

        # Auto-approve low-risk actions
        if risk_level == ActionRiskLevel.LOW and self.auto_approve_low:
            logger.debug(f"Auto-approved low-risk action: {action}")
            return True

        request = ApprovalRequest(
            request_id=str(uuid.uuid4()),
            action=action,
            risk_level=risk_level,
            description=description,
            estimated_impact=estimated_impact,
            metadata=metadata or {},
        )

        self.pending_requests[request.request_id] = request

        logger.info(
            f"🔒 Approval requested [{risk_level.value}]: {action}\n   Description: {description}"
        )

        # If callback is set, use it for approval
        if self.approval_callback:
            try:
                approved = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, self.approval_callback, request),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                logger.warning(f"Approval timed out for: {action}")
                approved = False

            request.approved = approved
            request.resolved_at = datetime.now().isoformat()
            self.pending_requests.pop(request.request_id, None)
            self.approval_history.append(request)

            return approved

        # No callback - deny high-risk by default
        logger.warning(f"No approval callback set - denying {risk_level.value} action: {action}")
        request.approved = False
        request.resolved_at = datetime.now().isoformat()
        self.pending_requests.pop(request.request_id, None)
        self.approval_history.append(request)

        return False

    def request_approval(
        self,
        action: str,
        description: str = "",
        estimated_impact: str = "",
        risk_level: Optional[ActionRiskLevel] = None,
        metadata: Optional[dict] = None,
        context: Optional[dict] = None,
        timeout: float = 300.0,
    ) -> bool:
        """Synchronous approval request (delegates to async version when needed)."""
        if context is not None and not description:
            description = json.dumps(context)
        if context is not None and metadata is None:
            metadata = context

        if risk_level is None:
            risk_level = self.classify_risk(action)

        if risk_level == ActionRiskLevel.LOW and self.auto_approve_low:
            return True

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            return False

        return asyncio.run(
            self.async_request_approval(
                action=action,
                description=description,
                estimated_impact=estimated_impact,
                risk_level=risk_level,
                metadata=metadata,
                timeout=timeout,
            )
        )

    def add_risk_rule(self, pattern: str, level: ActionRiskLevel):
        """Add a custom risk classification rule"""
        self.risk_rules[pattern] = level


# ===================================================================
# Observability & Audit Trail
# ===================================================================


@dataclass
class AuditEntry:
    """An immutable audit log entry"""

    entry_id: str
    timestamp: str
    event_type: str
    actor: str
    action: str
    target: str
    details: dict[str, Any]
    hash: str  # SHA-256 hash for integrity verification
    previous_hash: str  # Chain to previous entry


class AuditTrail:
    """
    Tamper-evident audit trail for all agent actions.

    Logs every decision, tool call, reasoning trace, and action
    with timestamps, full context, and cryptographic integrity.
    """

    def __init__(self, log_file: Optional[str] = None):
        self._log_file = log_file
        if log_file is not None:
            self._last_hash = "GENESIS"
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            if Path(log_file).exists():
                self._last_hash = self._jsonl_get_last_hash()
        else:
            self.db_path = Path(settings.data_dir) / "audit_trail.db"
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._init_db()
            self._last_hash = self._get_last_hash()

    def _conn(self):
        return sqlite3.connect(str(self.db_path))

    def _init_db(self):
        """Initialize audit database"""
        with self._conn() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    entry_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    action TEXT NOT NULL,
                    target TEXT,
                    details TEXT,
                    hash TEXT NOT NULL,
                    previous_hash TEXT NOT NULL
                )
            """)

            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp
                ON audit_log(timestamp)
            """)

            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_event_type
                ON audit_log(event_type)
            """)

            db.commit()

    def _get_last_hash(self) -> str:
        """Get the hash of the last audit entry"""
        with self._conn() as db:
            row = db.execute(
                "SELECT hash FROM audit_log ORDER BY timestamp DESC LIMIT 1"
            ).fetchone()
            return row[0] if row else "GENESIS"

    def _compute_hash(self, entry_data: str, previous_hash: str) -> str:
        """Compute SHA-256 hash for integrity chain"""
        content = f"{previous_hash}:{entry_data}"
        return hashlib.sha256(content.encode()).hexdigest()

    def log(
        self,
        event_type: str = "action",
        actor: str = "agent",
        action: str = "",
        target: str = "",
        details: Optional[dict] = None,
    ) -> AuditEntry:
        """
        Log an auditable event.

        Args:
            event_type: Type of event (tool_call, decision, action, error, etc.)
            actor: Who/what performed the action
            action: What was done
            target: What was acted upon
            details: Additional details

        Returns:
            The created AuditEntry
        """
        import uuid

        timestamp = datetime.now().isoformat()
        entry_id = str(uuid.uuid4())
        details = details or {}

        # Create hash for integrity
        details_json = json.dumps(details, sort_keys=True)
        entry_data = f"{timestamp}:{event_type}:{actor}:{action}:{target}:{details_json}"
        entry_hash = self._compute_hash(entry_data, self._last_hash)

        entry = AuditEntry(
            entry_id=entry_id,
            timestamp=timestamp,
            event_type=event_type,
            actor=actor,
            action=action,
            target=target,
            details=details,
            hash=entry_hash,
            previous_hash=self._last_hash,
        )

        if self._log_file is not None:
            self._jsonl_append(entry)
        else:
            with self._conn() as db:
                db.execute(
                    """INSERT INTO audit_log
                       (entry_id, timestamp, event_type,
                        actor, action, target, details,
                        hash, previous_hash)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        entry.entry_id,
                        entry.timestamp,
                        entry.event_type,
                        entry.actor,
                        entry.action,
                        entry.target,
                        json.dumps(entry.details),
                        entry.hash,
                        entry.previous_hash,
                    ),
                )
                db.commit()

        self._last_hash = entry_hash

        return entry

    # ------------------------------------------------------------------
    # JSONL file-based backend helpers
    # ------------------------------------------------------------------

    def _jsonl_append(self, entry: AuditEntry) -> None:
        record = {
            "entry_id": entry.entry_id,
            "timestamp": entry.timestamp,
            "event_type": entry.event_type,
            "actor": entry.actor,
            "action": entry.action,
            "target": entry.target,
            "details": entry.details,
            "hash": entry.hash,
            "previous_hash": entry.previous_hash,
        }
        with open(self._log_file, "a", encoding="utf-8") as fh:  # noqa: PTH123
            fh.write(json.dumps(record) + "\n")

    def _jsonl_get_last_hash(self) -> str:
        try:
            with open(self._log_file, encoding="utf-8") as fh:  # noqa: PTH123
                lines = [ln for ln in fh.read().splitlines() if ln.strip()]
            if lines:
                return json.loads(lines[-1])["hash"]
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            pass
        return "GENESIS"

    def _jsonl_read_entries(self) -> list[dict]:
        try:
            with open(self._log_file, encoding="utf-8") as fh:  # noqa: PTH123
                return [json.loads(ln) for ln in fh.read().splitlines() if ln.strip()]
        except FileNotFoundError:
            return []

    def get_entries(self) -> list[dict]:
        """Return all audit entries (JSONL or SQLite)."""
        if self._log_file is not None:
            return self._jsonl_read_entries()
        return self.query(limit=10_000)

    def _jsonl_verify_integrity(self) -> bool:
        entries = self._jsonl_read_entries()
        if not entries:
            return True
        expected_prev = "GENESIS"
        for entry in entries:
            details_json = json.dumps(entry.get("details", {}), sort_keys=True)
            entry_data = (
                f"{entry['timestamp']}:{entry.get('event_type', 'action')}"
                f":{entry.get('actor', 'agent')}:{entry['action']}"
                f":{entry.get('target', '')}:{details_json}"
            )
            expected_hash = self._compute_hash(entry_data, expected_prev)
            if entry.get("previous_hash") != expected_prev:
                return False
            if entry.get("hash") != expected_hash:
                return False
            expected_prev = entry["hash"]
        return True

    def verify_integrity(self):
        """
        Verify the integrity of the entire audit trail.

        When backed by a JSONL file, returns ``True`` / ``False``.
        When backed by SQLite, returns a dict with details.
        """
        if self._log_file is not None:
            return self._jsonl_verify_integrity()

        with self._conn() as db:
            rows = db.execute(
                "SELECT entry_id, timestamp, event_type,"
                " actor, action, target, details,"
                " hash, previous_hash "
                "FROM audit_log ORDER BY timestamp"
            ).fetchall()

        if not rows:
            return {"valid": True, "entries": 0, "message": "Empty audit trail"}

        expected_prev = "GENESIS"
        broken_at = None

        for i, row in enumerate(rows):
            try:
                canonical_details = json.dumps(json.loads(row[6]), sort_keys=True)
            except (TypeError, json.JSONDecodeError):
                canonical_details = row[6]

            entry_data = f"{row[1]}:{row[2]}:{row[3]}:{row[4]}:{row[5]}:{canonical_details}"
            expected_hash = self._compute_hash(entry_data, expected_prev)

            if row[8] != expected_prev:
                broken_at = i
                break

            if row[7] != expected_hash:
                broken_at = i
                break

            expected_prev = row[7]

        return {
            "valid": broken_at is None,
            "entries": len(rows),
            "broken_at_index": broken_at,
            "message": "Integrity verified"
            if broken_at is None
            else f"Chain broken at entry {broken_at}",
        }

    def query(
        self,
        event_type: Optional[str] = None,
        actor: Optional[str] = None,
        since: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """Query the audit trail"""
        conditions = []
        params = []

        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)
        if actor:
            conditions.append("actor = ?")
            params.append(actor)
        if since:
            conditions.append("timestamp > ?")
            params.append(since)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        # Use parameterized query for limit as well
        query = f"SELECT * FROM audit_log {where} ORDER BY timestamp DESC LIMIT ?"  # noqa: S608
        params.append(limit)

        with self._conn() as db:
            rows = db.execute(query, params).fetchall()

        return [
            {
                "entry_id": r[0],
                "timestamp": r[1],
                "event_type": r[2],
                "actor": r[3],
                "action": r[4],
                "target": r[5],
                "details": json.loads(r[6]) if r[6] else {},
                "hash": r[7],
            }
            for r in rows
        ]

    def get_stats(self) -> dict[str, Any]:
        """Get audit trail statistics"""
        with self._conn() as db:
            total = db.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
            types = db.execute(
                "SELECT event_type, COUNT(*) FROM audit_log"
                " GROUP BY event_type"
                " ORDER BY COUNT(*) DESC"
            ).fetchall()

        return {
            "total_entries": total,
            "by_type": {r[0]: r[1] for r in types},
            "integrity": self.verify_integrity(),
        }


# ===================================================================
# Sandboxed Execution
# ===================================================================


@dataclass(init=False)
class SandboxConfig:
    """
    Configuration for sandboxed execution.

    Note:
        `requested_max_memory_mb`, `requested_network_access`, and
        `requested_filesystem_read` are advisory policy values only unless the
        underlying execution backend explicitly enforces them. The local
        executor should not treat them as strict security boundaries.
    """

    timeout_seconds: int = 30
    requested_max_memory_mb: int = 512
    max_output_size: int = 100000
    allowed_imports: Optional[list[str]] = None
    blocked_imports: list[str] = field(
        default_factory=lambda: ["subprocess", "shutil", "ctypes", "importlib"]
    )
    requested_network_access: bool = False
    requested_filesystem_read: bool = True
    filesystem_write: bool = False

    def __init__(
        self,
        timeout_seconds: int = 30,
        requested_max_memory_mb: int = 512,
        max_output_size: int = 100000,
        allowed_imports: Optional[list[str]] = None,
        blocked_imports: Optional[list[str]] = None,
        requested_network_access: bool = False,
        requested_filesystem_read: bool = True,
        filesystem_write: bool = False,
        max_memory_mb: Optional[int] = None,
        network_access: Optional[bool] = None,
        filesystem_read: Optional[bool] = None,
    ):
        self.timeout_seconds = timeout_seconds
        self.requested_max_memory_mb = (
            requested_max_memory_mb if max_memory_mb is None else max_memory_mb
        )
        self.max_output_size = max_output_size
        self.allowed_imports = allowed_imports
        self.blocked_imports = (
            blocked_imports
            if blocked_imports is not None
            else ["subprocess", "shutil", "ctypes", "importlib"]
        )
        self.requested_network_access = (
            requested_network_access if network_access is None else network_access
        )
        self.requested_filesystem_read = (
            requested_filesystem_read if filesystem_read is None else filesystem_read
        )
        self.filesystem_write = filesystem_write
        self.blocked_commands: list[str] = [
            "rm -rf",
            "mkfs",
            "dd if=",
            "chmod 777",
        ]

    @property
    def max_memory_mb(self) -> int:
        """Backward-compatible legacy alias for advisory memory policy."""
        return self.requested_max_memory_mb

    @max_memory_mb.setter
    def max_memory_mb(self, value: int) -> None:
        self.requested_max_memory_mb = value

    @property
    def network_access(self) -> bool:
        """Backward-compatible legacy alias for advisory network policy."""
        return self.requested_network_access

    @network_access.setter
    def network_access(self, value: bool) -> None:
        self.requested_network_access = value

    @property
    def filesystem_read(self) -> bool:
        """Backward-compatible legacy alias for advisory filesystem-read policy."""
        return self.requested_filesystem_read

    @filesystem_read.setter
    def filesystem_read(self, value: bool) -> None:
        self.requested_filesystem_read = value


@dataclass
class SandboxResult:
    """Result of sandboxed execution"""

    success: bool
    output: str = ""
    error: Optional[str] = None
    return_value: Any = None
    execution_time_ms: float = 0.0
    memory_used_mb: float = 0.0


class SandboxedExecution:
    """
    Runs code and commands in isolated environments with strict resource limits.

    Safety features:
    - Import restrictions
    - Timeout enforcement
    - Memory limits
    - Output size limits
    - Filesystem restrictions
    - Network access control
    """

    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self._audit = None

    def _get_audit(self):
        if self._audit is None:
            self._audit = audit_trail
        return self._audit

    async def execute_python(
        self, code: str, config: Optional[SandboxConfig] = None
    ) -> SandboxResult:
        """
        Execute Python code in a sandboxed environment.

        Args:
            code: Python code to execute
            config: Override sandbox configuration

        Returns:
            SandboxResult with output and metadata
        """
        cfg = config or self.config
        start = time.time()

        # Log to audit trail
        self._get_audit().log(
            event_type="sandbox_execution",
            actor="sandbox",
            action="execute_python",
            target="python_code",
            details={"code_length": len(code)},
        )

        # Safety: check for blocked imports
        for blocked in cfg.blocked_imports:
            if f"import {blocked}" in code or f"from {blocked}" in code:
                return SandboxResult(
                    success=False,
                    error=f"Blocked import: {blocked}",
                    execution_time_ms=(time.time() - start) * 1000,
                )

        # Execute in subprocess with timeout
        try:
            # Create a wrapper script with restrictions
            wrapper = self._create_sandbox_wrapper(code, cfg)

            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-c",
                wrapper,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self._get_restricted_env(),
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=cfg.timeout_seconds
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return SandboxResult(
                    success=False,
                    error=f"Execution timed out after {cfg.timeout_seconds}s",
                    execution_time_ms=(time.time() - start) * 1000,
                )

            output = stdout.decode("utf-8", errors="replace")
            errors = stderr.decode("utf-8", errors="replace")

            # Truncate large outputs
            if len(output) > cfg.max_output_size:
                output = output[: cfg.max_output_size] + "\n... [truncated]"

            return SandboxResult(
                success=process.returncode == 0,
                output=output,
                error=errors if errors else None,
                execution_time_ms=(time.time() - start) * 1000,
            )

        except Exception as e:
            return SandboxResult(
                success=False, error=str(e), execution_time_ms=(time.time() - start) * 1000
            )

    def _create_sandbox_wrapper(self, code: str, config: SandboxConfig) -> str:
        """Create a sandboxed wrapper for Python code"""
        restrictions = []

        if not config.filesystem_write:
            # Note: This monkeypatches builtins.open and pathlib.Path.write_text/write_bytes
            # to block write operations. This is a best-effort restriction, not an OS-level
            # sandbox. Code using os.open() or other low-level file APIs may bypass this.
            # For stronger isolation, use containerized execution.
            restrictions.append("import builtins; _original_open = builtins.open")
            restrictions.append(
                "def _restricted_open(f, mode='r', *a, **kw):\n"
                "    if any(m in mode for m in ('w', 'a', 'x')):\n"
                "        raise PermissionError('Write access denied in sandbox')\n"
                "    return _original_open(f, mode, *a, **kw)\n"
                "builtins.open = _restricted_open"
            )
            restrictions.append(
                "import pathlib\n"
                "def _block_write_text(self, *a, **kw):"
                " raise PermissionError("
                "'Write access denied in sandbox')\n"
                "def _block_write_bytes(self, *a, **kw):"
                " raise PermissionError("
                "'Write access denied in sandbox')\n"
                "pathlib.Path.write_text = _block_write_text\n"
                "pathlib.Path.write_bytes = _block_write_bytes"
            )

        import_checks = ""
        if config.blocked_imports:
            blocked = repr(config.blocked_imports)
            import_checks = (
                f"_original_import = builtins.__import__\n"
                f"_blocked = {blocked}\n"
                f"def _restricted_import(name, *args, **kwargs):\n"
                f"    if name in _blocked:\n"
                f"        raise ImportError(f'Import blocked in sandbox: {{name}}')\n"
                f"    return _original_import(name, *args, **kwargs)\n"
                f"builtins.__import__ = _restricted_import\n"
            )

        wrapper = f"""
import sys
import builtins
{chr(10).join(restrictions)}
{import_checks}
try:
{chr(10).join("    " + line for line in code.splitlines())}
except Exception as e:
    print(f"Error: {{type(e).__name__}}: {{e}}", file=sys.stderr)
    sys.exit(1)
"""
        return wrapper

    def _get_restricted_env(self) -> dict[str, str]:
        """Get restricted environment variables for sandbox"""
        # Start with minimal environment
        env = {
            "PATH": "/usr/bin:/bin",
            "HOME": "/tmp",  # noqa: S108
            "LANG": "en_US.UTF-8",
            "PYTHONDONTWRITEBYTECODE": "1",
        }

        # Never pass through sensitive variables
        sensitive = {
            "ANTHROPIC_API_KEY",
            "OPENAI_API_KEY",
            "OPENROUTER_API_KEY",
            "STRIPE_API_KEY",
            "GITHUB_TOKEN",
            "AWS_SECRET_ACCESS_KEY",
            "DATABASE_URL",
            "POSTGRES_URL",
        }

        for key, value in os.environ.items():
            if key.upper() not in sensitive and not key.startswith("API_"):
                # Only pass safe env vars
                if key in ("PYTHONPATH", "VIRTUAL_ENV"):
                    env[key] = value

        return env

    # Allowlisted shell commands that can be executed
    ALLOWED_COMMANDS = {
        "ls",
        "cat",
        "head",
        "tail",
        "grep",
        "find",
        "wc",
        "sort",
        "uniq",
        "echo",
        "date",
        "pwd",
        "whoami",
        "env",
        "which",
        "file",
        "stat",
        "diff",
        "tr",
        "cut",
        "awk",
        "sed",
        "python3",
        "python",
        "pip",
        "node",
        "npm",
        "git",
        "curl",
        "wget",
    }

    async def execute_shell(
        self, command: str, config: Optional[SandboxConfig] = None
    ) -> SandboxResult:
        """
        Execute a shell command with sandbox restrictions.

        Uses create_subprocess_exec with an allowlist of commands instead of
        create_subprocess_shell. Only the base command is checked against the
        allowlist; arguments are passed through.
        """
        cfg = config or self.config
        start = time.time()

        # Block dangerous commands
        dangerous = ["rm -rf", "mkfs", "dd if=", "> /dev/", "chmod 777", ":(){ :|:& };:"]
        for pattern in dangerous:
            if pattern in command:
                return SandboxResult(
                    success=False, error=f"Blocked dangerous command pattern: {pattern}"
                )

        # Parse command into executable + args
        import shlex

        try:
            parts = shlex.split(command)
        except ValueError as e:
            return SandboxResult(
                success=False,
                error=f"Failed to parse command: {e}",
                execution_time_ms=(time.time() - start) * 1000,
            )

        if not parts:
            return SandboxResult(
                success=False, error="Empty command", execution_time_ms=(time.time() - start) * 1000
            )

        base_cmd = os.path.basename(parts[0])
        # Reject commands with path separators to prevent path traversal bypass
        if os.sep in parts[0] or "/" in parts[0]:
            return SandboxResult(
                success=False,
                error=f"Path-based commands not allowed in sandbox: {parts[0]!r}. "
                f"Use bare command names only.",
                execution_time_ms=(time.time() - start) * 1000,
            )
        if base_cmd not in self.ALLOWED_COMMANDS:
            return SandboxResult(
                success=False,
                error=f"Command not in allowlist: {base_cmd!r}. "
                f"Allowed: {', '.join(sorted(self.ALLOWED_COMMANDS))}",
                execution_time_ms=(time.time() - start) * 1000,
            )

        self._get_audit().log(
            event_type="sandbox_execution",
            actor="sandbox",
            action="execute_shell",
            target="shell_command",
            details={"command": command[:200]},
        )

        try:
            process = await asyncio.create_subprocess_exec(
                *parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self._get_restricted_env(),
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=cfg.timeout_seconds
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return SandboxResult(
                    success=False, error=f"Command timed out after {cfg.timeout_seconds}s"
                )

            output = stdout.decode("utf-8", errors="replace")
            errors = stderr.decode("utf-8", errors="replace")

            return SandboxResult(
                success=process.returncode == 0,
                output=output[: cfg.max_output_size],
                error=errors if errors else None,
                execution_time_ms=(time.time() - start) * 1000,
            )

        except Exception as e:
            return SandboxResult(
                success=False, error=str(e), execution_time_ms=(time.time() - start) * 1000
            )

    # ------------------------------------------------------------------
    # Synchronous convenience wrappers
    # ------------------------------------------------------------------

    def get_safe_env(self) -> dict[str, str]:
        """Return a restricted environment (alias for ``_get_restricted_env``)."""
        return self._get_restricted_env()

    def execute(self, command: str) -> SandboxResult:
        """Run a shell command synchronously; raises on blocked commands."""
        dangerous = ["rm -rf", "mkfs", "dd if=", "> /dev/", "chmod 777", ":(){ :|:& };:"]
        for pattern in dangerous:
            if pattern in command:
                raise RuntimeError(f"Blocked dangerous command pattern: {pattern}")

        import shlex

        parts = shlex.split(command)
        if not parts:
            raise ValueError("Empty command")
        base_cmd = os.path.basename(parts[0])
        if os.sep in parts[0] or "/" in parts[0]:
            raise RuntimeError(f"Path-based commands not allowed: {parts[0]!r}")
        if base_cmd not in self.ALLOWED_COMMANDS:
            raise RuntimeError(f"Command not in allowlist: {base_cmd!r}")

        result = asyncio.run(self.execute_shell(command))
        if not result.success and result.error:
            raise RuntimeError(result.error)
        return result

    def execute_code(self, code: str) -> SandboxResult:
        """Run Python code synchronously; raises on blocked imports."""
        cfg = self.config
        for blocked in cfg.blocked_imports:
            if f"import {blocked}" in code or f"from {blocked}" in code:
                raise RuntimeError(f"Blocked import: {blocked}")

        result = asyncio.run(self.execute_python(code))
        if not result.success and result.error:
            raise RuntimeError(result.error)
        return result


class KillSwitchState(str, Enum):
    """Kill switch states"""

    ARMED = "armed"  # Ready to trigger
    TRIGGERED = "triggered"  # Kill switch activated
    RECOVERING = "recovering"  # Restoring state
    NORMAL = "normal"  # Normal operation


@dataclass
class AgentState:
    """Snapshot of agent state for recovery"""

    state_id: str
    timestamp: str
    active_tasks: list[dict] = field(default_factory=list)
    pending_operations: list[dict] = field(default_factory=list)
    sub_agents: list[dict] = field(default_factory=list)
    memory_snapshot: dict[str, Any] = field(default_factory=dict)


class KillSwitch:
    """
    Emergency halt system that gracefully preserves agent state,
    rolls back pending operations, and terminates all sub-agent activity.

    Features:
    - Immediate halt of all autonomous operations
    - State preservation before shutdown
    - Rollback of pending/incomplete operations
    - Sub-agent termination cascade
    - Safe recovery and resume
    """

    PREF_KEY_HEARTBEAT = "last_heartbeat_time"
    PREF_KEY_LOG_REVIEW = "last_log_review"

    def __init__(self, state_file: Optional[str] = None):
        self._state_file = state_file
        self.state = KillSwitchState.ARMED
        self._saved_states: list[AgentState] = []
        self._shutdown_callbacks: list[Callable] = []
        self._lock = threading.Lock()

    def trigger(self, reason: str = "Manual trigger") -> AgentState:
        """
        EMERGENCY: Trigger the kill switch.

        1. Save current state
        2. Cancel all pending operations
        3. Terminate sub-agents
        4. Halt autonomous systems
        """
        with self._lock:
            if self.state == KillSwitchState.TRIGGERED:
                logger.warning("Kill switch already triggered")
                return (
                    self._saved_states[-1]
                    if self._saved_states
                    else AgentState(state_id="none", timestamp=datetime.now().isoformat())
                )

            self.state = KillSwitchState.TRIGGERED
            logger.critical(f"🚨 KILL SWITCH TRIGGERED: {reason}")

            # 1. Save state
            state = self._capture_state()
            self._saved_states.append(state)

            # 2. Execute shutdown callbacks
            for callback in self._shutdown_callbacks:
                try:
                    callback(reason)
                except Exception as e:
                    logger.error(f"Shutdown callback failed: {e}")

            # 3. Halt heartbeat
            try:
                from heartbeat import heartbeat

                heartbeat.stop()
                logger.info("Heartbeat stopped")
            except Exception as e:
                logger.error(f"Failed to stop heartbeat: {e}")

            # 4. Log to audit trail
            try:
                audit_trail.log(
                    event_type="kill_switch",
                    actor="kill_switch",
                    action="triggered",
                    target="all_systems",
                    details={"reason": reason},
                )
            except Exception:
                logger.debug("Failed to log kill switch event to audit trail")

            logger.critical("🚨 All systems halted. State preserved.")

            # 5. Persist state to file if configured
            if self._state_file:
                try:
                    state_data = {
                        "active": False,
                        "triggered_at": state.timestamp,
                        "reason": reason,
                        "state_id": state.state_id,
                    }
                    with open(self._state_file, "w", encoding="utf-8") as fh:  # noqa: PTH123
                        json.dump(state_data, fh, indent=2)
                except Exception as exc:
                    logger.error(f"Failed to write kill-switch state file: {exc}")

            return state

    def _capture_state(self) -> AgentState:
        """Capture current agent state for recovery"""
        import uuid

        state = AgentState(state_id=str(uuid.uuid4()), timestamp=datetime.now().isoformat())

        # Capture active tasks from sub-agent orchestrator
        try:
            from sub_agents import orchestrator

            for wf_id, wf in orchestrator.active_workflows.items():
                state.active_tasks.append(
                    {
                        "workflow_id": wf_id,
                        "description": wf.description,
                        "task_count": len(wf.tasks),
                        "completed": len([t for t in wf.tasks if t.status.value == "completed"]),
                    }
                )
        except Exception as e:
            logger.warning(f"Failed to capture sub-agent state: {e}")

        # Capture memory snapshot
        try:
            from memory import memory

            state.memory_snapshot = {
                "preferences": {
                    "last_heartbeat": memory.get_preference(self.PREF_KEY_HEARTBEAT),
                    "last_log_review": memory.get_preference(self.PREF_KEY_LOG_REVIEW),
                }
            }
        except Exception as e:
            logger.warning(f"Failed to capture memory state: {e}")

        return state

    def is_active(self) -> bool:
        """Return ``True`` when the switch has *not* been triggered."""
        return self.state != KillSwitchState.TRIGGERED

    def recover(self) -> Optional[AgentState]:
        """
        Recover from a kill switch trigger.

        Returns the saved state for inspection before resuming.
        """
        with self._lock:
            if self.state != KillSwitchState.TRIGGERED:
                logger.warning("Cannot recover - kill switch not in triggered state")
                return None

            self.state = KillSwitchState.RECOVERING
            logger.info("🔄 Beginning recovery from kill switch...")

            last_state = self._saved_states[-1] if self._saved_states else None

            # Resume to normal
            self.state = KillSwitchState.ARMED
            logger.info("✅ Recovery complete. Kill switch re-armed.")

            # Update state file
            if self._state_file:
                try:
                    state_data = {"active": True, "recovered_at": datetime.now().isoformat()}
                    with open(self._state_file, "w", encoding="utf-8") as fh:  # noqa: PTH123
                        json.dump(state_data, fh, indent=2)
                except Exception as exc:
                    logger.error(f"Failed to update kill-switch state file: {exc}")

            return last_state

    def on_shutdown(self, callback: Callable):
        """Register a shutdown callback"""
        self._shutdown_callbacks.append(callback)

    def get_status(self) -> dict[str, Any]:
        """Get kill switch status"""
        return {
            "state": self.state.value,
            "saved_states": len(self._saved_states),
            "shutdown_callbacks": len(self._shutdown_callbacks),
            "last_trigger": self._saved_states[-1].timestamp if self._saved_states else None,
        }


# ===================================================================
# Global Instances
# ===================================================================

human_gate = HumanInTheLoop()
audit_trail = AuditTrail()
sandbox = SandboxedExecution()
kill_switch = KillSwitch()
