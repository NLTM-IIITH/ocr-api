from datetime import datetime
from typing import Optional
from uuid import uuid4

from passlib.context import CryptContext
from pydantic import BaseModel, Field

from server.database import get_db


class AuthToken(BaseModel):
    access_token: str
    token_type: str

class UserOut(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    username: str
    name: Optional[str] = ''
    mobile: Optional[str] = ''
    email: Optional[str] = ''
    active: Optional[bool] = True
    superuser: Optional[bool] = False
    created: Optional[datetime] = Field(default_factory=datetime.now)
    modified: Optional[datetime] = Field(default_factory=datetime.now)

class UserUpdate(BaseModel):
    name: Optional[str] = ''
    mobile: Optional[str] = ''
    email: Optional[str] = ''

class UserIn(BaseModel):
    username: str
    password: str
    name: Optional[str] = ''
    mobile: Optional[str] = ''
    email: Optional[str] = ''


class User(UserOut):
    # this stores the hashed password
    password: str

    @staticmethod
    async def get(id: str):
        ret = await get_db()['users'].find_one({'id': id})
        return User(**ret)

    @staticmethod
    async def all():
        ret = get_db()['users'].find()
        return [User(**i) async for i in ret]

    @staticmethod
    async def filter(**kwargs) -> list:
        if not kwargs:
            return await User.all()
        ret = get_db()['users'].find(kwargs)
        return [User(**i) async for i in ret]

    @staticmethod
    async def create(user: UserIn):
        userdict = user.dict().copy()
        # TODO: check if the username already exists
        userdict['password'] = CryptContext(
            schemes=['bcrypt'],
            deprecated='auto',
        ).hash(userdict['password'])
        ret = User(
            **userdict,
        )
        await ret.save()
        return ret

    @staticmethod
    async def login(username: str, password: str):
        user = await User.filter(username=username)
        if not user:
            return False
        if len(user) != 1:
            return False
        user = user[0]
        if not await user.authenticate(password):
            return False
        return user

    async def save(self):
        await get_db()['users'].insert_one(self.dict())

    async def refresh(self):
        return await User.get(self.id)

    async def update(self, **kwargs):
        kwargs.update({'modified': datetime.now()})
        await get_db()['users'].update_one(
            {'id': self.id},
            {'$set': kwargs},
        )

    async def delete(self) -> None:
        await get_db()['users'].delete_one({'id': self.id})

    async def authenticate(self, password):
        return CryptContext(
            schemes=['bcrypt'],
            deprecated='auto',
        ).verify(password, self.password)
