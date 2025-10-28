from datetime import datetime, timedelta
from typing import Optional
import jwt
from jwt.exceptions import PyJWTError as JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models.models import User
from database.connection import get_users_collection
from bson import ObjectId
import os

# Configuración de encriptación
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
security = HTTPBearer()

SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_key_for_development")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar contraseña"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Encriptar contraseña"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crear token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_user_by_email(email: str) -> Optional[User]:
    """Obtener usuario por email"""
    collection = await get_users_collection()
    user_data = await collection.find_one({"email": email})
    if user_data:
        return User(**user_data)
    return None

async def get_user_by_username(username: str) -> Optional[User]:
    """Obtener usuario por nombre de usuario"""
    collection = await get_users_collection()
    user_data = await collection.find_one({"username": username})
    if user_data:
        return User(**user_data)
    return None

async def get_user_by_id(user_id: str) -> Optional[User]:
    """Obtener usuario por ID"""
    try:
        collection = await get_users_collection()
        user_data = await collection.find_one({"_id": ObjectId(user_id)})
        if user_data:
            return User(**user_data)
        return None
    except:
        return None

async def authenticate_user(username_or_email: str, password: str) -> Optional[User]:
    """Autenticar usuario por email o username"""
    # Intentar primero con email
    user = await get_user_by_email(username_or_email)

    # Si no se encuentra por email, intentar con username
    if not user:
        user = await get_user_by_username(username_or_email)

    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Obtener usuario actual del token JWT"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    return user