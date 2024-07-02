from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from ..core.mixins import DBModelMixin



class Token(BaseModel, DBModelMixin):
    id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    email: str
    purpose: str
    quota: Optional[int] = Field(1000)
    created: Optional[datetime] = Field(default_factory=datetime.now)
    modified: Optional[datetime] = Field(default_factory=datetime.now)

    class Meta:
        collection_name = 'tokens'

    @classmethod
    async def create(cls, token_input):
        ret = cls(**token_input)
        await ret.save()
        return await ret.refresh()
