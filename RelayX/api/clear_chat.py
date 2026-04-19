from fastapi import APIRouter

from RelayX.database.crud import async_session
from RelayX.models.request_models import ClearChat
from RelayX.database.models import Message
from sqlalchemy import delete
from RelayX.utils.config import user_onion

router = APIRouter()

@router.delete("/clear_chat")
async def clear_chat(req : ClearChat) -> dict:
    global user_onion
    """Both user1 and user2 must be onions"""
    user1, user2 = user_onion, req.user_onion2
    if not user1 or not user2:
        return {"error":"Invalid User IDS"}
    try:
        async with async_session() as session:
            async with session.begin():
                result = await session.execute(delete(Message).where(
                ((Message.sender_onion == user1) & (Message.recipient_onion == user2)) | 
                ((Message.sender_onion == user2) & (Message.recipient_onion == user1)))) # type: ignore
                deleted = result.rowcount
        return {"status" : f"Chat Cleared. Deleted {deleted} message(s)"}
    except Exception as e:
        return {"error":"[DATABASE ERROR]\n", "detail": str(e)}