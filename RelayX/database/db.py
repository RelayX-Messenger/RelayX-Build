import os

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from RelayX.utils.paths import db_filepath

os.makedirs(os.path.dirname(db_filepath), exist_ok=True)

DATABASE_URL = f"sqlite+aiosqlite:///{db_filepath}"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()