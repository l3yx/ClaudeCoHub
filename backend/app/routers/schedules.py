from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..deps import get_current_user
from ..config import get_user_workdir
from ..services.scheduler import (
    load_schedules,
    save_schedules,
    reload_schedules,
)

router = APIRouter()


class ScheduleCreate(BaseModel):
    name: str
    content: str
    cron: str
    enabled: bool = True


class ScheduleUpdate(BaseModel):
    content: Optional[str] = None
    cron: Optional[str] = None
    enabled: Optional[bool] = None


@router.get("/api/schedules")
async def list_schedules(username: str = Depends(get_current_user)):
    workdir = str(get_user_workdir(username))
    return load_schedules(workdir)


@router.post("/api/schedules")
async def create_schedule(
    req: ScheduleCreate, username: str = Depends(get_current_user)
):
    workdir = str(get_user_workdir(username))
    schedules = load_schedules(workdir)
    if any(s["name"] == req.name for s in schedules):
        raise HTTPException(status_code=400, detail="Schedule name already exists")
    new_schedule = {
        "name": req.name,
        "content": req.content,
        "cron": req.cron,
        "workdir": workdir,
        "enabled": req.enabled,
    }
    schedules.append(new_schedule)
    save_schedules(schedules, workdir)
    reload_schedules()
    return new_schedule


@router.put("/api/schedules/{name}")
async def update_schedule(
    name: str,
    req: ScheduleUpdate,
    username: str = Depends(get_current_user),
):
    workdir = str(get_user_workdir(username))
    schedules = load_schedules(workdir)
    target = next((s for s in schedules if s["name"] == name), None)
    if not target:
        raise HTTPException(status_code=404, detail="Schedule not found")

    if req.content is not None:
        target["content"] = req.content
    if req.cron is not None:
        target["cron"] = req.cron
    if req.enabled is not None:
        target["enabled"] = req.enabled

    save_schedules(schedules, workdir)
    reload_schedules()
    return target


@router.delete("/api/schedules/{name}")
async def delete_schedule(
    name: str, username: str = Depends(get_current_user)
):
    workdir = str(get_user_workdir(username))
    schedules = load_schedules(workdir)
    schedules = [s for s in schedules if s["name"] != name]
    save_schedules(schedules, workdir)
    reload_schedules()
    return {"ok": True}
