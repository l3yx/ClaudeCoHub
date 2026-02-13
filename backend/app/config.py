import os
from pathlib import Path

import yaml

SECRET_KEY = os.getenv("JWT_SECRET", "claudecohub-dev-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

WORKDIR_BASE = Path.home() / "workdir"

CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"

SCHEDULES_DIR = Path.home() / ".claude" / "claudecohub"

USERS_FILE = SCHEDULES_DIR / "users.yaml"


def load_users() -> list[dict]:
    if not USERS_FILE.exists():
        return []
    with open(USERS_FILE) as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, list) else []


def find_user(uid: str) -> dict | None:
    for u in load_users():
        if u.get("uid") == uid:
            return u
    return None


def get_user_workdir(uid: str) -> Path:
    return WORKDIR_BASE / uid


def encode_path_for_claude(path: Path) -> str:
    """Encode a path to Claude Code's project directory name: /a/b/c -> -a-b-c"""
    return str(path).replace("/", "-")


def get_claude_project_dir(username: str) -> Path:
    workdir = get_user_workdir(username)
    encoded = encode_path_for_claude(workdir)
    return CLAUDE_PROJECTS_DIR / encoded
