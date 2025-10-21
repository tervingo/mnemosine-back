from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from models.models import User, UserCreate, UserResponse
from auth.auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_user_by_email,
    get_user_by_username,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from database.connection import get_users_collection
from datetime import datetime

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate):
    """Registrar nuevo usuario"""
    # Verificar si el email ya existe
    existing_user = await get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )

    # Verificar si el username ya existe
    existing_username = await get_user_by_username(user.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está en uso"
        )

    # Crear nuevo usuario
    hashed_password = get_password_hash(user.password)
    new_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )

    collection = await get_users_collection()
    result = await collection.insert_one(new_user.dict(by_alias=True, exclude={"id"}))

    # Crear armario por defecto
    from routers.armarios import create_default_armario
    await create_default_armario(str(result.inserted_id))

    return UserResponse(
        id=str(result.inserted_id),
        email=new_user.email,
        username=new_user.username,
        created_at=new_user.created_at
    )

@router.post("/login")
async def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    """Iniciar sesión"""
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario/email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            created_at=user.created_at
        )
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Obtener información del usuario actual"""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        created_at=current_user.created_at
    )