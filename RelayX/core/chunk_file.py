import time, uuid, asyncio
from multiprocessing import Pool

from utilities.network.Client_RelayX import send_via_tor
from utilities.encryptdecrypt.encrypt_message import encrypt_bytes
from RelayX.utils.config import session_key, PROXY, LISTEN_PORT, user_onion
from RelayX.utils import config
from RelayX.utils.queue import pending_lock

ACK_TIMEOUT = 8
MAX_RETRIES = 5

def file_init_metadata(total_chunks : int, filename : str, msg_id) -> dict:
    return {
        "type": "FILE_TRANSFER_INIT",
        "msg_id" : msg_id,
        "from": user_onion,
        "total_chunks" : total_chunks,
        "filename" : filename,
        "ts" : int(time.time())
    }


def _encrypt_chunk_helper(args : tuple[int, bytes, bytes]):
    """Returns chunk_index  (class int) and encrypted_byes (class bytes)"""
    chunk_index, chunk_bytes, session_key = args
    encrypted_bytes = encrypt_bytes(session_key, chunk_bytes)
    return chunk_index, encrypted_bytes

def encrypt_chunks(chunks : dict, session_key : bytes, processes:int = 4) -> dict:
    """Func for Parallel encryption of chunks"""
    with Pool(processes) as pool:
        results = pool.map(_encrypt_chunk_helper, [(i,b,session_key) for i, b in chunks.items()])
    return dict(results)


async def send_chunk_process(chunk_index, chunk_data, target_onion, msg_id):
    packet = {
        "type" : "FILE_CHUNK",
        "from" : user_onion,
        "to" : target_onion,
        "msg_id" : msg_id,
        "chunk_index" : chunk_index,
        "data" : chunk_data
    }
    await send_via_tor(target_onion, LISTEN_PORT, packet, PROXY)


async def _send_loop(msg_id: str):
    while True:
        to_send = []
        async with pending_lock:
            t = config.pending_transfers.get(msg_id) # t because im lazy
            if not t:
                return
            now = time.time()

            inflight = sum(1 for c in t["chunks"].values() if not c["acked"] and c["sent_ts"] and now - c["sent_ts"] < ACK_TIMEOUT)
            while inflight < t["window"]:
                next_idx = t["last_sent"] + 1

                if next_idx >= t["total_chunks"]:
                    break

                chunk = t["chunks"][next_idx]

                if chunk["acked"]:
                    t["last_sent"] = next_idx
                    continue

                if chunk["sent_ts"] == 0 or now - chunk["sent_ts"] >= ACK_TIMEOUT:
                    chunk["sent_ts"] = now
                    chunk["retries"] += 1

                    if chunk["retries"] > MAX_RETRIES:
                        print("[CHUNK SEND FAILED] Max retries hit")
                        chunk["acked"] = True
                        t["last_sent"] = next_idx
                        continue

                    to_send.append((next_idx, chunk["data"], t["to"], msg_id))
                    inflight += 1
                    t["last_sent"] = next_idx
                else:
                    break

        for args in to_send:
            await send_chunk_process(*args)
        async with pending_lock:
            t = config.pending_transfers.get(msg_id)
            if not t:
                return
            
            all_acked = all(c.get("acked") for c in t["chunks"].values())
            if all_acked:
                print(f"[FILE SEND COMPLETE]")
                del config.pending_transfers[msg_id]
                return
        await asyncio.sleep(0.1)


async def send_file(chunks : dict , target_onion : str, filename : str):
    """
    chunks : {index : bytes}
    """

    msg_id = str(uuid.uuid4())
    total_chunks = len(chunks)
    key = session_key[target_onion]
    if not key:
        print(f"[FILE_SEND_ERROR] Cannot send {filename}.\nNo Session key exists for {target_onion}")
        return
    
    encrypted_chunks = encrypt_chunks(chunks, key)
    
    async with pending_lock:
        config.pending_transfers[msg_id] = {
            "to" : target_onion,
            "chunks" : {idx : 
                        {"data" : chunk_data,"acked" : False, "retries" : 0,
                            "sent_ts" : 0} for idx, chunk_data in encrypted_chunks.items()},
            "next_idx" : 0,
            "last_acked" : -1,
            "window" : 16,
            "total_chunks" : total_chunks,
            "ts" : int(time.time()),
            "last_sent" : -1
        }
    # Details so the recipient can join chunks
    metadata_packet = file_init_metadata(total_chunks, filename, msg_id)
    await send_via_tor(target_onion, LISTEN_PORT, metadata_packet, PROXY)
    asyncio.create_task(_send_loop(msg_id))
