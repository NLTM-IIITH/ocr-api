from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field

from .mixins import DBModelMixin


class Log(BaseModel, DBModelMixin):
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_token: str | None = Field('')
    language: str | None = Field('')
    modality: str | None = Field('printed')
    version: str
    image_count: int | None = Field(0)
    created: datetime | None = Field(default_factory=datetime.now)

    class Meta:
        collection_name = 'logs'


class Model(BaseModel, DBModelMixin):
    id: str = Field(default_factory=lambda: str(uuid4()))
    language: str
    modality: str
    version: str
    created: datetime | None = Field(default_factory=datetime.now)

    class Meta:
        collection_name = 'models'