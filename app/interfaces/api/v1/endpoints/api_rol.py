from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from sqlalchemy.orm import Session
from app.infrastructure.db.database import get_db
from app.infrastructure.db.repositories.api_rol_repository_sql import SqlApiRolRepository
from app.interfaces.schemas.api_rol import CrearAdminRequest, ApiRolResponse
from app.interfaces.schemas.api_rol_update import ActualizarRolRequest


router = APIRouter(prefix="/api-rol", tags=["API Rol"])

@router.post("", response_model=ApiRolResponse,
    summary="Crear nuevo administrador",
    description="Registra un nuevo email como administrador en la plataforma.")
def crear_admin(
    data: CrearAdminRequest,
    db: Session = Depends(get_db)
):
    repo = SqlApiRolRepository(db)

    # Check if already exists
    existe = repo.buscar_por_email(data.email)
    if existe:
        raise HTTPException(status_code=400, detail="El email ya tiene un rol asignado")

    nuevo_admin = repo.crear(data.email, data.admin)
    return nuevo_admin

@router.get("/{email}", response_model=ApiRolResponse,
    summary="Buscar rol por email",
    description="Busca un rol de administrador por email.")
def buscar_admin_por_email(
    email: str,
    db: Session = Depends(get_db)
):
    repo = SqlApiRolRepository(db)
    admin = repo.buscar_por_email(email)
    if not admin:
        raise HTTPException(status_code=404, detail="Admin no encontrado")
    return admin

@router.get("", summary="Listar roles de administrador",
    description="Devuelve la lista de roles de administrador, con paginación y ordenación.")
def listar_admins(
    page: Optional[int] = Query(None, ge=1, description="Página actual"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Cantidad de resultados por página"),
    sort_field: Optional[str] = Query(None, description="Campo por el cual ordenar"),
    sort_direction: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Dirección de ordenación: asc o desc"),
    db: Session = Depends(get_db)
):
    repo = SqlApiRolRepository(db)
    admins = repo.listar()

    total = len(admins)

    # Aplicar ordenación si se especifica
    if sort_field and hasattr(admins[0] if admins else None, sort_field):
        reverse = sort_direction == "desc"

        def sort_key(admin):
            value = getattr(admin, sort_field, None)
            if value is None:
                return ""
            return str(value).lower()

        admins.sort(key=sort_key, reverse=reverse)

    # Aplicar paginación
    if page is not None and limit is not None:
        start = (page - 1) * limit
        end = start + limit
        admins = admins[start:end]

    return {
        "total": total,
        "admins": admins
    }

@router.put("/{id}", response_model=ApiRolResponse, tags=["API Rol"],
    summary="Actualizar rol de administrador",
    description="Actualiza el estado de administrador para un email específico.")
def actualizar_admin(
    data: ActualizarRolRequest,
    id: int,
    db: Session = Depends(get_db)
):
    repo = SqlApiRolRepository(db)
    actualizado = repo.actualizar(id, data.admin)

    if not actualizado:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return actualizado
