import asyncio
import logging
from datetime import datetime
from pathlib import Path

import yaml
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ..config import WORKDIR_BASE, get_user_workdir

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def run_claude_task(username: str, task_id: str, description: str):
    workdir = get_user_workdir(username)
    log_file = workdir / ".claudecohub" / "task_output.log"

    timestamp = datetime.now().isoformat()
    header = f"\n{'='*60}\n[{timestamp}] Task: {task_id}\nPrompt: {description}\n{'='*60}\n"

    proc = await asyncio.create_subprocess_shell(
        f'claude -p "{description}"',
        cwd=str(workdir),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    output = stdout.decode(errors="replace")

    with open(log_file, "a") as f:
        f.write(header + output + "\n")

    logger.info(f"Task {task_id} for {username} completed (rc={proc.returncode})")


def load_user_schedules(username: str) -> list[dict]:
    schedule_file = get_user_workdir(username) / ".claudecohub" / "schedules.yaml"
    if not schedule_file.exists():
        return []
    with open(schedule_file) as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, list) else []


def save_user_schedules(username: str, schedules: list[dict]):
    schedule_file = get_user_workdir(username) / ".claudecohub" / "schedules.yaml"
    schedule_file.parent.mkdir(parents=True, exist_ok=True)
    with open(schedule_file, "w") as f:
        yaml.dump(schedules, f, default_flow_style=False, allow_unicode=True)


def _job_id(username: str, task_id: str) -> str:
    return f"schedule_{username}_{task_id}"


def reload_user_schedules(username: str):
    # Remove existing jobs for this user
    for job in scheduler.get_jobs():
        if job.id.startswith(f"schedule_{username}_"):
            scheduler.remove_job(job.id)

    # Re-add from file
    schedules = load_user_schedules(username)
    for s in schedules:
        if not s.get("enabled", True):
            continue
        job_id = _job_id(username, s["id"])
        cron = s.get("cron", "")
        parts = cron.split()
        if len(parts) != 5:
            logger.warning(f"Invalid cron '{cron}' for job {job_id}")
            continue
        scheduler.add_job(
            run_claude_task,
            "cron",
            id=job_id,
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            day_of_week=parts[4],
            args=[username, s["id"], s["description"]],
            replace_existing=True,
        )


def load_all_schedules():
    if not WORKDIR_BASE.exists():
        return
    for user_dir in WORKDIR_BASE.iterdir():
        if user_dir.is_dir():
            reload_user_schedules(user_dir.name)
