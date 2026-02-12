import json
import re
from pathlib import Path

from ..config import get_claude_project_dir

UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)


def _is_real_session(filepath: Path) -> bool:
    """Check if a .jsonl file is a real session by looking for 'sessionId' keyword."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if '"sessionId"' in line:
                    return True
        return False
    except OSError:
        return False


def _get_first_message(filepath: Path) -> str:
    """Extract the content of the first user message from a .jsonl file."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    msg = obj.get("message")
                    if isinstance(msg, dict) and msg.get("content"):
                        return msg["content"][:100]
                except (json.JSONDecodeError, KeyError):
                    continue
    except OSError:
        pass
    return ""


def _get_last_timestamp(filepath: Path) -> str:
    """Get the timestamp from the last line of a .jsonl file."""
    try:
        with open(filepath, "rb") as f:
            # 从文件末尾往前读取最后一行
            f.seek(0, 2)
            size = f.tell()
            if size == 0:
                return ""
            pos = size - 1
            while pos > 0:
                f.seek(pos)
                if f.read(1) == b"\n" and pos < size - 1:
                    break
                pos -= 1
            last_line = f.read().decode("utf-8", errors="replace").strip()
            if last_line:
                obj = json.loads(last_line)
                return obj.get("timestamp", "")
    except (OSError, json.JSONDecodeError):
        pass
    return ""


def discover_sessions(username: str) -> list[dict]:
    """Scan Claude project dir for UUID-named .jsonl files that are real sessions."""
    project_dir = get_claude_project_dir(username)
    if not project_dir.exists():
        return []

    sessions = []
    for f in project_dir.iterdir():
        if f.suffix == ".jsonl" and UUID_RE.match(f.stem) and _is_real_session(f):
            sessions.append(
                {
                    "session_id": f.stem,
                    "updated_at": _get_last_timestamp(f),
                    "first_message": _get_first_message(f),
                }
            )

    sessions.sort(key=lambda s: s["updated_at"], reverse=True)
    return sessions


def delete_session(username: str, session_id: str) -> bool:
    """Delete the .jsonl file for a session."""
    project_dir = get_claude_project_dir(username)
    filepath = project_dir / f"{session_id}.jsonl"
    if filepath.exists():
        filepath.unlink()
        return True
    return False
