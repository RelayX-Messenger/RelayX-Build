import asyncio, struct, msgpack

from RelayX.core.process_message import process_outer

green = "\033[0;32m"
cyan = "\033[0;36m"
reset = "\033[0m"


async def handle_incoming(reader, writer):
    global user_onion
    try:
        raw_len = await reader.readexactly(4)
        msg_len = struct.unpack("!I", raw_len)[0]
        payload = await reader.readexactly(msg_len)

        outer = msgpack.unpackb(payload, raw=False)
        if not outer:
            print("[INBOUND_ERROR]\nNo envelope")
            return
        
        await process_outer(outer)
    except Exception as e:
        print(f"[ERROR]\n{e}")
    finally:
        writer.close()
        await writer.wait_closed()

async def inbound_listener():
    server = await asyncio.start_server(handle_incoming, "127.0.0.1", 5050)
    print(f"{green}INFO{reset}:     [{cyan}Inbound Listener{reset}] Listener Active on 127.0.0.1:{5050}")
    async with server:
        await server.serve_forever()