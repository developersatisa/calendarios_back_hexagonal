from datetime import datetime, timedelta
from typing import Optional, Dict, List
import re

from jose import JWTError, jwt
from passlib.context import CryptContext
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.config import settings

SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
ALGORITHM = settings.ALGORITHM

# Donde esperamos el token (en los headers)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Contexto de hash de bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Hashing de contraseña
def hash_password(password: str) -> str:
    # Bcrypt tiene un límite de 72 bytes, truncamos si es necesario
    password_bytes = password.encode('utf-8')[:72]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')


# Verificación de contraseña
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        # Bcrypt tiene un límite de 72 bytes, truncamos si es necesario
        plain_password_bytes = plain_password.encode('utf-8')[:72]
        hashed_password_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)
    except (ValueError, TypeError):
        return False


# Crear token JWT
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Dependencia para obtener usuario autenticado (desde el token)
def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return {
                "username": payload.get("username", username),  # Prioriza el username explícito del SSO
                "email": payload.get("email"),
                "id_api_rol": payload.get("id_api_rol"),
                "atisa": payload.get("atisa", False),
                "rol": payload.get("rol"),
                "codSubDepar": payload.get("codSubDepar")
            }
    except JWTError:
        raise credentials_exception

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=1))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def validar_password_criterios(password: str) -> Dict[str, any]:
    """
    Valida una contraseña según criterios de seguridad.

    Criterios:
    - Mínimo 8 caracteres
    - Al menos una letra minúscula
    - Al menos una letra mayúscula
    - Al menos un número
    - Al menos un carácter especial

    Returns:
        Dict con 'valida' (bool) y 'errores' (List[str])
    """
    errores = []

    if len(password) < 8:
        errores.append("La contraseña debe tener al menos 8 caracteres")

    if not re.search(r'[a-z]', password):
        errores.append("La contraseña debe contener al menos una letra minúscula")

    if not re.search(r'[A-Z]', password):
        errores.append("La contraseña debe contener al menos una letra mayúscula")

    if not re.search(r'\d', password):
        errores.append("La contraseña debe contener al menos un número")

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errores.append("La contraseña debe contener al menos un carácter especial (!@#$%^&*(),.?\":{}|<>)")

    return {
        "valida": len(errores) == 0,
        "errores": errores
    }
