from sqlalchemy.future import select
from sqlalchemy import desc
import os, time
from pathlib import Path

from RelayX.database.db import async_session
from RelayX.database.models import User, Message, Tokens
from Keys.public_key_private_key.db_encryptdecrypt import db_encrypt, db_decrypt
from RelayX.utils.keyring_manager import keyring_load_key

# Users ------------------------------------------------------------------------------------------------

key = keyring_load_key()

def burn_file(filepath : Path):
    try:
        if filepath.exists():
            with open(filepath, "r+b") as f:
                f.truncate(0)
                f.flush()
                os.fsync(f.fileno())
            filepath.unlink()
    except Exception:
        pass 


async def add_user(onion : str, display_name :str):
    async with async_session() as session:
        async with session.begin():
            user = User(onion=onion,display_name=display_name)
            session.add(user)

async def get_user(onion :str):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.onion == onion))
        user = result.scalar_one_or_none()
        return user
    
async def get_username(user_onion : str) -> str:
    user_record = await get_user(user_onion)
    if user_record:
        recipient_username = user_record.display_name
        return recipient_username
    
async def add_token(msg_id, filepath):
    async with async_session() as session:
        token = Tokens(msg_id=str(msg_id), path=filepath)
        session.add(token)
        await session.commit()

async def burn_token(msg_id):
    async with async_session() as session:
        result = await session.execute(select(Tokens).where(Tokens.msg_id == msg_id))
        token = result.scalar_one_or_none()
        if token is None or token.burned:
            return None
        filepath = Path(token.path)
        if os.path.exists(filepath):
            burn_file(filepath)
            token.burned = True
        await session.commit()
# Messages -----------------------------------------------------------------------------------------------

async def add_message(sender_onion : str, recipient_onion : str, message : str, msg_id : str):
    async with async_session() as session:
        async with session.begin():
            encrypted_message = db_encrypt(message)
            msg = Message(msg_id=str(msg_id), sender_onion=sender_onion, recipient_onion=recipient_onion, message=encrypted_message)
            session.add(msg)

async def mark_delivered(msg_id):
    async with async_session() as session:
        result = await session.execute(select(Message).where(Message.msg_id == msg_id))
        message = result.scalar_one_or_none()

        if not message:
            return
        message.delivered = True
        await session.commit()

async def fetch_undelivered(recipient_onion : str):
    async with async_session() as session:
        result = await session.execute(select(Message).where(Message.recipient_onion == recipient_onion, Message.delivered == False))
        messages = result.scalars().all()
        messages.reverse()
        print( [
        {
            "from" : m.sender_onion,
            "to" : m.recipient_onion,
            "msg" : db_decrypt(m.message).decode(),
            "timestamp" : m.TIMESTAMP,
            "msg_id" : m.msg_id
        }
        for m in messages
    ])

async def chat_history_load(user1 : str, user2 : str, before_ts = None,limit : int = 200) -> list[dict]:
    """Both user1 & user2 need to be their respective onions"""
    async with async_session() as session:
        query = select(Message).where(
            (
                ((Message.sender_onion == user1) & (Message.recipient_onion == user2)) | 
                ((Message.sender_onion == user2) & (Message.recipient_onion == user1))
            )
        )
        if before_ts is not None:
            query = query.where(Message.TIMESTAMP < before_ts)
            query  = (query.order_by(desc(Message.TIMESTAMP)).limit(limit))

        result = await session.execute(query)
        messages = result.scalars().all()
    messages.reverse()
    return [
        {
            "from" : m.sender_onion,
            "to" : m.recipient_onion,
            "msg" : db_decrypt(m.message),
            "timestamp" : m.TIMESTAMP,
            "msg_id" : m.msg_id
        }
        for m in messages
    ]
    
async def fetch_blocked_contacts() -> set[str]:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.blocked.is_(True)))
        return set(result.scalars().all())

async def fetch_contacts(current_onion) -> list[dict]:
    blocked_contacts = await fetch_blocked_contacts()
    async with async_session() as session:
        result = await session.execute(select(User).where((User.onion != current_onion) and (User.onion not in blocked_contacts)))
        users = result.scalars().all()
        return [
            {   
                "display_name" : user.display_name,
                "username" : user.onion,
            }
            for user in users
        ]
    
async def fetch_by_id(msg_id : str) -> dict[str]:
    """Fetches a single message from the DB by UUID (msg_id)"""
    async with async_session() as session:
        result = await session.execute(select(Message).where(Message.msg_id == msg_id))
        message = result.scalar_one_or_none()
        if not message:
            return None
        
        decrypted_text = db_decrypt(message.message)
        print(decrypted_text)

        return {
            "sender" : message.sender_onion,
            "recipient" : message.recipient_onion,
            "msg" : decrypted_text
        }

async def delete_message(msg_id : str) -> bool:
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(Message).where(Message.msg_id == msg_id))
            message = result.scalar_one_or_none()
            if not message:
                return False
            await session.delete(message)
        await session.commit()
        return True
    
async def set_block_status(onion : str, blocked_status : bool):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(User).where(User.onion == onion))
            user = result.scalar_one_or_none()
            if not user:
                return {"status" : "Failed", "msg" : "No such user exists"}
            
            user.blocked = blocked_status
        await session.commit()

async def cleanup_tokens():
    async with async_session() as session:
        result = await session.execute(select(Tokens))
        tokens = result.scalars().all()
        now_ts = int(time.time())
        for token in tokens:
            if now_ts - token.ts > 120:
                try:
                    if token.path and os.path.exists(token.path):
                        os.remove(token.path)
                except Exception:
                    pass
        await session.commit()