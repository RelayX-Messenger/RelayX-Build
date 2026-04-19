import os

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

db_path = os.path.join(os.getenv("LOCALAPPDATA"), "RelayX")
os.makedirs(db_path, exist_ok=True)
db_filepath = os.path.join(db_path, "RelayX.db")

DATABASE_URL = f"sqlite+aiosqlite:///{db_filepath}"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()