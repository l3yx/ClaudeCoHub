import re
from pathlib import Path
from datetime import datetime

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


def discover_sessions(username: str) -> list[dict]:
    """Scan Claude project dir for UUID-named .jsonl files that are real sessions."""
    project_dir = get_claude_project_dir(username)
    if not project_dir.exists():
        return []

    sessions = []
    for f in project_dir.iterdir():
        if f.suffix == ".jsonl" and UUID_RE.match(f.stem) and _is_real_session(f):
            stat = f.stat()
            sessions.append(
                {
                    "session_id": f.stem,
                    "updated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "size_bytes": stat.st_size,
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
