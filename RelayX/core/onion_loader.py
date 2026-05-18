import asyncio, os

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(ROOT, "..", ".."))

from utilities.network.network_service import tor_hostname_creation
from RelayX.utils import config, paths
from RelayX.database.crud import fetch_blocked_contacts

async def load_blocked():
    config.blocked_users = set(await fetch_blocked_contacts())
    
async def load_onion():
    addr_file = paths.hostname_path
    if not os.path.exists(addr_file):
        await tor_hostname_creation()
    for _ in range(50):
        if os.path.exists(addr_file):
            with open(addr_file, "r") as f:
                user_onion = f.read().replace("\n", "").strip()
                return user_onion     
        await asyncio.sleep(0.2)
    return