from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from jose import jwt
from pydantic import BaseModel

from .config import (
    SECRET_KEY,
    JWT_ALGORITHM,
    JWT_EXPIRE_HOURS,
    get_user_workdir,
    get_claude_project_dir,
)

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str


@router.post("/api/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    # Simple auth: username == password
    if req.username != req.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Ensure user directories exist
    workdir = get_user_workdir(req.username)
    workdir.mkdir(parents=True, exist_ok=True)
    (workdir / ".claude").mkdir(exist_ok=True)
    (workdir / ".claudecohub").mkdir(exist_ok=True)

    # Also ensure the claude project dir exists
    project_dir = get_claude_project_dir(req.username)
    project_dir.mkdir(parents=True, exist_ok=True)

    exp = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    token = jwt.encode(
        {"sub": req.username, "exp": exp}, SECRET_KEY, algorithm=JWT_ALGORITHM
    )
    return LoginResponse(token=token, username=req.username)
