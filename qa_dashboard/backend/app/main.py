
import logging
import json
import asyncio
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .api import router as api_router
from .db import get_questions 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("qa-dashboard")

app = FastAPI(title="QA Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

connected_websockets: List[WebSocket] = []
ws_lock = asyncio.Lock()

async def broadcast(event: str, payload):
    message = json.dumps({"event": event, "payload": payload}, default=str)
    async with ws_lock:
        to_remove = []
        for ws in connected_websockets:
            try:
                if ws.client_state.name == "CONNECTED" or getattr(ws, "client_state", None) is None:
                    await ws.send_text(message)
                else:
                    to_remove.append(ws)
            except Exception as e:
                logger.warning("WS send failed, removing ws: %s", e)
                try:
                    await ws.close()
                except:
                    pass
                to_remove.append(ws)

        for r in to_remove:
            if r in connected_websockets:
                connected_websockets.remove(r)

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    logger.info("WS: client connected")
    async with ws_lock:
        connected_websockets.append(ws)
    try:
        while True:
            try:
                data = await ws.receive_text()
            except WebSocketDisconnect:
                raise
            except Exception:
                break
            try:
                qid = int(data)
                questions_db = get_questions()
                for q in questions_db:
                    if q["question_id"] == qid:
                        await ws.send_text(json.dumps({"event": "status", "payload": q}, default=str))
            except Exception:
                pass

    except WebSocketDisconnect:
        logger.info("WS: client disconnected")
    except Exception as e:
        logger.exception("WS: unexpected error: %s", e)
    finally:
        async with ws_lock:
            if ws in connected_websockets:
                connected_websockets.remove(ws)

def get_broadcast_func():
    return broadcast

import inspect
import sys
try:
    import backend.app.api as api_mod  
    api_mod.broadcast = broadcast
except Exception:
    try:
        import app.api as api_mod  
        api_mod.broadcast = broadcast
    except Exception:
        logger.debug("Couldn't attach broadcast to api module (optional)")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
