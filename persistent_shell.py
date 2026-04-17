"""
Persistent Shell Environments for Big Homie
Maintains shell sessions that don't reset between commands
"""

import asyncio
import os
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger


@dataclass
class ShellSession:
    """Represents a persistent shell session"""

    session_id: str
    process: asyncio.subprocess.Process
    created_at: datetime
    last_used: datetime
    cwd: str
    env: dict[str, str]
    history: list[str]

    def __post_init__(self):
        if not self.history:
            self.history = []


class PersistentShellManager:
    """
    Manages persistent shell sessions that survive across multiple commands

    Features:
    - Sessions persist across commands
    - Environment variables are maintained
    - Working directory is preserved
    - Command history tracking
    - Session timeout and cleanup
    """

    def __init__(self, session_timeout: int = 3600):
        """
        Initialize the persistent shell manager

        Args:
            session_timeout: Seconds before idle sessions are cleaned up (default: 1 hour)
        """
        self.sessions: dict[str, ShellSession] = {}
        self.session_timeout = session_timeout
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the shell manager and cleanup task"""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Persistent shell manager started")

    async def stop(self):
        """Stop all sessions and cleanup"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Terminate all sessions
        for session_id in list(self.sessions.keys()):
            await self.terminate_session(session_id)

        logger.info("Persistent shell manager stopped")

    async def create_session(
        self, cwd: Optional[str] = None, env: Optional[dict[str, str]] = None
    ) -> str:
        """
        Create a new persistent shell session

        Args:
            cwd: Working directory for the session
            env: Environment variables

        Returns:
            Session ID
        """
        # Lazily start the cleanup task on first use so callers don't need
        # to explicitly call start() before creating sessions.
        if self._cleanup_task is None or self._cleanup_task.done():
            await self.start()
        session_id = str(uuid.uuid4())

        # Choose a platform-appropriate interactive shell
        if sys.platform == "win32":
            shell_cmd = os.environ.get("COMSPEC", "cmd.exe")
        else:
            shell_cmd = os.environ.get("SHELL", "/bin/sh")

        # Start the shell process
        # Pass --norc/--noprofile only to bash to avoid a fast, clean start
        shell_name = Path(shell_cmd).name
        bash_flags = ["--norc", "--noprofile"] if shell_name == "bash" else []

        process = None
        try:
            process = await asyncio.create_subprocess_exec(
                shell_cmd,
                *bash_flags,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=cwd,
                env=env,
            )

            session = ShellSession(
                session_id=session_id,
                process=process,
                created_at=datetime.now(),
                last_used=datetime.now(),
                cwd=cwd or ".",
                env=env or {},
                history=[],
            )

            self.sessions[session_id] = session
            logger.info(f"Created persistent shell session: {session_id}")

            return session_id
        except Exception:
            # Clean up the process if session creation fails
            if process is not None:
                try:
                    process.kill()
                    await process.wait()
                except Exception:
                    pass
            raise

    async def execute_command(
        self, session_id: str, command: str, timeout: float = 30.0
    ) -> dict[str, str]:
        """
        Execute a command in a persistent session

        Args:
            session_id: Session ID
            command: Command to execute
            timeout: Command timeout in seconds

        Returns:
            Dict with stdout, stderr, and exit_code
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.sessions[session_id]
        session.last_used = datetime.now()
        session.history.append(command)

        # Write command to stdin with a unique marker for output parsing
        marker = f"__CMD_DONE_{uuid.uuid4().hex}__"
        full_command = f"{command}\necho {marker} $?\n"

        if session.process.stdin:
            session.process.stdin.write(full_command.encode())
            await session.process.stdin.drain()

        # Read output until we see the marker
        output_lines = []
        exit_code = None

        try:
            async with asyncio.timeout(timeout):
                while True:
                    if session.process.stdout:
                        line = await session.process.stdout.readline()
                        if not line:
                            break

                        line_str = line.decode("utf-8", errors="replace").rstrip()

                        # Check for completion marker
                        if marker in line_str:
                            # Extract exit code
                            parts = line_str.split()
                            if len(parts) >= 2:
                                try:
                                    exit_code = int(parts[-1])
                                except ValueError:
                                    exit_code = 0
                            break
                        else:
                            output_lines.append(line_str)
        except asyncio.TimeoutError:
            logger.warning(f"Command timed out in session {session_id}: {command}")
            return {
                "stdout": "\n".join(output_lines),
                "stderr": "Command timed out",
                "exit_code": "timeout",
            }

        output = "\n".join(output_lines)

        logger.debug(f"Executed in session {session_id}: {command} (exit: {exit_code})")

        return {
            "stdout": output,
            "stderr": "",
            "exit_code": str(exit_code) if exit_code is not None else "0",
        }

    async def get_session_info(self, session_id: str) -> dict:
        """Get information about a session"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.sessions[session_id]

        return {
            "session_id": session_id,
            "created_at": session.created_at.isoformat(),
            "last_used": session.last_used.isoformat(),
            "cwd": session.cwd,
            "command_count": len(session.history),
            "recent_commands": session.history[-5:] if session.history else [],
        }

    async def list_sessions(self) -> list[dict]:
        """List all active sessions"""
        return [await self.get_session_info(session_id) for session_id in self.sessions.keys()]

    async def terminate_session(self, session_id: str):
        """Terminate a session"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.sessions[session_id]

        # Try graceful shutdown
        if session.process.stdin:
            try:
                session.process.stdin.write(b"exit\n")
                await session.process.stdin.drain()
                await asyncio.wait_for(session.process.wait(), timeout=2.0)
            except (asyncio.TimeoutError, BrokenPipeError):
                # Force kill if graceful exit fails
                session.process.kill()
                await session.process.wait()

        del self.sessions[session_id]
        logger.info(f"Terminated shell session: {session_id}")

    async def _cleanup_loop(self):
        """Background task to cleanup idle sessions"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes

                now = datetime.now()
                to_remove = []

                for session_id, session in self.sessions.items():
                    idle_time = (now - session.last_used).total_seconds()
                    if idle_time > self.session_timeout:
                        to_remove.append(session_id)
                        logger.info(f"Session {session_id} idle for {idle_time:.0f}s, cleaning up")

                for session_id in to_remove:
                    try:
                        await self.terminate_session(session_id)
                    except Exception as e:
                        logger.error(f"Error terminating session {session_id}: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")


# Global shell manager instance
shell_manager = PersistentShellManager()
