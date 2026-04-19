from fastapi import APIRouter, WebSocket

from RelayX.utils.queue import state_queue

router = APIRouter()

@router.websocket("/state")
async def ws_state_endpoint(websocket : WebSocket):
    await websocket.accept()
    try:
        while True:
            state = await state_queue.get()
            await websocket.send_json(state)
    except Exception as e:
        print(f"[STATE WS ERROR] {e}")
    finally:
        await websocket.close()