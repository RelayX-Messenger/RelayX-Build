from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from contextlib import asynccontextmanager

from RelayX.api import init, send, recieve, clear_chat, delete_message, delete_account, blocked_state
from RelayX.api import fetch_history, fetch_contacts, state_ws, file_sending, tokens_api, shutdown
from RelayX.database.models import init_db
from RelayX.core.inbound import inbound_listener
from RelayX.core.tor_bootstrap import start_tor, stop_tor
from RelayX.database.crud import cleanup_tokens

green = "\033[0;32m"
cyan = "\033[0;36m"
reset = "\033[0m"

@asynccontextmanager
async def lifespan(app:FastAPI):
    print(f"{green}INFO{reset}:     [{cyan}RelayX Core{reset}] Starting up.")
    tasks = []
    start_tor()
    await init_db()
    tasks.append(asyncio.create_task(inbound_listener()))
    tasks.append(asyncio.create_task(cleanup_tokens()))
    try:
        yield
    finally:
        print("[RelayX Core] Shutting down.")
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        stop_tor()

app = FastAPI(lifespan=lifespan)

origins = [
    "*",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow POST, GET, etc.
    allow_headers=["*"],  # Allow all headers
)
app.include_router(send.router)
app.include_router(delete_message.router)
app.include_router(init.router)
app.include_router(recieve.router)
app.include_router(clear_chat.router)
app.include_router(fetch_history.router)
app.include_router(fetch_contacts.router)
app.include_router(state_ws.router)
app.include_router(file_sending.router)
app.include_router(delete_account.router)
app.include_router(blocked_state.router)
app.include_router(tokens_api.router)
app.include_router(shutdown.router)

@app.get("/status")
def status():
    return {"Online":True}
