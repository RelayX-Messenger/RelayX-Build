import asyncio, uuid, traceback
from RelayX.database.crud import fetch_undelivered, fetch_contacts
from utilities.network.Client_RelayX import send_via_tor, send_via_tor_transport
from RelayX.utils import config, queue
from utilities.encryptdecrypt.encrypt_message import encrypt_message
from Keys.public_key_private_key.generate_keys import handshake_initiator, make_init_message

def make_envelope(msg_id, recipient_onion, message_content):
    return {
        "from" : config.user_onion,
        "to" : recipient_onion,
        "msg" : message_content,
        "msg_id" : msg_id,
        "msg_type" : "UNDELIVERED"
    }

async def ack_undelivered_send(undelivered_env: dict,recipient_onion: str, msg_id: str):
    """ 
    undelivered env : list[dict]
    [ {from, to, msg, ts, msg_id}, {from, to, msg, ts, msg_id}, ... ]
    """
    event = asyncio.Event()
    async with queue.pending_ack_lock:
        queue.pending_ack[msg_id] = event
    try:
        for Attempt in range(5):      
            for msg_dict in undelivered_env:
                msg : bytes = msg_dict.get("msg")
                msg_dict["msg"] = encrypt_message(config.session_key[recipient_onion], msg.decode())
            env = make_envelope(msg_id, recipient_onion, undelivered_env)
            await send_via_tor(recipient_onion, config.LISTEN_PORT, env, config.PROXY)
            try:
                await asyncio.wait_for(event.wait(), timeout=15)
                return True
            except asyncio.TimeoutError:
                continue
        return False
    finally:
        async with queue.pending_ack_lock:
            queue.pending_ack.pop(msg_id, None)


async def send_to_peers(contacts: list[dict]):
    sem = asyncio.Semaphore(3)

    async def handle_peer(contact: dict):
        async with sem:
            try:
                if not config.session_key.get(contact["username"]):
                    await handshake_initiator(config.user_onion, contact.get("username"), send_via_tor_transport, make_init_message)
                undelivered = await fetch_undelivered(contact.get("username"))
                if not undelivered:
                    return
                await ack_undelivered_send(undelivered, contact.get("username"), str(uuid.uuid4()))
            except Exception as e:
                traceback.print_exc()
                print("Error", e)
                return
    tasks = [asyncio.create_task(handle_peer(c)) for c in contacts]
    await asyncio.gather(*tasks)

async def undelivered_send():
    contacts = await fetch_contacts(config.user_onion)
    if not contacts:
        return
    await send_to_peers(contacts)