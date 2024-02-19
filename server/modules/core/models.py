from datetime import datetime
from uuid import uuid4
from typing import List, Optional

from pydantic import BaseModel, Field

from .mixins import DBModelMixin

class Log(BaseModel, DBModelMixin):
    id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    user_token: Optional[str] = Field('')
    language: Optional[str] = Field('')
    modality: Optional[str] = Field('printed')
    version: str
    image_count: Optional[int] = Field(0)
    created: Optional[datetime] = Field(default_factory=datetime.now)

    class Meta:
        collection_name = 'logs'

    @classmethod
    async def create(cls, **kwargs):
        ret = cls(**kwargs)
        await ret.save()
        return await ret.refresh()