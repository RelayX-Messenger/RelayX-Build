from fastapi import APIRouter
from plyer import notification

from RelayX.models.request_models import DeleteAccont
from RelayX.core.delete_account import perform_account_deletion

router = APIRouter()

@router.delete("/delete_account")
async def delete_account(req : DeleteAccont):
    if not req.confirm:
        return {"status": "Auth not completed"}
    await perform_account_deletion()
    notification.notify(title="RelayX Core : Account Deletion successful.", message="Your RelayX Account has been deleted. Restart the app to setup a new Account.", timeout=4)
    return
