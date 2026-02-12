from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from datetime import datetime
from sqlalchemy.orm import Session
from app.infrastructure.db.database import SessionLocal
from app.infrastructure.db.repositories.documental_carpeta_proceso_repository_sql import DocumentalCarpetaProcesoRepositorySQL
from app.interfaces.schemas.documental_carpeta_proceso import (
    DocumentalCarpetaProcesoCreate,
    DocumentalCarpetaProcesoUpdate
)
from app.domain.entities.documental_carpeta_proceso import DocumentalCarpetaProceso

router = APIRouter(prefix="/documental-carpeta-proceso", tags=["Documental Carpeta Proceso"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_repo(db: Session = Depends(get_db)):
    return DocumentalCarpetaProcesoRepositorySQL(db)

@router.get("", summary="Listar todas las carpetas de proceso",
    description="Devuelve todas las carpetas de proceso registradas en el sistema.")
def get_all(
    page: Optional[int] = Query(None, ge=1, description="Página actual"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Cantidad de resultados por página (máximo 10000)"),
    sort_field: Optional[str] = Query(None, description="Campo por el cual ordenar"),
    sort_direction: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Dirección de ordenación: asc o desc"),
    repo: DocumentalCarpetaProcesoRepositorySQL = Depends(get_repo)
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
            elif sort_field in ["fecha_creacion", "fecha_actualizacion"]:
                if hasattr(value, 'timestamp'):
                    return value.timestamp()
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

@router.get("/{id}", summary="Obtener carpeta de proceso por ID",
    description="Devuelve una carpeta de proceso específica según su ID.")
def get_by_id(
    id: int = Path(..., description="ID de la carpeta a consultar"),
    repo: DocumentalCarpetaProcesoRepositorySQL = Depends(get_repo)
):
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Carpeta Proceso no encontrada")
    return entity

@router.get("/proceso/{proceso_id}", summary="Obtener carpetas por proceso",
    description="Devuelve todas las carpetas asociadas a un proceso específico.")
def get_by_proceso(
    proceso_id: int = Path(..., description="ID del proceso a consultar"),
    page: Optional[int] = Query(None, ge=1, description="Página actual"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Cantidad de resultados por página (máximo 10000)"),
    sort_field: Optional[str] = Query(None, description="Campo por el cual ordenar"),
    sort_direction: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Dirección de ordenación: asc o desc"),
    repo: DocumentalCarpetaProcesoRepositorySQL = Depends(get_repo)
):
    carpetas = repo.get_by_proceso_id(proceso_id)
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
            elif sort_field in ["fecha_creacion", "fecha_actualizacion"]:
                if hasattr(value, 'timestamp'):
                    return value.timestamp()
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

@router.post("", summary="Crear carpeta de proceso",
    description="Crea una nueva carpeta asociada a un proceso.")
def create(
    payload: DocumentalCarpetaProcesoCreate,
    repo: DocumentalCarpetaProcesoRepositorySQL = Depends(get_repo)
):
    entity = DocumentalCarpetaProceso(
        id=0,
        proceso_id=payload.proceso_id,
        nombre=payload.nombre,
        descripcion=payload.descripcion,
        eliminado=False,
        fecha_creacion=datetime.now(),
        fecha_actualizacion=datetime.now()
    )
    return repo.create(entity)

@router.put("/{id}", summary="Actualizar carpeta de proceso",
    description="Actualiza una carpeta de proceso existente por su ID.")
def update(
    id: int = Path(..., description="ID de la carpeta a actualizar"),
    payload: DocumentalCarpetaProcesoUpdate = None,
    repo: DocumentalCarpetaProcesoRepositorySQL = Depends(get_repo)
):
    current = repo.get_by_id(id)
    if not current:
        raise HTTPException(status_code=404, detail="Carpeta Proceso no encontrada")

    if payload.nombre is not None:
        current.nombre = payload.nombre
    if payload.descripcion is not None:
        current.descripcion = payload.descripcion

    updated = repo.update(id, current)
    return updated

@router.delete("/{id}", summary="Eliminar carpeta de proceso",
    description="Elimina una carpeta de proceso existente por su ID.")
def delete(
    id: int = Path(..., description="ID de la carpeta a eliminar"),
    repo: DocumentalCarpetaProcesoRepositorySQL = Depends(get_repo)
):
    success = repo.delete(id)
    if not success:
        raise HTTPException(status_code=404, detail="Carpeta Proceso no encontrada")
    return {"mensaje": "Carpeta Proceso eliminada"}
