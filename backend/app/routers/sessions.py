import uuid

from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_current_user
from ..config import get_user_workdir
from ..services import tmux, claude_session

router = APIRouter()


@router.get("/api/sessions")
async def list_sessions(uid: str = Depends(get_current_user)):
    discovered = claude_session.discover_sessions(uid)
    alive_sessions = await tmux.list_tmux_sessions()

    results = []
    for s in discovered:
        sid = s["session_id"]
        alive = sid in alive_sessions
        status = None
        if alive:
            status = await tmux.detect_status(sid)
        results.append(
            {
                "session_id": sid,
                "updated_at": s["updated_at"],
                "alive": alive,
                "status": status or ("idle" if alive else "dead"),
                "first_message": s.get("first_message", ""),
            }
        )

    return results


@router.post("/api/sessions")
async def create_session(uid: str = Depends(get_current_user)):
    session_id = str(uuid.uuid4())
    workdir = str(get_user_workdir(uid))
    ok = await tmux.create_session(session_id, workdir)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to create tmux session")
    return {"session_id": session_id}


@router.post("/api/sessions/{session_id}/resume")
async def resume_session(session_id: str, uid: str = Depends(get_current_user)):
    if await tmux.session_exists(session_id):
        raise HTTPException(status_code=400, detail="Session already alive")
    workdir = str(get_user_workdir(uid))
    ok = await tmux.resume_session(session_id, workdir)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to resume session")
    return {"session_id": session_id}


@router.delete("/api/sessions/{session_id}")
async def close_session(session_id: str, uid: str = Depends(get_current_user)):
    if not await tmux.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found or already dead")
    await tmux.kill_session(session_id)
    return {"ok": True}


@router.delete("/api/sessions/{session_id}/delete")
async def delete_session(session_id: str, uid: str = Depends(get_current_user)):
    if await tmux.session_exists(session_id):
        await tmux.kill_session(session_id)
    claude_session.delete_session(uid, session_id)
    return {"ok": True}
