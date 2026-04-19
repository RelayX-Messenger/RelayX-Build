from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, func
import time

from RelayX.database.db import Base, engine
green = "\033[0;32m"
cyan = "\033[0;36m"
reset = "\033[0m"


class User(Base):
    __tablename__ = "users"
    onion = Column(String, nullable=False, primary_key=True)
    display_name = Column(String)
    blocked = Column(Boolean, default=False)
    last_seen = Column(TIMESTAMP, default=func.now(), onupdate=func.now())

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    msg_id = Column(String, nullable=False)
    sender_onion = Column(String, nullable=False)
    recipient_onion = Column(String, nullable=False)
    message = Column(String, nullable=False)
    TIMESTAMP = Column(TIMESTAMP, default=func.now())
    delivered = Column(Boolean, default=False)

class Tokens(Base):
    __tablename__ = "tokens"
    msg_id = Column(String, primary_key=True,nullable=True)
    path = Column(String)
    ts = Column(Integer, default=int(time.time()))
    burned = Column(Boolean, default=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print(f"{green}INFO{reset}:     [{cyan}Database{reset}] RelayX Database initialized.")