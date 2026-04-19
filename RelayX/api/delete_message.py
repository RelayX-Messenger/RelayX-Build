from fastapi import APIRouter, HTTPException

from RelayX.database.crud import delete_message
from RelayX.models.request_models import DeleteChat

router = APIRouter()

@router.delete("/delete_message")
async def delete_one_message(request: DeleteChat):
    deleted = await delete_message(request.msg_id)
    if deleted:
        return {"status" : "success", "msg" : "Deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Message not found")