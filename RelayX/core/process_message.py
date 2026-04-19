import asyncio, msgpack
from plyer import notification
from cryptography.exceptions import InvalidTag

from RelayX.utils.queue import incoming_queue, pending_ack, pending_ack_lock
from utilities.encryptdecrypt.decrypt_message import decrypt_message
from RelayX.utils.config import PROXY, user_onion
from utilities.network.Client_RelayX import send_via_tor, send_via_tor_transport
from RelayX.database.crud import add_message, get_username, mark_delivered
from Keys.public_key_private_key.generate_keys import handshake_responder
from RelayX.core.handshake import do_handshake
from RelayX.utils import config
from RelayX.utils.queue import state_queue
from RelayX.core.file_transfer import handle_file_chunk, handle_file_chunk_ack, handle_file_init
from utilities.encryptdecrypt.shield_crypto import verify_AEAD_envelope
from RelayX.core.process_undelivered import process_undelivered

session_key = config.session_key
blocked_contacts = config.blocked_users 

def _log_task_exception(task):
    try:
        task.result()
    except Exception as e:
        print("[ERROR]\n",e)

def run_and_log(coro):
    task = asyncio.create_task(coro)
    task.add_done_callback(_log_task_exception)
    return task

#----- Layer 3, Encrypted message handling -------------------------------------------------------------------------------

async def handle_message(recipient_onion, envelope):
    recipient_username = await get_username(recipient_onion)
    msg_id = envelope.get("msg_id")
    msg = envelope.get("payload", "")
    decrypted = await asyncio.to_thread(decrypt_message, config.session_key.get(recipient_onion), msg)
    await incoming_queue.put(msg_id)
    await add_message(user_onion, recipient_onion, decrypted, msg_id)
    if decrypted:     
        print(f"\n[INCOMING MESSAGE]\nFrom: {recipient_username}\nMsg: {decrypted}\n")
        ack_env = {
            "type" : "ack_resp",
            "msg_id": envelope.get("msg_id"),
            "to": recipient_onion,
            "stap": envelope.get("stap"),
            "is_ack": True,
        }
        await send_via_tor(recipient_onion,5050, ack_env, PROXY)
    else:
        asyncio.to_thread(notification.notify(title="RelayX Core : [Warn]", message=f"A message from {recipient_username} failed to Decrypt.", timeout=4))

#----- Layer 2, Routing to functions.--------------------------------------------------------------------------------------

async def route_envelope(sender, envelope):
    envelope_type = envelope["type"]

    if envelope.get("is_ack"):
        msg_id = envelope.get('msg_id')
        async with pending_ack_lock:
            event = pending_ack.get(msg_id)
        if event:
            event.set()
        await state_queue.put(f"\n[ACK RECEIVED]\nMessage ID : {msg_id}\n")
        run_and_log(mark_delivered(msg_id))
        return

    if envelope_type == "msg":
        await handle_message(sender, envelope) # GOTO Layer 3
    
    if envelope_type == "FILE_TRANSFER_INIT":
        await handle_file_init(envelope)
        return
    
    elif envelope_type == "FILE_CHUNK":
        await handle_file_chunk(envelope)
        return
    
    elif envelope_type == "FILE_ACK":
        await handle_file_chunk_ack(envelope)
        return
    elif envelope_type == "UNDELIVERED":
        await process_undelivered(envelope)

#----- Layer 1, Encrypted data processing ------------------------------------------------------------------------------

async def process_encrypted(recipient_onion, outer):
    key = session_key.get(recipient_onion)
    if not key:
        run_and_log(do_handshake(user_onion, recipient_onion, send_via_tor_transport))
        return
    try:
        inner = verify_AEAD_envelope(outer["sealed_envelope"], key)
        envelope = msgpack.unpackb(inner, raw=False)
    except InvalidTag:
        asyncio.to_thread(notification.notify(title="RelayX Core: [Severe]. Possible Interception.", message=f"A message from {await get_username(recipient_onion)} was tampered with. Restart the Network service.", timeout=4))
        return
    except Exception:
        asyncio.to_thread(notification.notify(title="RelayX Core: [Moderate]", message=f"Message from {await get_username(recipient_onion)} Failed to process.", timeout=4))
        return
    await route_envelope(recipient_onion, envelope) # GOTO Layer 2

#----- Layer 0, Handshake handling and outer env handling.-----------------------------------------------------------------

async def process_outer(outer : dict):
    sender = outer.get("from")
    if not isinstance(sender, str):
        return
    recipient_onion = sender.strip().replace("\n", "")
    if recipient_onion in blocked_contacts:
        return
    recipient_username = await get_username(recipient_onion)
    if outer.get("type") in ["HANDSHAKE_INIT", "HANDSHAKE_RESP"]:
        try:
            await asyncio.wait_for(handshake_responder(outer, user_onion, send_via_tor_transport), timeout=25)
        except asyncio.TimeoutError:
            pass
        if outer.get("type") == "HANDSHAKE_INIT":
            print(f"[HANDSHAKE_INIT]\nSent To  {recipient_username}")
        else:
            print(f"[HANDSHAKE_RESP] Received from {recipient_username}")
        return
    asyncio.create_task(process_encrypted(recipient_onion, outer)) # GOTO: Layer 1