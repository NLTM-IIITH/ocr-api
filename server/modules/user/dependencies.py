from fastapi import HTTPException, Form
from .models import Token

async def get_token(token: str = Form(...)) -> Token:
    token = await Token.get(id=token)
    if token is None:
        raise HTTPException(status_code=403, detail='No such token present')
    return token