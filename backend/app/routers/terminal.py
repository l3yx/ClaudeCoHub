import asyncio
import json
import logging
import os

import ptyprocess
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
        pty = ptyprocess.PtyProcess.spawn(
            ["tmux", "attach-session", "-t", session_id],
            env=env,
            dimensions=(24, 80),
        )
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
                    # ptyprocess.read() returns str
                    data = await loop.run_in_executor(None, lambda: pty.read(4096))
                except EOFError:
                    break
                if not data:
                    break
                try:
                    await websocket.send_text(data)
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
                pty.write(msg["bytes"])
            elif "text" in msg:
                text = msg["text"]
                try:
                    cmd = json.loads(text)
                    if cmd.get("type") == "resize":
                        pty.setwinsize(cmd["rows"], cmd["cols"])
                        continue
                except (json.JSONDecodeError, KeyError):
                    pass
                pty.write(text.encode())
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.debug(f"ws loop ended: {e}")
    finally:
        closed.set()
        reader_task.cancel()
        # Detach from tmux instead of killing
        try:
            if pty.isalive():
                pty.write(b"\x02d")
                await asyncio.sleep(0.3)
        except (OSError, EOFError):
            pass
        try:
            if pty.isalive():
                pty.terminate(force=True)
        except Exception:
            pass
