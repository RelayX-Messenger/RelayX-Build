import asyncio

from RelayX.core.onion_loader import load_onion

#-------------------------------------- Configs --------------------------------------------------------------------------

ROTATE_INTERVAL = 600
ROTATE_AFTER_MESSAGES = 25
LISTEN_PORT = 5050
PROXY = ("127.0.0.1", 9050)
message_count = 0
session_key = {}
ack_dict = {}
TOKEN_EXPIRY = 120

# onion -----------

user_onion = asyncio.run(load_onion())

# State

incoming_transfers = {}
pending_transfers = {}
blocked_users : set[str] = set()