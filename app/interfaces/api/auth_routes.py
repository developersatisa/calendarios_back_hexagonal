from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import timedelta
from jose import JWTError, jwt

from app.infrastructure.db.database import SessionLocal
from app.infrastructure.db.repositories.sql_api_cliente_repository import SqlApiClienteRepository
from app.infrastructure.db.repositories.api_rol_repository_sql import SqlApiRolRepository
from app.interfaces.api.security.auth import create_access_token, verify_password,create_refresh_token
from app.config import settings
from app.interfaces.schemas.token import RefreshTokenRequest, TokenResponse
from app.infrastructure.services.sso_service import SSOService



router = APIRouter()

# Dependency para obtener sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/token", summary="Login de cliente API y emisión de JWT")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    repo = SqlApiClienteRepository(db)
    cliente = repo.get_by_nombre(form_data.username)

    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Usuario '{form_data.username}' no encontrado en la base de datos"
        )

    if not cliente.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Usuario '{form_data.username}' está inactivo. Contacte al administrador."
        )

    if not verify_password(form_data.password, cliente.hashed_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Clave incorrecta")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": cliente.nombre_cliente,
            "id_api_cliente": cliente.id,
            "atisa": False
        },
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": cliente.nombre_cliente})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh-token", response_model=TokenResponse)
def refresh_token_view(data: RefreshTokenRequest):
    try:
        payload = jwt.decode(data.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Token inválido")

        # Preservar la información original del token
        token_data = {
            "sub": username,
            "username": payload.get("username", username),
            "email": payload.get("email"),
            "id_api_rol": payload.get("id_api_rol"),
            "atisa": payload.get("atisa", False),
            "rol": payload.get("rol"),
            "codSubDepar": payload.get("codSubDepar")
        }

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = create_access_token(data=token_data, expires_delta=access_token_expires)

        # Generar un nuevo refresh token también, para rotación (opcional pero recomendado)
        new_refresh_token = create_refresh_token(data=token_data)

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "user_info": {
                "username": token_data["username"],
                "email": token_data["email"],
                "id_api_rol": token_data["id_api_rol"],
                "atisa": token_data["atisa"],
                "rol": token_data["rol"],
                "codSubDepar": token_data["codSubDepar"]
            }
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh token inválido o caducado")


@router.get("/sso/login", summary="Inicia el proceso de Single Sign-On")
def sso_login():
    """
    Inicia el proceso de autenticación SSO con Microsoft Azure AD.

    Este endpoint genera una URL de autorización de Azure AD que debe ser usada
    para redirigir al usuario al portal de autenticación de Microsoft.

    **Flujo:**
    1. El cliente llama a este endpoint
    2. El backend genera una URL de autorización de Azure AD
    3. El cliente redirige al usuario a esa URL
    4. El usuario se autentica en Azure AD
    5. Azure AD redirige al usuario a `/sso/callback` con un código

    **Returns:**
        - `auth_url`: URL completa de Azure AD donde el usuario debe autenticarse
        - `message`: Mensaje descriptivo

    **Raises:**
        - `503 Service Unavailable`: Si SSO no está configurado correctamente

    **Example Response:**
    ```json
    {
        "auth_url": "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize?...",
        "message": "Redirige al usuario a esta URL para completar la autenticación"
    }
    ```
    """
    try:
        sso_service = SSOService()
        auth_url = sso_service.get_auth_url()

        return {
            "auth_url": auth_url,
            "message": "Redirige al usuario a esta URL para completar la autenticación"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"SSO no disponible: {str(e)}"
        )


@router.get("/sso/callback", summary="Callback del SSO que devuelve el JWT")
def sso_callback(
    code: str = Query(..., description="Código de autorización de Azure AD (proporcionado por Azure después de la autenticación)"),
    db: Session = Depends(get_db)
):
    """
    Endpoint de callback para completar la autenticación SSO.

    Este endpoint es llamado automáticamente por Azure AD después de que el usuario
    se autentica exitosamente. Azure AD redirige al usuario aquí con un código de
    autorización que se intercambia por tokens.

    **Flujo:**
    1. Azure AD redirige al usuario aquí con `?code=xxx`
    2. El backend intercambia el código por un token de acceso de Azure AD
    3. El backend usa el token para obtener información del usuario desde Microsoft Graph
    4. El backend valida que el usuario esté autorizado (dominio @atisa.es o @atisa-grupo.com)
    5. El backend genera tokens JWT propios de la aplicación
    6. Se devuelven los tokens JWT al cliente

    **Query Parameters:**
        - `code` (required): Código de autorización de Azure AD. Válido por ~10 minutos, un solo uso.

    **Returns:**
        - `access_token`: Token JWT para autenticar peticiones a la API
        - `refresh_token`: Token JWT para renovar el access_token sin re-autenticación
        - `token_type`: Tipo de token (siempre "bearer")
        - `user_info`: Información del usuario autenticado

    **Raises:**
        - `400 Bad Request`: Si hay error al obtener el token o información del usuario
        - `403 Forbidden`: Si el usuario no está autorizado (dominio no permitido)
        - `503 Service Unavailable`: Si SSO no está configurado correctamente

    **Example Response:**
    ```json
    {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "token_type": "bearer",
        "user_info": {
            "username": "Juan Pérez",
            "email": "juan.perez@atisa.es",
            "id_api_cliente": 1,
            "atisa": true,
            "rol": "admin"
        }
    }
    ```

    **Notas:**
    - El código de autorización solo puede usarse una vez
    - El código expira después de ~10 minutos
    - Solo usuarios con dominios @atisa.es o @atisa-grupo.com están autorizados
    """
    try:
        sso_service = SSOService()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"SSO no disponible: {str(e)}"
        )



    # Intercambia el código por un token
    token_result = sso_service.get_token_from_code(code)
    if not token_result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al obtener token de acceso"
        )

    # Obtiene información del usuario
    user_info = sso_service.get_user_info(token_result["access_token"])
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al obtener información del usuario"
        )

    # Extrae datos del usuario
    username = user_info.get("displayName", "")
    email = user_info.get("mail") or user_info.get("userPrincipalName", "")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo obtener el email del usuario"
        )

    # Obtiene el rol y id_api_rol basado en el email
    repo_rol = SqlApiRolRepository(db)
    api_rol = repo_rol.buscar_por_email(email)

    # Determinar rol segun si existe mapping
    rol = "admin" if (api_rol and api_rol.admin) else "user"
    id_api_rol = api_rol.id if api_rol else None

    # Obtener CECO
    codSubDepar = None
    try:
        # Se ha removido el campo nombre de la consulta y del token
        query_codSubDepar = text("""
            SELECT sd.codSubDepar
            FROM [ATISA_Input].dbo.clientes c
            JOIN [ATISA_Input].dbo.clienteSubDepar csd ON c.CIF = csd.cif
            JOIN [ATISA_Input].dbo.SubDepar sd ON sd.codSubDepar = csd.codSubDepar
            JOIN [BI DW RRHH DEV].dbo.HDW_Cecos cc
                ON SUBSTRING(CAST(cc.CODIDEPAR AS VARCHAR), 24, 6) = RIGHT('000000' + CAST(sd.codSubDepar AS VARCHAR), 6)
                AND cc.fechafin IS NULL
            JOIN [BI DW RRHH DEV].dbo.Persona per ON per.Numeross = cc.Numeross
            WHERE per.email = :email
        """)
        result = db.execute(query_codSubDepar, {"email": email}).first()
        if result:
            codSubDepar = result.codSubDepar
    except Exception as e:
        # Si falla la consulta de ceco, no bloqueamos el login
        print(f"Error obteniendo codSubDepar para {email}: {e}")

    # Crea el JWT con la información requerida
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {
        "sub": username,
        "username": username,
        "email": email,  # Email del usuario autenticado
        "id_api_rol": id_api_rol,
        "atisa": True,
        "rol": rol,
        "codSubDepar": codSubDepar
    }

    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )

    # Crea también un refresh token
    refresh_token = create_refresh_token(data=token_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_info": {
            "username": username,
            "email": email,
            "id_api_rol": id_api_rol,
            "atisa": True,
            "rol": rol,
            "codSubDepar": codSubDepar
        }
    }
