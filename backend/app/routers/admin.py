from fastapi import APIRouter, Depends

from ..deps import get_current_user
from ..config import WORKDIR_BASE
from ..services import tmux, claude_session
from ..services.scheduler import load_schedules

router = APIRouter()


@router.get("/api/admin/overview")
async def admin_overview(uid: str = Depends(get_current_user)):
    alive_sessions = await tmux.list_tmux_sessions()

    users = []
    if WORKDIR_BASE.exists():
        for user_dir in sorted(WORKDIR_BASE.iterdir()):
            if not user_dir.is_dir():
                continue
            uname = user_dir.name
            discovered = claude_session.discover_sessions(uname)
            sessions = []
            for s in discovered:
                sid = s["session_id"]
                alive = sid in alive_sessions
                status = None
                if alive:
                    status = await tmux.detect_status(sid)
                sessions.append({
                    "session_id": sid,
                    "first_message": s.get("first_message", ""),
                    "updated_at": s["updated_at"],
                    "status": status or ("idle" if alive else "dead"),
                })
            users.append({
                "username": uname,
                "sessions": sessions,
            })

    schedules = load_schedules()
    return {"users": users, "schedules": schedules}
