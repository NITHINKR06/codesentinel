from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import redis.asyncio as aioredis
import json
import asyncio
from config import settings

router = APIRouter()


@router.websocket("/ws/scan/{scan_id}")
async def websocket_scan(websocket: WebSocket, scan_id: str):
    await websocket.accept()
    r = aioredis.from_url(settings.REDIS_URL)
    pubsub = r.pubsub()
    channel = f"scan:{scan_id}:events"

    await pubsub.subscribe(channel)

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode()
                try:
                    await websocket.send_text(data)
                except (WebSocketDisconnect, ConnectionResetError, RuntimeError):
                    break

                # Stop when scan completes or fails
                try:
                    parsed = json.loads(data)
                    if parsed.get("stage") in ("complete", "failed"):
                        break
                except Exception:
                    pass
    except (WebSocketDisconnect, ConnectionResetError, asyncio.CancelledError):
        pass
    finally:
        try:
            await pubsub.unsubscribe(channel)
        except Exception:
            pass
        await r.aclose()


async def emit_event(scan_id: str, stage: str, message: str, data: dict = None, progress: int = 0):
    """Helper for workers to push events to the WebSocket channel."""
    import redis as sync_redis
    r = sync_redis.from_url(settings.REDIS_URL)
    event = {
        "scan_id": scan_id,
        "stage": stage,
        "message": message,
        "progress": progress,
        "data": data or {},
    }
    r.publish(f"scan:{scan_id}:events", json.dumps(event))
    r.close()
