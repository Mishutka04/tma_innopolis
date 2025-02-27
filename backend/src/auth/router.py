from fastapi import APIRouter, HTTPException, status, Response
from fastapi.responses import JSONResponse

from src.auth.auth import authenticate_user, create_access_token, get_password_hash, verify_password
from src.auth.schemas import SUserAuth
from src.auth.service import UserService

router = APIRouter()

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user_data: SUserAuth) -> JSONResponse:
    existing_user = await UserService.find_one_or_none(email=user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует"
        )
    
    hashed_password = await get_password_hash(user_data.password)
    user = await UserService.add(
        email=user_data.email,
        hashed_password=hashed_password
    )
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": "Пользователь успешно зарегистрирован"}
    )
    
@router.post("/login", status_code=status.HTTP_200_OK)
async def login_user(response: Response, user_data: SUserAuth) -> dict:
    user = await authenticate_user(user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )
    
    access_token = await create_access_token({"sub": str(user.id)})
    response.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        secure=True,  # Только для HTTPS
        samesite="lax"  # Защита от CSRF
    )
    
    return {"access_token": access_token}