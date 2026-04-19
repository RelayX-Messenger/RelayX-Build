import asyncio
from utilities.encryptdecrypt.decrypt_message import decrypt_message
from RelayX.utils import config
from RelayX.database.crud import add_message
from utilities.network.Client_RelayX import send_via_tor

async def process_undelivered(envelope: dict):
    msg_id = envelope.get("msg_id")
    messages = envelope.get("msg", [])
    sender_onion = envelope.get("from")
    if not isinstance(messages, list):
        return
    delivered_any = False
    for msg in messages:
        inner_id = msg.get("msg_id")
        ack = {
            "type" : "ack_resp",
            "msg_id" : inner_id,
            "is_ack" : True
        }
        try:
            plaintext = decrypt_message(config.session_key[sender_onion], msg["msg"])
        except Exception as e:
            print(e)
        await add_message(sender_onion, config.user_onion, plaintext, inner_id)
        asyncio.create_task(send_via_tor(sender_onion, config.LISTEN_PORT, ack, config.PROXY))
        delivered_any = True
    if delivered_any:
        ack_env = {
            "type" : "ack_resp",
            "msg_id" : msg_id,
            "is_ack" : True
        }
        await send_via_tor(sender_onion, config.LISTEN_PORT, ack_env, config.PROXY)