"""              tor_transport module

User side RelayX relay. Helpers for Recieving and sending messages.
By- Poojit Matukumalli
thats it. Go read the code 🙏
"""
# ==================== Imports =========================================================================================

import random, aiohttp_socks as asocks
from typing import Any
import struct, msgpack

from utilities.encryptdecrypt.encrypt_message import encrypt_message
from utilities.encryptdecrypt.decrypt_message import decrypt_message
from RelayX.utils.config import user_onion, session_key, LISTEN_PORT, PROXY
from utilities.encryptdecrypt.shield_crypto import derive_AEAD_envelope


# Helpers ---------------------------------------------------------------------------------------------------------------

def encrypt_payload(chat_key: bytes, msg: str) -> str:
    return encrypt_message(chat_key, msg)              #GOTO encrypt_message

def decrypt_payload(chat_key: bytes, msg: str) -> str:
    return decrypt_message(chat_key, msg)              #GOTO decrypt_message
sys_rand = random.SystemRandom()

async def _send_tor_data(
    onion: str,
    port: int,
    data: bytes,
    proxy: tuple[str, int],
) -> None:
    """Raw function that opens an aiohttp socks connection and handles sending the data."""
    reader, writer = await asocks.open_connection( #pyright: ignore[reportUnknownMemberType, reportUnusedVariable]
        proxy_host=proxy[0],
        proxy_port=proxy[1],
        host=onion,
        port=port
    )
    try:
        length = struct.pack("!I", len(data)) # Big Endian
        writer.write(length + data)
        await writer.drain()
        writer.close()
    except Exception as e:
        print(e)
    finally:
        await writer.wait_closed()
    
# Helper ----------------------------------------------------------------------------------------------------------------

async def send_via_tor_transport(onion: str, envelope: dict[str, str | Any]):
    """No AEAD. A helper for relay_send"""
    try:
        env_type = envelope.get("type")
        data: bytes = msgpack.packb(envelope, use_bin_type=True)

        await _send_tor_data(
            onion=onion,
            port = LISTEN_PORT,
            data = data,
            proxy = PROXY
        )

        print(f"\n[{env_type}] Envelope sent → {onion}:{LISTEN_PORT}\n")

    except Exception as e:
        print(f"\n[FAIL] Transmission error → {onion}:{LISTEN_PORT} | {e}")

# Helper, Accessed by relay_send() ---------------------------------------------------------------------------------------
async def send_payload(onion: str, envelope: dict[str, str | Any]):
    """AEAD version for raw uses. Here onion is recipient_onion."""
    try:
        env_type = envelope.get("type")
        envelope_bytes = msgpack.packb(envelope, use_bin_type=True)
        sealed_data = derive_AEAD_envelope(envelope_bytes, session_key[onion])

        env = {
            "sealed_envelope" : sealed_data,
            "from" : user_onion
            }
        env_bytes: bytes = msgpack.packb(env, use_bin_type=True)

        await _send_tor_data(
            onion=onion,
            port = LISTEN_PORT,
            data = env_bytes,
            proxy = PROXY
        )
        print(f"\n[{env_type}] Envelope sent → {onion}:{LISTEN_PORT}\n")

    except Exception as e:
        print(f"\n[FAIL] Transmission error → {onion}:{LISTEN_PORT} | {e}")
