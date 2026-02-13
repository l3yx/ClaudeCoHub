from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from jose import jwt
from pydantic import BaseModel

from .config import (
    SECRET_KEY,
    JWT_ALGORITHM,
    JWT_EXPIRE_HOURS,
    get_user_workdir,
    find_user,
)

router = APIRouter()


class LoginRequest(BaseModel):
    uid: str
    password: str


class LoginResponse(BaseModel):
    token: str
    uid: str
    username: str


@router.post("/api/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    user = find_user(req.uid)
    if not user or user.get("password") != req.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Ensure user workdir exists
    workdir = get_user_workdir(req.uid)
    workdir.mkdir(parents=True, exist_ok=True)

    exp = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    token = jwt.encode(
        {"sub": req.uid, "exp": exp}, SECRET_KEY, algorithm=JWT_ALGORITHM
    )
    return LoginResponse(token=token, uid=req.uid, username=user.get("username", req.uid))
