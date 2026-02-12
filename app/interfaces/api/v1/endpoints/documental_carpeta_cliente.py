from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from app.infrastructure.db.database import SessionLocal
from app.infrastructure.db.repositories.documental_carpeta_cliente_repository_sql import DocumentalCarpetaClienteRepositorySQL
from app.interfaces.schemas.documental_carpeta_cliente import (
    DocumentalCarpetaClienteCreate,
    DocumentalCarpetaClienteRead,
    DocumentalCarpetaClienteUpdate
)
from app.domain.entities.documental_carpeta_cliente import DocumentalCarpetaCliente

router = APIRouter(prefix="/documental-carpeta-cliente", tags=["Documental Carpeta Cliente"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_repo(db: Session = Depends(get_db)):
    return DocumentalCarpetaClienteRepositorySQL(db)

@router.get("", summary="Listar todas las carpetas de cliente",
    description="Devuelve todas las carpetas de cliente registradas en el sistema.")
def get_all(
    page: Optional[int] = Query(None, ge=1, description="Página actual"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Cantidad de resultados por página (máximo 10000)"),
    sort_field: Optional[str] = Query(None, description="Campo por el cual ordenar"),
    sort_direction: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Dirección de ordenación: asc o desc"),
    repo: DocumentalCarpetaClienteRepositorySQL = Depends(get_repo)
):
    carpetas = repo.get_all()
    total = len(carpetas)

    # Aplicar ordenación si se especifica
    if sort_field and carpetas and hasattr(carpetas[0], sort_field):
        reverse = sort_direction == "desc"

        def sort_key(item):
            value = getattr(item, sort_field, None)
            if value is None:
                return ""
            if sort_field == "id":
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return 0
            return str(value).lower() if isinstance(value, str) else str(value)

        carpetas.sort(key=sort_key, reverse=reverse)

    # Aplicar paginación después de ordenar
    if page is not None and limit is not None:
        start = (page - 1) * limit
        end = start + limit
        carpetas = carpetas[start:end]

    return {
        "total": total,
        "carpetas": carpetas
    }

@router.get("/{id}", summary="Obtener carpeta de cliente por ID",
    description="Devuelve una carpeta de cliente específica según su ID.")
def get_by_id(
    id: int = Path(..., description="ID de la carpeta a consultar"),
    repo: DocumentalCarpetaClienteRepositorySQL = Depends(get_repo)
):
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Carpeta Cliente no encontrada")
    return entity

@router.get("/cliente/{cliente_id}", summary="Obtener carpetas por cliente",
    description="Devuelve todas las carpetas asociadas a un cliente específico.")
def get_by_cliente(
    cliente_id: str = Path(..., description="ID del cliente a consultar"),
    page: Optional[int] = Query(None, ge=1, description="Página actual"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Cantidad de resultados por página (máximo 10000)"),
    sort_field: Optional[str] = Query(None, description="Campo por el cual ordenar"),
    sort_direction: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Dirección de ordenación: asc o desc"),
    repo: DocumentalCarpetaClienteRepositorySQL = Depends(get_repo)
):
    carpetas = repo.get_by_cliente_id(cliente_id)
    total = len(carpetas)

    # Aplicar ordenación si se especifica
    if sort_field and carpetas and hasattr(carpetas[0], sort_field):
        reverse = sort_direction == "desc"

        def sort_key(item):
            value = getattr(item, sort_field, None)
            if value is None:
                return ""
            if sort_field == "id":
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return 0
            return str(value).lower() if isinstance(value, str) else str(value)

        carpetas.sort(key=sort_key, reverse=reverse)

    # Aplicar paginación después de ordenar
    if page is not None and limit is not None:
        start = (page - 1) * limit
        end = start + limit
        carpetas = carpetas[start:end]

    return {
        "total": total,
        "carpetas": carpetas
    }

@router.post("", summary="Crear carpeta de cliente",
    description="Crea una nueva relación de carpeta con un cliente.")
def create(
    payload: DocumentalCarpetaClienteCreate,
    repo: DocumentalCarpetaClienteRepositorySQL = Depends(get_repo)
):
    entity = DocumentalCarpetaCliente(
        id=0,
        cliente_id=payload.cliente_id,
        proceso_id=payload.proceso_id,
        carpeta_id=payload.carpeta_id
    )
    return repo.create(entity)

@router.put("/{id}", summary="Actualizar carpeta de cliente",
    description="Actualiza una carpeta de cliente existente por su ID.")
def update(
    id: int = Path(..., description="ID de la carpeta a actualizar"),
    payload: DocumentalCarpetaClienteUpdate = None,
    repo: DocumentalCarpetaClienteRepositorySQL = Depends(get_repo)
):
    current = repo.get_by_id(id)
    if not current:
        raise HTTPException(status_code=404, detail="Carpeta Cliente no encontrada")
    updated = repo.update(id, current)
    return updated

@router.delete("/{id}", summary="Eliminar carpeta de cliente",
    description="Elimina una carpeta de cliente existente por su ID.")
def delete(
    id: int = Path(..., description="ID de la carpeta a eliminar"),
    repo: DocumentalCarpetaClienteRepositorySQL = Depends(get_repo)
):
    success = repo.delete(id)
    if not success:
        raise HTTPException(status_code=404, detail="Carpeta Cliente no encontrada")
    return {"mensaje": "Carpeta Cliente eliminada"}
