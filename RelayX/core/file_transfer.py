import os, time, asyncio, orjson

from utilities.chunker.chunker import chunk_file
from RelayX.core.chunk_file import send_file
from RelayX.core.handshake import do_handshake
from RelayX.utils import config
from RelayX.utils.config import user_onion, session_key, PROXY
from RelayX.utils.queue import pending_lock
from utilities.encryptdecrypt.decrypt_message import decrypt_bytes
from utilities.network.Client_RelayX import send_via_tor


CHUNK_SIZE = 1024 * 1024
WINDOW_SIZE = 16

def write_chunk(path, idx, decrypted):
    with open(path, "r+b") as f:
        f.seek(idx * CHUNK_SIZE)
        f.write(decrypted)

async def file_transfer(filepath, target_onion):
    filename = os.path.basename(filepath)
    #await do_handshake(user_onion, target_onion, send_via_tor)

    chunks = chunk_file(filepath)
    if not chunks:
        print(f"[ERROR] Failed to chunk file : {filepath}")
        return
    await send_file(chunks, target_onion, filename)



async def handle_file_init(packet):
        msg_id = packet.get("msg_id")
        total_chunks = packet["total_chunks"]
        tmp_path = f"tmp_{msg_id}.bin"

        with open(tmp_path, "wb") as f:
            f.truncate(total_chunks * CHUNK_SIZE)

        async with pending_lock:
            config.incoming_transfers[msg_id] = {
                "from" : packet["from"],
                "file_name" : packet["filename"],
                "total_chunks" : total_chunks,
                "msg_id" : msg_id,
                "received" : set(),
                "last_chunk_len" : 0,
                "path" : tmp_path,
                "last_acked" : -1,
                "ts" : time.time()
            }

async def handle_file_chunk(packet : dict):
    msg_id = packet.get("msg_id")
    idx = packet.get("chunk_index")
    sender_onion = packet["from"]
    encrypted_data = packet["data"]

    async with pending_lock:
        transfer = config.incoming_transfers.get(packet["msg_id"])
        if idx == transfer["total_chunks"] - 1:
            transfer["last_chunk_len"] = len(encrypted_data)
        if not transfer:
            return
        
        if idx in transfer["received"]:
            return
        
        if packet["from"] != transfer["from"]:
            return
        
        path = transfer["path"]
        filename = transfer["file_name"]
    key = session_key.get(sender_onion)
    decrypted = decrypt_bytes(key, encrypted_data)
    await asyncio.to_thread(write_chunk, path, idx, decrypted)

    async with pending_lock:
        transfer["received"].add(idx)
        transfer["ts"] = time.time()

        expected = transfer["last_acked"] + 1
        while expected in transfer["received"]:
            expected += 1
        new_acked_upto = expected -1
        should_ack = new_acked_upto > transfer["last_acked"]
        transfer["last_acked"] = new_acked_upto

        if len(transfer["received"]) % WINDOW_SIZE == 0:
            meta_path = f"{path}.meta"
            with open(meta_path, "wb") as f:
                f.write(orjson.dumps(list(transfer["received"])))
        complete = len(transfer["received"]) == transfer["total_chunks"]
    if should_ack:
        ack_env = {
                "type" : "FILE_ACK",
                "msg_id": msg_id,
                "acked_upto" : new_acked_upto,
                "from": user_onion,
                "to": sender_onion,
            }
        asyncio.create_task(send_via_tor(sender_onion,5050, ack_env, PROXY))
    
    if complete:
        last_idx = transfer["total_chunks"] - 1
        last_size = transfer.get("last_chunk_len", CHUNK_SIZE)
        final_size = last_idx * CHUNK_SIZE + last_size

        with open(path, "r+b") as f:
            f.truncate(final_size)
        os.rename(path, filename)
        meta_path = f"{path}.meta"
        if os.path.exists(meta_path):
            os.remove(meta_path)
            
        async with pending_lock:
            del config.incoming_transfers[msg_id]

        print(f"[RELAYX] File {msg_id} reconstructed successfully at {filename}")


async def handle_file_chunk_ack(packet : dict):
    msg_id = packet.get("msg_id")
    acked_upto = packet.get("acked_upto")

    async with pending_lock:
        transfer = config.pending_transfers.get(msg_id)
        if not transfer:
            return
        if acked_upto <= transfer["last_acked"]:
            return
        
        transfer["last_acked"] = acked_upto

        for idx, chunk in transfer["chunks"].items():
            if idx <= acked_upto:
                chunk["acked"] = True
        
        transfer["ts"] = time.time()

        done = transfer["last_acked"] + 1 == transfer["total_chunks"]

    if done:
        async with pending_lock:
            config.pending_transfers.pop(msg_id)
        
        print(f"[RELAYX] File {msg_id} fully delivered")