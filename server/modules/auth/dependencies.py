from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from server.config import AUTH_ALGORITHM, AUTH_SECRET_KEY

from .models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/login')

async def get_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, AUTH_SECRET_KEY, algorithms=[AUTH_ALGORITHM])
        username: str = payload.get("username")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await User.filter(username=username)
    if user is None or len(user) != 1:
        raise credentials_exception
    return user[0]


async def get_active_user(user: User = Depends(get_user)):
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User Inactive. Please contact admin",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_superuser(user: User = Depends(get_user)):
    if not user.superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Endpoint only accessible to admins",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
