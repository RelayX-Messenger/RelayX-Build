from RelayX.database.crud import fetch_by_id
from RelayX.utils.config import user_onion
from RelayX.core.send_msg import ack_relay_send
async def forward_message(msg_id : str, new_recipient : str):
    original = await fetch_by_id(msg_id)
    if not original:
        return {"status" : "Fail", "msg" : "Message not found."}
    await ack_relay_send(original, user_onion, new_recipient)
    return {"status":"Forwarded"}
