from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import redis.asyncio as aioredis
import json
import asyncio

router = APIRouter()

REDIS_URL = "redis://localhost:6379/0"


@router.websocket("/ws/scan/{scan_id}")
async def websocket_scan(websocket: WebSocket, scan_id: str):
    await websocket.accept()

    r = aioredis.from_url(REDIS_URL, decode_responses=True)
    pubsub = r.pubsub()
    channel = f"scan:{scan_id}:events"
    await pubsub.subscribe(channel)

    try:
        deadline = asyncio.get_event_loop().time() + 300

        while True:
            now = asyncio.get_event_loop().time()
            if now > deadline:
                await websocket.send_text(json.dumps({
                    "stage": "failed", "message": "Scan timed out",
                    "progress": 0, "data": {}
                }))
                break

            try:
                message = await asyncio.wait_for(
                    pubsub.get_message(ignore_subscribe_messages=True),
                    timeout=1.0
                )
            except asyncio.TimeoutError:
                message = None

            if message and message.get("type") == "message":
                data = message["data"]
                await websocket.send_text(data)
                try:
                    parsed = json.loads(data)
                    if parsed.get("stage") in ("complete", "failed"):
                        break
                except Exception:
                    pass

            await asyncio.sleep(0.5)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({
                "stage": "failed", "message": str(e), "progress": 0, "data": {}
            }))
        except Exception:
            pass
    finally:
        await pubsub.unsubscribe(channel)
        await r.aclose()