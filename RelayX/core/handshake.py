from RelayX.utils import config
from Keys.public_key_private_key.generate_keys import handshake_initiator, make_init_message


async def do_handshake(user_onion, recipient_onion, send_via_tor_transport):
    try:
        config.session_key[recipient_onion] = await handshake_initiator(user_onion, recipient_onion, send_via_tor_transport, make_init_message)
    except Exception as e:
        raise("Handshake Error", e)