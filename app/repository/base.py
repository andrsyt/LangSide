from typing import Any, Generic, Sequence, Type, TypeVar

from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

# Generic types for model, create schema, and update schema
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, db: AsyncSession, model: Type[ModelType]):
        self.db = db
        self.model = model

    async def get(self, obj_id: Any) -> ModelType | None:
        query = select(self.model).where(self.model.id == obj_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(self, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
        query = select(self.model).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, obj_in: CreateSchemaType | dict[str, Any]) -> ModelType:
        if isinstance(obj_in, dict):
            obj_data = obj_in
        else:
            obj_data = obj_in.model_dump()

        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        # Do not commit here — the service owns the transaction
        return db_obj

    async def update(self, db_obj: ModelType, obj_in: UpdateSchemaType | dict[str, Any]) -> ModelType:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
            
        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])
        
        self.db.add(db_obj)
        return db_obj

    async def remove(self, obj_id: Any) -> ModelType:
        query = delete(self.model).where(self.model.id == obj_id).returning(self.model)
        result = await self.db.execute(query)
        return result.scalar_one()