import asyncio
import re
from typing import Optional


async def _run(cmd: str) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    stdout, _ = await proc.communicate()
    return proc.returncode, stdout.decode(errors="replace").strip()


async def list_tmux_sessions() -> list[str]:
    rc, out = await _run('tmux list-sessions -F "#{session_name}" 2>/dev/null')
    if rc != 0 or not out:
        return []
    return [line.strip().strip('"') for line in out.splitlines() if line.strip()]


async def session_exists(session_id: str) -> bool:
    sessions = await list_tmux_sessions()
    return session_id in sessions


async def create_session(session_id: str, workdir: str) -> bool:
    rc, _ = await _run(
        f"tmux new-session -d -s {session_id} -c {workdir} "
        f"'claude --session-id {session_id}'"
    )
    return rc == 0


async def resume_session(session_id: str, workdir: str) -> bool:
    rc, _ = await _run(
        f"tmux new-session -d -s {session_id} -c {workdir} "
        f"'claude --resume {session_id}'"
    )
    return rc == 0


async def kill_session(session_id: str) -> bool:
    rc, _ = await _run(f"tmux kill-session -t {session_id}")
    return rc == 0


async def capture_last_lines(session_id: str, n: int = 5) -> str:
    rc, out = await _run(f"tmux capture-pane -t {session_id} -p -S -{n}")
    if rc != 0:
        return ""
    return out


async def detect_status(session_id: str) -> Optional[str]:
    """Return 'working', 'idle', or None if session doesn't exist."""
    if not await session_exists(session_id):
        return None
    lines = await capture_last_lines(session_id, 5)
    lower = lines.lower()
    if "esc to interrupt" in lower or "running" in lower:
        return "working"
    return "idle"
