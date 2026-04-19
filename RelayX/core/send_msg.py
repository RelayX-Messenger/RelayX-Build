import asyncio

from utilities.network.Client_RelayX import relay_send
from RelayX.utils import queue
from utilities.encryptdecrypt.encrypt_message import encrypt_message
from RelayX.utils import config

async def ack_relay_send(message: str, user_onion: str, recipient_onion: str, msg_id: str):
    event = asyncio.Event()
    async with queue.pending_ack_lock:
        queue.pending_ack[msg_id] = event
    try:
        for Attempt in range(5):
            cipher = encrypt_message(config.session_key[recipient_onion], message)
            await relay_send(message=cipher, user_onion=user_onion, recipient_onion=recipient_onion,msg_uuid=msg_id, show_route=True)
            try:
                await asyncio.wait_for(event.wait(), timeout=15)
                return True
            except asyncio.TimeoutError:
                continue
        return False
    finally:
        async with queue.pending_ack_lock:
            queue.pending_ack.pop(msg_id, None)