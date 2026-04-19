# ============================================== Imports ===================================================================

import base64, os, time, asyncio
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from RelayX.utils import config
from RelayX.utils.queue import rotation_lock
from utilities.encryptdecrypt.shield_crypto import derive_shield_key
# ---------------- Pending handshakes ---------------------------------------------

pending_handshakes = {} # Dict{str, Tuple(X25519PrivateKey, bytes, asyncio.Future)}

# ================================================ Functions ===========================================================

def b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode()

# ---------------------------------------------------

def b64_decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data.encode())

# ----------------------------------------------------

def generate_x25519(): # -> Tuple(X25519PrivateKey, bytes)
    private_key = X25519PrivateKey.generate()
    public_key = private_key.public_key()
    # serialize public key to raw bytes (32 bytes)
    public_bytes = public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)
    return private_key, public_bytes

# ------------------------------------------------------------------------------------------

def derive_shared_key(private_key: X25519PrivateKey, peer_public_key_bytes: bytes) -> bytes:
    peer_pub = X25519PublicKey.from_public_bytes(peer_public_key_bytes)
    return private_key.exchange(peer_pub)

# --------------------------------------------------------------------------------
def make_init_message(public_bytes,nonce_a, user_onion) -> dict:
    return {
        "type": "HANDSHAKE_INIT",
        "from": user_onion,
        "pub" : b64_encode(public_bytes),
        "nonce": b64_encode(nonce_a),
        "ts" : int(time.time())
    }

# -------------------------------------------------------------------------------------

def make_resp_message(public_bytes, user_onion, nonce_a_b64, nonce_b) -> dict:
    return {
        "type": "HANDSHAKE_RESP",
        "from": user_onion,
        "pub" : b64_encode(public_bytes),
        "nonce_reply": nonce_a_b64,
        "nonce_b": b64_encode(nonce_b),
        "ts" : int(time.time())
    }

# ============================================== Handshake =============================================================

async def handshake_initiator(user_onion: str, peer_onion: str, send_via_tor_transport,make_init_message,proxy=("127.0.0.1", 9050), timeout=25):
    my_private, my_public_bytes = generate_x25519()
    nonce_a = os.urandom(16)
    # make_init_message expects (public_bytes, nonce_a, user_onion)
    initial = make_init_message(my_public_bytes, nonce_a, user_onion)
    loop = asyncio.get_event_loop()
    future_response = loop.create_future()
    pending_handshakes[peer_onion] = (my_private, nonce_a, future_response)

    await send_via_tor_transport(peer_onion, 5050, initial, proxy)
    try:
        resp = await asyncio.wait_for(future_response, timeout=timeout)
        if resp.get("nonce_reply") != b64_encode(nonce_a):
            return None
        peer_pub_bytes = b64_decode(resp["pub"])
        nonce_b = b64_decode(resp["nonce_b"])
        shared_key = derive_shared_key(my_private, peer_pub_bytes)
        async with rotation_lock:
            config.session_key[peer_onion] = derive_shield_key(shared_key, nonce_a, nonce_b)
            return config.session_key[peer_onion]
    except asyncio.TimeoutError:
        print("TIMEOUT")
        return None
    finally:
        pending_handshakes.pop(peer_onion, None)

# ========================================= Reciever (Handhshake) ====================================================

async def handshake_responder(envelope: dict, user_onion: str, send_via_tor_transport, proxy=("127.0.0.1", 9050)):
    type = envelope.get("type")
    peer = envelope.get("from", "")
    if type == "HANDSHAKE_INIT":
        try:
            peer_public = b64_decode(envelope["pub"])
            nonce_a = b64_decode(envelope["nonce"])
        except Exception:
            return None
        my_private, my_public = generate_x25519()
        nonce_b = os.urandom(16)
        resp_msg = make_resp_message(my_public, user_onion, envelope.get("nonce"), nonce_b)
        await send_via_tor_transport(peer, 5050, resp_msg, proxy=proxy)
        shared_key = derive_shared_key(my_private, peer_public)
        async with rotation_lock:
            config.session_key[peer] = derive_shield_key(shared_key, nonce_a, nonce_b)
            return config.session_key[peer]
    elif type == "HANDSHAKE_RESP":
        if peer in pending_handshakes:
            _, _, future = pending_handshakes[peer]
            if not future.done():
                future.set_result(envelope)
        return None
    return None