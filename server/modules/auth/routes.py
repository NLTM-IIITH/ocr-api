from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt

from server.config import AUTH_ALGORITHM, AUTH_SECRET_KEY

from .dependencies import get_active_user, get_superuser
from .models import AuthToken, User, UserIn, UserOut, UserUpdate

router = APIRouter(
    prefix='/ocr/auth',
    tags=['Auth'],
)

@router.post("/login", response_model=AuthToken)
async def login_for_access_token(data: OAuth2PasswordRequestForm = Depends()):

    def create_access_token(data: dict):
        to_encode = data.copy()
        encoded_jwt = jwt.encode(to_encode, AUTH_SECRET_KEY, algorithm=AUTH_ALGORITHM)
        return encoded_jwt

    user = await User.login(data.username, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"username": user.username}
    )
    return {"access_token": access_token, "token_type": "Bearer"}


async def get_user_by_id(id: str) -> User:
    return await User.get(id)


@router.get('/all', response_model=list[UserOut])
async def get_all_users(superuser: User = Depends(get_superuser)):
    return await User.all()

@router.get("/me", response_model=UserOut)
async def get_my_user_details(user: User = Depends(get_active_user)):
    return user

@router.patch("/me", response_model=UserOut)
async def update_my_user_details(
    data: UserUpdate = Body(...),
    user: User = Depends(get_active_user)
):
    data = data.dict()
    # ignore the empty data keys
    data = {i:data[i] for i in data if data[i]}
    await user.update(**data)
    return await user.refresh()


@router.post('/register', response_model=UserOut)
async def register_new_user(
    data: UserIn = Body(...),
    superuser: User = Depends(get_superuser)
):
    return await User.create(data)


@router.get('/{id}', response_model=UserOut)
async def get_user_details(
    user: User = Depends(get_user_by_id),
    superuser: User = Depends(get_superuser),
):
    return user


@router.patch("/{id}", response_model=UserOut)
async def update_user_details(
    user: User = Depends(get_user_by_id),
    data: UserUpdate = Body(...),
    superuser: User = Depends(get_superuser),
):
    data = data.dict()
    # ignore the empty data keys
    data = {i:data[i] for i in data if data[i]}
    await user.update(**data)
    return await user.refresh()


@router.delete('/{id}')
async def delete_user(
    user: User = Depends(get_user_by_id),
    superuser: User = Depends(get_superuser),
):
    await user.delete()
    return {'detail': '1 User deleted'}

