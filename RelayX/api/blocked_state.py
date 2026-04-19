from fastapi import APIRouter

from RelayX.database.crud import set_block_status
from RelayX.models.request_models import BlockStatus
from RelayX.core.onion_loader import load_blocked

router = APIRouter()

@router.post("/set_block_state")
async def set_block(request : BlockStatus):
    try:
        onion, block_status = request.onion, request.block_status
        await set_block_status(onion, block_status)
        await load_blocked()
        return {"status" : "Success", "msg": f"User has been {'Blocked' if block_status else 'Unblocked'}"}
    except Exception as e:
        return {"status" : "failed", "msg" : f"[ERROR]\n{e}"}