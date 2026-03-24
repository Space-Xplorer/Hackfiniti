from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db


async def get_database_session(db: AsyncSession = Depends(get_db)) -> AsyncSession:
    return db
