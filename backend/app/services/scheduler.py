import asyncio
import logging
from datetime import datetime
from pathlib import Path

import yaml
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ..config import SCHEDULES_DIR, get_user_workdir

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

SCHEDULE_FILE = SCHEDULES_DIR / "schedules.yaml"


async def run_claude_task(username: str, task_id: str, content: str, workdir: str):
    log_file = SCHEDULES_DIR / "task_output.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().isoformat()
    header = f"\n{'='*60}\n[{timestamp}] Task: {task_id}\nPrompt: {content}\n{'='*60}\n"

    cwd = workdir or str(get_user_workdir(username))
    proc = await asyncio.create_subprocess_shell(
        f'claude -p "{content}"',
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    output = stdout.decode(errors="replace")

    with open(log_file, "a") as f:
        f.write(header + output + "\n")

    logger.info(f"Task {task_id} for {username} completed (rc={proc.returncode})")


def load_schedules(workdir: str = "") -> list[dict]:
    if not SCHEDULE_FILE.exists():
        return []
    with open(SCHEDULE_FILE) as f:
        data = yaml.safe_load(f)
    if not isinstance(data, list):
        return []
    if workdir:
        return [s for s in data if s.get("workdir") == workdir]
    return data


def _load_all_schedules() -> list[dict]:
    if not SCHEDULE_FILE.exists():
        return []
    with open(SCHEDULE_FILE) as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, list) else []


def save_schedules(schedules: list[dict], workdir: str = ""):
    SCHEDULE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if workdir:
        # 只替换该workdir的任务，保留其他用户的
        all_schedules = _load_all_schedules()
        all_schedules = [s for s in all_schedules if s.get("workdir") != workdir]
        all_schedules.extend(schedules)
    else:
        all_schedules = schedules
    with open(SCHEDULE_FILE, "w") as f:
        yaml.dump(all_schedules, f, default_flow_style=False, allow_unicode=True)


def _job_id(name: str, workdir: str) -> str:
    return f"schedule_{workdir}_{name}"


def reload_schedules():
    # Remove all schedule jobs
    for job in scheduler.get_jobs():
        if job.id.startswith("schedule_"):
            scheduler.remove_job(job.id)

    # Re-add from file
    schedules = _load_all_schedules()
    for s in schedules:
        if not s.get("enabled", True):
            continue
        job_id = _job_id(s["name"], s.get("workdir", ""))
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
            args=["", s["name"], s["content"], s.get("workdir", "")],
            replace_existing=True,
        )
