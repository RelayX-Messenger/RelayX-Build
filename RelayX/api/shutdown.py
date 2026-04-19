from fastapi import APIRouter

from RelayX.core.delete_account import shutdown_backend
from RelayX.core.tor_bootstrap import stop_tor

router = APIRouter()

@router.post("/shutdown")
async def shutdown() -> None:
    """Shuts the Local ASGI server down."""
    try:
        stop_tor()
        await shutdown_backend()
    except Exception as e:
        return {"status": "Fail", "msg":e}