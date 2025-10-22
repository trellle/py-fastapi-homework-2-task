from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from sqlalchemy import select, and_
from src.database.session_postgresql import get_postgresql_db
from src.database.models import Base


async def get_or_create(model: Base, raw_data: dict, db: AsyncSession = Depends(get_postgresql_db)):
    conditions = [getattr(model, key) == value for key, value in raw_data.items()]
    response = await db.execute(select(model).where(and_(*conditions)))
    instance = response.scalar_one_or_none()
    if instance:
        return instance
    instance = model(**raw_data)
    db.add(instance)
    await db.commit()
    await db.refresh(instance)
    return instance
