from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from sqlalchemy import select
from src.database import get_db
from src.database.models import Base, CountryModel


async def get_or_create(model: Base, raw_data: str, db: AsyncSession):
    column = model.code if model == CountryModel else model.name
    response = await db.execute(select(model).where(column == raw_data))
    instance = response.scalar_one_or_none()
    if instance:
        return instance
    if model == CountryModel:
        instance = model(code=raw_data)
    else:
        instance = model(name=raw_data)
    db.add(instance)
    await db.commit()
    await db.refresh(instance)
    return instance
