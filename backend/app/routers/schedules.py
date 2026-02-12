import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..deps import get_current_user
from ..services.scheduler import (
    load_user_schedules,
    save_user_schedules,
    reload_user_schedules,
)

router = APIRouter()


class ScheduleCreate(BaseModel):
    description: str
    cron: str
    enabled: bool = True


class ScheduleUpdate(BaseModel):
    description: Optional[str] = None
    cron: Optional[str] = None
    enabled: Optional[bool] = None


@router.get("/api/schedules")
async def list_schedules(username: str = Depends(get_current_user)):
    return load_user_schedules(username)


@router.post("/api/schedules")
async def create_schedule(
    req: ScheduleCreate, username: str = Depends(get_current_user)
):
    schedules = load_user_schedules(username)
    new_schedule = {
        "id": str(uuid.uuid4())[:8],
        "description": req.description,
        "cron": req.cron,
        "enabled": req.enabled,
    }
    schedules.append(new_schedule)
    save_user_schedules(username, schedules)
    reload_user_schedules(username)
    return new_schedule


@router.put("/api/schedules/{schedule_id}")
async def update_schedule(
    schedule_id: str,
    req: ScheduleUpdate,
    username: str = Depends(get_current_user),
):
    schedules = load_user_schedules(username)
    target = next((s for s in schedules if s["id"] == schedule_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Schedule not found")

    if req.description is not None:
        target["description"] = req.description
    if req.cron is not None:
        target["cron"] = req.cron
    if req.enabled is not None:
        target["enabled"] = req.enabled

    save_user_schedules(username, schedules)
    reload_user_schedules(username)
    return target


@router.delete("/api/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: str, username: str = Depends(get_current_user)
):
    schedules = load_user_schedules(username)
    schedules = [s for s in schedules if s["id"] != schedule_id]
    save_user_schedules(username, schedules)
    reload_user_schedules(username)
    return {"ok": True}
