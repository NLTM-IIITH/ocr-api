from datetime import datetime
from uuid import uuid4
from typing import List, Optional

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


class Log(BaseModel, DBModelMixin):
    id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    user_token: str
    created: Optional[datetime] = Field(default_factory=datetime.now)

    class Meta:
        collection_name = 'logs'

    @classmethod
    async def create(cls, token: Token):
        print('creating log for {}'.format(token.id))
        ret = cls(user_token=token.id)
        await ret.save()
        return await ret.refresh()