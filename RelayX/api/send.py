from fastapi import APIRouter
import uuid, asyncio

from utilities.network.Client_RelayX import send_via_tor_transport
from RelayX.models.request_models import SendModel
from RelayX.utils.config import ROTATE_AFTER_MESSAGES, user_onion
from Keys.public_key_private_key.generate_keys import handshake_initiator, make_init_message
from RelayX.utils import config
from RelayX.core.send_msg import ack_relay_send
from RelayX.database.crud import add_message

router = APIRouter()

async def _helper_send(model):
    global user_onion
    msg_id = str(uuid.uuid4())
    recipient_onion = model.recipient_onion
    if recipient_onion not in config.session_key:
        await handshake_initiator(user_onion, recipient_onion, send_via_tor_transport, make_init_message)
    try:
        if config.session_key[recipient_onion] is None:
            return
    except KeyError:
        pass
    plaintext = model.msg
    await ack_relay_send(plaintext, user_onion, recipient_onion, msg_id)
    await add_message(user_onion, recipient_onion, plaintext, msg_id)
    config.message_count += 1
    if config.message_count >= ROTATE_AFTER_MESSAGES:
        await handshake_initiator(user_onion, recipient_onion, send_via_tor_transport, make_init_message)
        config.message_count = 0


@router.post("/send")
async def send_message(model : SendModel):
    asyncio.create_task(_helper_send(model))
    return {"ok" : True}