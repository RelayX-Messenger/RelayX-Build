from fastapi import APIRouter   ;   from plyer import notification
import asyncio

from RelayX.utils.config import user_onion
from RelayX.core.send_undelivered import undelivered_send

router = APIRouter()

@router.post("/init")
async def init_state():
    """Initializes User state and sends undelivered messages."""
    if not user_onion:
        notification.notify(title="RelayX Core: [Severe]", message=f"Unable to load your Networking Identity. Please restart the Network service", timeout=4)
        return {"Error" : "Networking Identity not found"}
    asyncio.create_task(undelivered_send())
    return {"Status" : "Initialized", "user_onion" : user_onion}