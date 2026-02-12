import re
from pathlib import Path
from datetime import datetime

from ..config import get_claude_project_dir

UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)


def discover_sessions(username: str) -> list[dict]:
    """Scan Claude project dir for UUID-named .jsonl files."""
    project_dir = get_claude_project_dir(username)
    if not project_dir.exists():
        return []

    sessions = []
    for f in project_dir.iterdir():
        if f.suffix == ".jsonl" and UUID_RE.match(f.stem):
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
