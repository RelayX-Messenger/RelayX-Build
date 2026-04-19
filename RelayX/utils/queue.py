import asyncio
incoming_queue = asyncio.Queue()
pending_ack : dict[str, asyncio.Event] = {}
pending_ack_lock = asyncio.Lock()
rotation_lock = asyncio.Lock()
rotation_started = False
state_queue = asyncio.Queue()
pending_lock = asyncio.Lock()