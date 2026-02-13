from contextlib import asynccontextmanager
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .auth import router as auth_router
from .routers.sessions import router as sessions_router
from .routers.terminal import router as terminal_router
from .routers.schedules import router as schedules_router
from .routers.admin import router as admin_router
from .services.scheduler import scheduler, reload_schedules


logging.basicConfig(level=logging.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    reload_schedules()
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="ClaudeCoHub", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(sessions_router)
app.include_router(terminal_router)
app.include_router(schedules_router)
app.include_router(admin_router)

# Mount frontend static files last (catch-all)
frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
