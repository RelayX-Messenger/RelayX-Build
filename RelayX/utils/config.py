import os, asyncio, sys, pathlib

from RelayX.core.onion_loader import load_onion
from utilities.network.network_service import HSDIR

#-------------------------------------- Configs --------------------------------------------------------------------------

RelayX_exe_location = pathlib.Path(sys.executable).parent # sys.executable returns python.exe's Location, But after compiling, It will point to RelayX.exe's Location.
APPDATA = os.getenv("APPDATA")
LOCALAPPDATA = os.getenv("LOCALAPPDATA")

ROTATE_INTERVAL = 600
ROTATE_AFTER_MESSAGES = 25
LISTEN_PORT = 5050
PROXY = ("127.0.0.1", 9050)
message_count = 0
session_key = {}
ack_dict = {}
TOKEN_EXPIRY = 120

# Paths & onion -----------

torrc_path = os.path.join(APPDATA, "RelayX", "torrc")
hostname_path = os.path.join(HSDIR, "hostname")
tor_necessities = os.path.join(HSDIR, "tor_necessities")
libs_dir = os.path.join(RelayX_exe_location, "..", "libs")
db_filepath = os.path.join(LOCALAPPDATA, "RelayX", "RelayX.db")

tor_path = os.path.join(RelayX_exe_location, '..', "tor", "tor.exe" )
relay_file = os.path.join(APPDATA, "RelayX", "Routing", "relay_list.json")
user_onion = asyncio.run(load_onion())

# State

incoming_transfers = {}
pending_transfers = {}
blocked_users : set[str] = set()