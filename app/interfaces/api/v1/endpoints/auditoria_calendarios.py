from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from app.infrastructure.db.database import SessionLocal
from app.infrastructure.db.repositories.auditoria_calendarios_repository_sql import AuditoriaCalendariosRepositorySQL
from app.interfaces.schemas.auditoria_calendarios import (
    AuditoriaCalendariosCreate,
    AuditoriaCalendariosUpdate,
    AuditoriaCalendariosResponse
)
from app.domain.entities.auditoria_calendarios import AuditoriaCalendarios

router = APIRouter(prefix="/auditoria-calendarios", tags=["AuditoriaCalendarios"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_repo(db: Session = Depends(get_db)):
    return AuditoriaCalendariosRepositorySQL(db)


def _sort_and_paginate(items: list, sort_field, sort_direction, page, limit):
    """Ordena y pagina una lista de dicts."""
    total = len(items)
    if sort_field and items and sort_field in items[0]:
        reverse = sort_direction == "desc"

        def sort_key(a):
            value = a.get(sort_field)
            if sort_field in ["id", "hito_id"]:
                try:
                    return int(value) if value is not None else (-1 if not reverse else float('inf'))
                except (ValueError, TypeError):
                    return -1 if not reverse else float('inf')
            elif sort_field in ["fecha_modificacion", "created_at", "updated_at"]:
                if value is None:
                    return -1 if not reverse else float('inf')
                return value.timestamp() if hasattr(value, 'timestamp') else (-1 if not reverse else float('inf'))
            else:
                return str(value).lower() if value is not None else ""

        items.sort(key=sort_key, reverse=reverse)

    if page is not None and limit is not None:
        start = (page - 1) * limit
        items = items[start:start + limit]

    return total, items


@router.post("",
             summary="Crear registro de auditoría",
             description="Crea un nuevo registro de auditoría de calendario")
def crear(data: AuditoriaCalendariosCreate, repo=Depends(get_repo)):
    try:
        auditoria = AuditoriaCalendarios(
            cliente_id=data.cliente_id,
            hito_id=data.hito_id,
            campo_modificado=data.campo_modificado,
            valor_anterior=data.valor_anterior or "",
            valor_nuevo=data.valor_nuevo or "",
            observaciones=data.observaciones,
            motivo=data.motivo,
            usuario=data.usuario,
            codSubDepar=data.codSubDepar,
            fecha_modificacion=datetime.utcnow(),
        )
        resultado = repo.guardar(auditoria)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear registro de auditoría: {str(e)}")


@router.get("",
            summary="Listar registros de auditoría",
            description="Devuelve todos los registros de auditoría enriquecidos con hito, proceso, departamento, tipo y momento del cambio.")
def listar(
    page: Optional[int] = Query(None, ge=1, description="Página actual"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Resultados por página"),
    sort_field: Optional[str] = Query(None, description="Campo por el cual ordenar"),
    sort_direction: Optional[str] = Query("desc", regex="^(asc|desc)$", description="asc o desc"),
    repo=Depends(get_repo)
):
    try:
        auditorias = repo.listar()
        total, auditorias = _sort_and_paginate(auditorias, sort_field, sort_direction, page, limit)
        return {"total": total, "auditoria_calendarios": auditorias}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar auditorias: {str(e)}")


@router.get("/cliente/{cliente_id}",
            summary="Obtener auditoría de un cliente",
            description="Devuelve todos los registros de auditoría de un cliente con información completa.")
def obtener_por_cliente(
    cliente_id: str = Path(..., description="ID del cliente"),
    page: Optional[int] = Query(None, ge=1),
    limit: Optional[int] = Query(None, ge=1, le=10000),
    sort_field: Optional[str] = Query(None),
    sort_direction: Optional[str] = Query("desc", regex="^(asc|desc)$"),
    repo=Depends(get_repo)
):
    try:
        auditorias = repo.obtener_por_cliente(cliente_id)
        total, auditorias = _sort_and_paginate(auditorias, sort_field, sort_direction, page, limit)
        return {"total": total, "auditoria_calendarios": auditorias}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener auditorías del cliente: {str(e)}")


@router.get("/hito/{id_hito}",
            summary="Obtener auditoría de un hito",
            description="Devuelve todos los registros de auditoría de un hito específico.")
def obtener_por_hito(id_hito: int = Path(...), repo=Depends(get_repo)):
    try:
        return repo.obtener_por_hito(id_hito)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener auditorías del hito: {str(e)}")


@router.get("/{id}",
            summary="Obtener registro de auditoría por ID",
            description="Obtiene un registro de auditoría por su ID.")
def obtener_por_id(id: int = Path(...), repo=Depends(get_repo)):
    result = repo.obtener_por_id(id)
    if not result:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    return result
