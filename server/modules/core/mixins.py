from datetime import datetime

from server.database import get_db


class DBModelMixin:

    @classmethod
    async def all(cls) -> list:
        ret = get_db()[cls.Meta.collection_name].find()
        return [cls(**i) async for i in ret]

    @classmethod
    async def get(cls, id):
        try:
            ret = await get_db()[cls.Meta.collection_name].find_one({'id': id})
            return cls(**ret)
        except Exception:
            return None

    @classmethod
    async def filter(cls, **kwargs) -> list:
        if not kwargs:
            return await cls.all()
        ret = get_db()[cls.Meta.collection_name].find(kwargs)
        return [cls(**i) async for i in ret]

    async def save(self):
        await get_db()[self.Meta.collection_name].insert_one(self.dict())

    async def update(self, **kwargs):
        kwargs.update({'modified': datetime.now()})
        await get_db()[self.Meta.collection_name].update_one(
            {'id': self.id},
            {'$set': kwargs},
        )

    async def refresh(self):
        return await self.__class__.get(self.id)

    async def delete(self) -> None:
        await get_db()[self.Meta.collection_name].delete_one({'id': self.id})
