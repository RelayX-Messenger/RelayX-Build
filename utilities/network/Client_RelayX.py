"""              Client_RelayX module

User side RelayX relay. Helpers for Recieving and sending messages.
By- Poojit Matukumalli
thats it. Go read the code 🙏
"""
# ==================== Imports =========================================================================================

import json, random, aiohttp_socks as asocks
import time, struct, msgpack, asyncio

from utilities.encryptdecrypt.encrypt_message import encrypt_message
from utilities.encryptdecrypt.decrypt_message import decrypt_message
from RelayX.utils.config import user_onion, relay_file, session_key
from utilities.encryptdecrypt.shield_crypto import derive_AEAD_envelope

# ========================= Helpers ====================================================================================
 
def load_active_relays():       # Loads active relays... Duh
    global relay_file
    try:
        with open(relay_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        relays = data.get("relays", [])
        active_relays = []
        for r in relays:
            if r.get("status") == "active" and r.get("onion"):
                addr = r["onion"]
                port = r.get("port", 5050)
                active_relays.append(f"{addr}:{port}")
        return active_relays
    except Exception as e:
        print(f"[ERR] Failed to load {relay_file}: {e}")
        return []

# Helpers ---------------------------------------------------------------------------------------------------------------

def encrypt_payload(chat_key: bytes, msg) -> str:
    return encrypt_message(chat_key, msg)              #GOTO encrypt_message

def decrypt_payload(chat_key: bytes, msg) -> str:
    return decrypt_message(chat_key, msg)              #GOTO decrypt_message
sys_rand = random.SystemRandom()

# Route builder (Helper)--------------------------------------------------------------------------------------------------

async def build_route(active_relays, min_hops=1, max_hops=1):
    if not active_relays:
        return []
    shuffled_list = active_relays.copy()
    sys_rand.shuffle(shuffled_list)

    k = min(len(shuffled_list), sys_rand.randint(min_hops, max_hops))
    route = shuffled_list[:k]
    return route

# Helper ----------------------------------------------------------------------------------------------------------------

def parse_hostport(addr: str):
    try:
        h, p = addr.rsplit(":", 1)
        return h, int(p)
    except:
        return None, None

async def send_via_tor_transport(onion_route: str, port: int, envelope: dict, proxy):
    """No AEAD. A helper for relay_send"""
    try:
        reader, writer = await asocks.open_connection(
            proxy_host=proxy[0],
            proxy_port=proxy[1],
            host=onion_route,
            port=port
        )
        env_type = envelope.get("type")
        data = msgpack.packb(envelope, use_bin_type=True)
        length = struct.pack("!I", len(data)) # Big Endian
        writer.write(length + data)
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        await writer.wait_closed()
        print(f"\n[{env_type}] Envelope sent → {onion_route}:{port}\n")
    except Exception as e:
        print(f"\n[FAIL] Transmission error → {onion_route}:{port} | {e}")

# Helper, Accessed by relay_send() ---------------------------------------------------------------------------------------
async def send_via_tor(onion: str, port: int, envelope: dict, proxy):
    """AEAD version for raw uses. Here onion is recipient_onion."""
    try:
        reader, writer = await asocks.open_connection(
            proxy_host=proxy[0],
            proxy_port=proxy[1],
            host=onion,
            port=port
        )
        env_type = envelope.get("type")
        envelope_bytes = msgpack.packb(envelope, use_bin_type=True)
        data = derive_AEAD_envelope(envelope_bytes, session_key[onion])
        env = {
            "sealed_envelope" : data,
            "from" : user_onion
            }
        env_bytes = msgpack.packb(env, use_bin_type=True)
        length = struct.pack("!I", len(env_bytes)) # Big Endian
        writer.write(length + env_bytes)
        await writer.drain()
        try:
            writer.write_eof()
        except (AttributeError, NotImplementedError):
            pass
        await asyncio.sleep(0.05)
        writer.close()
        await writer.wait_closed()
        print(f"\n[{env_type}] Envelope sent → {onion}:{port}\n")
    except Exception as e:
        print(f"\n[FAIL] Transmission error → {onion}:{port} | {e}")

# Helper, Accessed in the executor script --------------------------------------------------------------------------------

async def relay_send(message ,user_onion, recipient_onion,msg_uuid, show_route=True):
    try:
        active_relays = load_active_relays()
        if not active_relays:
            print("\n[ERR] No active relays found.")
            return

        route_relays = await build_route(active_relays, min_hops=1, max_hops=1)

        # route (user → relays → destination)
        route = [f"{user_onion}:5050"] + route_relays + [f"{recipient_onion}:5050"]
        if show_route:
            print("\n[ROUTE]\n")
            for i, hop in enumerate(route, start=1):
                print(f"Hop {i}. {hop.strip()}")

        route.pop(0) # popping onion to avoid (looping back
        env = {
            "msg_id" : msg_uuid,
            "payload": message,
            "from": user_onion,
            "to": recipient_onion,
            "stap": time.time(),
            "type": "msg"
        }
        env_bytes = msgpack.packb(env, use_bin_type=True)
        sealed_envelope = derive_AEAD_envelope(env_bytes, session_key[recipient_onion])
        envelope = {
            "route": route.copy(),
            "sealed_envelope" : sealed_envelope,
            "from" : user_onion
        }
        first_hop = route[0]
        host, port = parse_hostport(first_hop)
        if not host or port is None:
            print("\n[Error] Invalid first hop.\n")
            return
        proxy = ("127.0.0.1", 9050)
        await send_via_tor_transport(host, port, envelope, proxy)

    except Exception as e:
        print(f"\n[ERR] Relay send failed:\n{e}")