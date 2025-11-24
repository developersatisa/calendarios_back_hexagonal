from fastapi import APIRouter, Depends, HTTPException, Body, Path, Query
from sqlalchemy.orm import Session
from typing import Optional
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

@router.post("",
            response_model=AuditoriaCalendariosResponse,
            summary="Crear registro de auditoría",
            description="Crea un nuevo registro de auditoría")
def crear(data: AuditoriaCalendariosCreate, repo = Depends(get_repo)):
    try:
        auditoria = AuditoriaCalendarios(
            id=None,
            cliente_id=data.cliente_id,
            hito_id=data.hito_id,
            campo_modificado=data.campo_modificado,
            valor_anterior=data.valor_anterior or "",
            valor_nuevo=data.valor_nuevo or "",
            usuario_modificacion=data.usuario_modificacion,
            fecha_modificacion=datetime.utcnow(),
            observaciones=data.observaciones
        )
        resultado = repo.guardar(auditoria)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear registro de auditoría: {str(e)}")

@router.get("", summary="Listar registros de auditoría", description="Devuelve todos los registros de auditoría definidos en el sistema.")
def listar(
    page: Optional[int] = Query(None, ge=1, description="Página actual"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Cantidad de resultados por página"),
    sort_field: Optional[str] = Query(None, description="Campo por el cual ordenar"),
    sort_direction: Optional[str] = Query("desc", regex="^(asc|desc)$", description="Dirección de ordenación: asc o desc"),
    repo = Depends(get_repo)
):
    auditorias = repo.listar()
    total = len(auditorias)

    # Aplicar ordenación si se especifica y hay datos para ordenar
    if sort_field and auditorias and hasattr(auditorias[0], sort_field):
        reverse = sort_direction == "desc"

        # Función de ordenación que maneja valores None
        def sort_key(auditoria):
            value = getattr(auditoria, sort_field, None)

            # Manejo especial para diferentes tipos de campos
            if sort_field in ["id", "id_hito"]:
                if value is None:
                    return -1 if not reverse else float('inf')
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return -1 if not reverse else float('inf')

            elif sort_field in ["fecha_modificacion", "created_at", "updated_at"]:
                if value is None:
                    return -1 if not reverse else float('inf')
                try:
                    if hasattr(value, 'timestamp'):
                        return value.timestamp()
                    return -1 if not reverse else float('inf')
                except (ValueError, TypeError):
                    return -1 if not reverse else float('inf')
            else:
                # Para campos de texto
                if value is None:
                    return ""
                return str(value).lower()

        auditorias.sort(key=sort_key, reverse=reverse)

    # Aplicar paginación después de ordenar
    if page is not None and limit is not None:
        start = (page - 1) * limit
        end = start + limit
        auditorias = auditorias[start:end]

    return {
        "total": total,
        "auditoria_calendarios": auditorias
    }

@router.get("/{id}", summary="Obtener registro de auditoría por ID", description="Obtiene un registro de auditoría por su ID")
def obtener_por_id(id: int = Path(...), repo = Depends(get_repo)):
    return repo.obtener_por_id(id)

@router.get("/hito/{id_hito}", summary="Obtener auditoría de un hito específico", description="Obtiene todos los registros de auditoría de un hito específico")
def obtener_por_hito(id_hito: int = Path(...), repo = Depends(get_repo)):
    return repo.obtener_por_hito(id_hito)

@router.get("/cliente/{cliente_id}", summary="Obtener auditoría de un cliente específico", description="Devuelve todos los registros de auditoría de un cliente específico.")
def obtener_por_cliente(
    cliente_id: str = Path(..., description="ID del cliente"),
    page: Optional[int] = Query(None, ge=1, description="Página actual"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Cantidad de resultados por página"),
    sort_field: Optional[str] = Query(None, description="Campo por el cual ordenar"),
    sort_direction: Optional[str] = Query("desc", regex="^(asc|desc)$", description="Dirección de ordenación: asc o desc"),
    repo = Depends(get_repo)
):
    resultados = repo.obtener_por_cliente(cliente_id)
    total = len(resultados)

    # Procesar los resultados para incluir el nombre del hito
    auditorias = []
    for auditoria_model, nombre_hito in resultados:
        auditoria_dict = {
            "id": auditoria_model.id,
            "cliente_id": auditoria_model.cliente_id,
            "hito_id": auditoria_model.hito_id,
            "nombre_hito": nombre_hito,
            "campo_modificado": auditoria_model.campo_modificado,
            "valor_anterior": auditoria_model.valor_anterior,
            "valor_nuevo": auditoria_model.valor_nuevo,
            "usuario_modificacion": auditoria_model.usuario_modificacion,
            "fecha_modificacion": auditoria_model.fecha_modificacion,
            "observaciones": auditoria_model.observaciones,
            "created_at": auditoria_model.created_at,
            "updated_at": auditoria_model.updated_at
        }
        auditorias.append(auditoria_dict)

    # Aplicar ordenación si se especifica y hay datos para ordenar
    if sort_field and auditorias and sort_field in auditorias[0]:
        reverse = sort_direction == "desc"

        # Función de ordenación que maneja valores None
        def sort_key(auditoria):
            value = auditoria.get(sort_field)

            # Manejo especial para diferentes tipos de campos
            if sort_field in ["id", "hito_id"]:
                if value is None:
                    return -1 if not reverse else float('inf')
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return -1 if not reverse else float('inf')

            elif sort_field in ["fecha_modificacion", "created_at", "updated_at"]:
                if value is None:
                    return -1 if not reverse else float('inf')
                try:
                    if hasattr(value, 'timestamp'):
                        return value.timestamp()
                    return -1 if not reverse else float('inf')
                except (ValueError, TypeError):
                    return -1 if not reverse else float('inf')
            else:
                # Para campos de texto
                if value is None:
                    return ""
                return str(value).lower()

        auditorias.sort(key=sort_key, reverse=reverse)

    # Aplicar paginación después de ordenar
    if page is not None and limit is not None:
        start = (page - 1) * limit
        end = start + limit
        auditorias = auditorias[start:end]

    return {
        "total": total,
        "auditoria_calendarios": auditorias
    }
