import asyncio
import fcntl
import json
import logging
import os
import pty
import signal
import struct
import subprocess
import termios

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from ..deps import get_current_user_ws
from ..services import tmux

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/api/ws/terminal/{session_id}")
async def terminal_ws(
    websocket: WebSocket,
    session_id: str,
    username: str = Depends(get_current_user_ws),
):
    await websocket.accept()

    if not await tmux.session_exists(session_id):
        await websocket.send_text(
            json.dumps({"error": "Session not found or not alive"})
        )
        await websocket.close()
        return

    # Spawn pty attached to tmux session
    env = os.environ.copy()
    env["TERM"] = "xterm-256color"
    try:
        master_fd, slave_fd = pty.openpty()
        # 设置初始窗口大小
        fcntl.ioctl(slave_fd, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
        proc = subprocess.Popen(
            ["tmux", "attach-session", "-t", session_id],
            stdin=slave_fd, stdout=slave_fd, stderr=slave_fd,
            env=env, preexec_fn=os.setsid,
        )
        os.close(slave_fd)
    except Exception as e:
        logger.error(f"Failed to spawn pty: {e}")
        await websocket.send_text(json.dumps({"error": str(e)}))
        await websocket.close()
        return

    closed = asyncio.Event()

    async def pty_reader():
        loop = asyncio.get_event_loop()
        try:
            while not closed.is_set():
                try:
                    data = await loop.run_in_executor(
                        None, lambda: os.read(master_fd, 4096)
                    )
                except OSError:
                    break
                if not data:
                    break
                try:
                    await websocket.send_bytes(data)
                except Exception:
                    break
        except Exception as e:
            logger.debug(f"pty_reader ended: {e}")
        finally:
            closed.set()

    reader_task = asyncio.create_task(pty_reader())

    try:
        while not closed.is_set():
            msg = await websocket.receive()
            if msg.get("type") == "websocket.disconnect":
                break
            if "bytes" in msg:
                os.write(master_fd, msg["bytes"])
            elif "text" in msg:
                text = msg["text"]
                try:
                    cmd = json.loads(text)
                    if isinstance(cmd, dict) and cmd.get("type") == "resize":
                        rows, cols = cmd["rows"], cmd["cols"]
                        fcntl.ioctl(master_fd, termios.TIOCSWINSZ,
                                    struct.pack("HHHH", rows, cols, 0, 0))
                        os.kill(proc.pid, signal.SIGWINCH)
                        continue
                except (json.JSONDecodeError, KeyError):
                    pass
                os.write(master_fd, text.encode())
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.debug(f"ws loop ended: {e}")
    finally:
        closed.set()
        reader_task.cancel()
        # Detach from tmux instead of killing
        try:
            os.write(master_fd, b"\x02d")
            await asyncio.sleep(0.3)
        except OSError:
            pass
        try:
            os.close(master_fd)
        except OSError:
            pass
        try:
            proc.send_signal(signal.SIGHUP)
            proc.wait(timeout=2)
        except Exception:
            proc.kill()
