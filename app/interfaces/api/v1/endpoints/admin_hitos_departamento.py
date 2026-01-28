from typing import Optional
from fastapi import APIRouter, Depends, Query, Body, HTTPException, Path
from sqlalchemy.orm import Session

from app.infrastructure.db.database import SessionLocal
from app.infrastructure.db.repositories.admin_hitos_departamento_repository_sql import (
    AdminHitosDepartamentoRepositorySQL,
)


router = APIRouter(prefix="/admin-hitos", tags=["AdminHitosDepartamento"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_repo(db: Session = Depends(get_db)):
    return AdminHitosDepartamentoRepositorySQL(db)


@router.get(
    "/departamentos-hitos",
    summary="Listar hitos por departamentos",
    description=(
        "Dos modos: (1) Anidado por departamento/proceso (por defecto). "
        "(2) Plano y paginado cuando flat=1, devolviendo items + quedan + next_cursor. "
        "Incluye proceso, cliente (id, nombre, cif), estado, fecha_limite, hora_limite, tipo y habilitado (0/1)."
    ),
)
def listar_hitos_departamentos(
    mes: Optional[int] = Query(None, ge=1, le=12, description="Mes (1-12) de fecha límite"),
    anio: Optional[int] = Query(None, ge=2000, le=2100, description="Año de fecha límite"),
    cod_subdepar: Optional[str] = Query(None, description="Filtrar por código de subdepartamento"),
    flat: bool = Query(False, description="Si es 1/true devuelve resultado plano y paginado"),
    limit: Optional[int] = Query(1000, ge=1, le=5000, description="Tamaño de página en modo flat"),
    cursor: Optional[int] = Query(None, ge=0, description="Cursor (cliente_proceso_hito_id) para paginación flat"),
    repo = Depends(get_repo),
):
    if flat:
        # Modo plano y paginado (keyset pagination por cph.id)
        return repo.listar_hitos_departamentos_flat(
            mes=mes,
            anio=anio,
            cod_subdepar=cod_subdepar,
            limit=limit or 1000,
            cursor=cursor,
        )
    # Modo anidado original (sin paginación)
    return repo.listar_hitos_departamentos(mes=mes, anio=anio, cod_subdepar=cod_subdepar)


@router.post(
    "/departamento-hito/{cliente_proceso_hito_id}",
    summary="Actualizar campos de hito por ID de cliente_proceso_hito",
    description=(
        "Actualiza campos del hito a nivel de cliente_proceso_hito. "
        "Permite modificar: estado, fecha_limite, hora_limite y tipo. "
        "IMPORTANTE: 'tipo' SIEMPRE se obtiene y se modifica en la tabla 'hito' (nunca en cliente_proceso_hito)."
    ),
)
def actualizar_hito_departamento(
    cliente_proceso_hito_id: int = Path(..., description="ID del registro cliente_proceso_hito a actualizar"),
    data: dict = Body(..., example={
        "estado": "pendiente",
        "fecha_limite": "2025-10-01",
        "hora_limite": "13:30:00",
        "tipo": "Atisa"
    }),
    repo = Depends(get_repo),
):
    # Filtrar solo campos permitidos
    allowed_fields = {"estado", "fecha_limite", "hora_limite", "tipo"}
    payload = {k: v for k, v in data.items() if k in allowed_fields}

    # Normalizar hora HH:MM -> HH:MM:SS si aplica
    if "hora_limite" in payload and isinstance(payload["hora_limite"], str):
        partes = payload["hora_limite"].split(":")
        if len(partes) == 2:
            payload["hora_limite"] = payload["hora_limite"] + ":00"

    if not payload:
        raise HTTPException(status_code=400, detail="No hay campos válidos para actualizar")

    actualizado = repo.actualizar_hito_departamento(cliente_proceso_hito_id, payload)
    if not actualizado:
        raise HTTPException(status_code=404, detail="Registro no encontrado o sin campos válidos para actualizar")
    return actualizado