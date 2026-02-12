from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from app.infrastructure.db.database import SessionLocal
from app.infrastructure.db.repositories.cliente_proceso_repository_sql import ClienteProcesoRepositorySQL
from app.infrastructure.db.repositories.proceso_repository_sql import ProcesoRepositorySQL
from app.infrastructure.db.repositories.proceso_hito_maestro_repository_sql import ProcesoHitoMaestroRepositorySQL
from app.infrastructure.db.repositories.cliente_proceso_hito_repository_sql import ClienteProcesoHitoRepositorySQL

from app.application.use_cases.cliente_proceso.crear_cliente_proceso import crear_cliente_proceso
from app.application.use_cases.cliente_proceso.generar_calendario_cliente_proceso import generar_calendario_cliente_proceso
from app.interfaces.schemas.cliente_proceso import GenerarClienteProcesoRequest

router = APIRouter(prefix="/cliente-procesos", tags=["ClienteProceso"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_repo(db: Session = Depends(get_db)):
    return ClienteProcesoRepositorySQL(db)

def get_repo_proceso(db: Session = Depends(get_db)):
    return ProcesoRepositorySQL(db)

def get_repo_proceso_hito_maestro(db: Session = Depends(get_db)):
    return ProcesoHitoMaestroRepositorySQL(db)

def get_repo_cliente_proceso_hito(db: Session = Depends(get_db)):
    return ClienteProcesoHitoRepositorySQL(db)

@router.post("")
def crear(data: dict, repo = Depends(get_repo)):
    return crear_cliente_proceso(data, repo)

@router.get("")
def listar(
    page: Optional[int] = Query(None, ge=1, description="Página actual"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Cantidad de resultados por página (máximo 10000)"),
    sort_field: Optional[str] = Query(None, description="Campo por el cual ordenar"),
    sort_direction: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Dirección de ordenación: asc o desc"),
    repo = Depends(get_repo)
):
    items = repo.listar()
    total = len(items)

    # Aplicar ordenación si se especifica
    if sort_field and hasattr(items[0] if items else None, sort_field):
        reverse = sort_direction == "desc"
        def sort_key(item):
            val = getattr(item, sort_field, None)
            if val is None:
                return ""
            if sort_field == "id":
                try:
                    return int(val)
                except (ValueError, TypeError):
                    return 0
            return str(val).lower() if isinstance(val, str) else val

        items.sort(key=sort_key, reverse=reverse)

    # Aplicar paginación
    if page is not None and limit is not None:
        start = (page - 1) * limit
        end = start + limit
        items = items[start:end]

    return {
        "total": total,
        "items": items
    }

@router.get("/{id}")
def get(id: int, repo = Depends(get_repo)):
    cliente_proceso = repo.obtener_por_id(id)
    if not cliente_proceso:
        raise HTTPException(status_code=404, detail="No encontrado")
    return cliente_proceso

@router.get("/cliente/{cliente_id}")
def get_por_cliente(cliente_id: str,
                    page: Optional[int] = Query(None, ge=1, description="Página actual"),
                    limit: Optional[int] = Query(None, ge=1, le=10000, description="Cantidad de resultados por página (máximo 10000)"),
                    sort_field: Optional[str] = Query(None, description="Campo por el cual ordenar"),
                    sort_direction: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Dirección de ordenación: asc o desc"),
                    repo = Depends(get_repo)):

    cliente_procesos = repo.listar_por_cliente(cliente_id)
    total = len(cliente_procesos)

    # Aplicar ordenación si se especifica
    if sort_field and hasattr(cliente_procesos[0] if cliente_procesos else None, sort_field):
        reverse = sort_direction == "desc"
        def sort_key(item):
            val = getattr(item, sort_field, None)
            if val is None:
                return ""
            if sort_field == "id":
                try:
                    return int(val)
                except (ValueError, TypeError):
                    return 0
            return str(val).lower() if isinstance(val, str) else val

        cliente_procesos.sort(key=sort_key, reverse=reverse)

    if page is not None and limit is not None:
        start = (page - 1) * limit
        end = start + limit
        cliente_procesos = cliente_procesos[start:end]

    return {
        "clienteProcesos" : cliente_procesos,
        "total": total
    }

@router.get("/habilitados", summary="Listar procesos de cliente habilitados",
    description="Devuelve solo los procesos de cliente que están habilitados (habilitado=True).")
def listar_habilitados(
    page: Optional[int] = Query(None, ge=1, description="Página actual"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Cantidad de resultados por página (máximo 10000)"),
    sort_field: Optional[str] = Query(None, description="Campo por el cual ordenar"),
    sort_direction: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Dirección de ordenación: asc o desc"),
    repo = Depends(get_repo)
):
    items = repo.listar_habilitados()
    total = len(items)

    # Aplicar ordenación si se especifica
    if sort_field and hasattr(items[0] if items else None, sort_field):
        reverse = sort_direction == "desc"
        def sort_key(item):
            val = getattr(item, sort_field, None)
            if val is None:
                return ""
            if sort_field == "id":
                try:
                    return int(val)
                except (ValueError, TypeError):
                    return 0
            return str(val).lower() if isinstance(val, str) else val

        items.sort(key=sort_key, reverse=reverse)

    if page is not None and limit is not None:
        start = (page - 1) * limit
        end = start + limit
        items = items[start:end]

    return {
        "total": total,
        "items": items
    }

@router.get("/cliente/{cliente_id}/habilitados", summary="Listar procesos de cliente habilitados por cliente",
    description="Devuelve solo los procesos de cliente habilitados de un cliente específico.")
def get_habilitados_por_cliente(
    cliente_id: str,
    page: Optional[int] = Query(None, ge=1, description="Página actual"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Cantidad de resultados por página (máximo 10000)"),
    sort_field: Optional[str] = Query(None, description="Campo por el cual ordenar"),
    sort_direction: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Dirección de ordenación: asc o desc"),
    repo = Depends(get_repo)
):
    cliente_procesos = repo.listar_habilitados_por_cliente(cliente_id)
    total = len(cliente_procesos)

    # Aplicar ordenación si se especifica
    if sort_field and hasattr(cliente_procesos[0] if cliente_procesos else None, sort_field):
        reverse = sort_direction == "desc"
        def sort_key(item):
            val = getattr(item, sort_field, None)
            if val is None:
                return ""
            if sort_field == "id":
                try:
                    return int(val)
                except (ValueError, TypeError):
                    return 0
            return str(val).lower() if isinstance(val, str) else val

        cliente_procesos.sort(key=sort_key, reverse=reverse)

    if page is not None and limit is not None:
        start = (page - 1) * limit
        end = start + limit
        cliente_procesos = cliente_procesos[start:end]

    return {
        "clienteProcesos": cliente_procesos,
        "total": total
    }

@router.delete("/{id}")
def delete(id: int, repo = Depends(get_repo)):
    ok = repo.eliminar(id)
    if not ok:
        raise HTTPException(status_code=404, detail="No encontrado")
    return {"mensaje": "Eliminado"}

router_calendario = APIRouter(prefix="", tags=["Generar Calendario"])

@router_calendario.post("/generar-calendario-cliente-proceso")
def generar_calendario_cliente_by_proceso(request: GenerarClienteProcesoRequest,
                                        repo = Depends(get_repo),
                                        proceso_repo = Depends(get_repo_proceso),
                                        repo_proceso_hito_maestro = Depends(get_repo_proceso_hito_maestro),
                                        repo_cliente_proceso_hito = Depends(get_repo_cliente_proceso_hito)):
    proceso_maestro = proceso_repo.obtener_por_id(request.proceso_id)
    if not proceso_maestro:
        raise HTTPException(status_code=404, detail="Proceso no encontrado")

    # Validar que no exista solapamiento
    start_date = request.fecha_inicio or date.today()
    # Si solo manda fecha de inicio, asumimos que intenta generar hasta fin de año
    end_date = date(start_date.year, 12, 31)

    existentes = repo.listar_por_cliente(request.cliente_id)
    for p in existentes:
        if p.proceso_id == request.proceso_id:
            # Check overlap: (StartA <= EndB) and (EndA >= StartB)
            p_fin = p.fecha_fin or date.max
            if p.fecha_inicio <= end_date and start_date <= p_fin:
                 raise HTTPException(status_code=400, detail=f"El proceso ya existe en el rango seleccionado ({p.fecha_inicio} - {p_fin})")

    return generar_calendario_cliente_proceso(request,proceso_maestro, repo,repo_proceso_hito_maestro, repo_cliente_proceso_hito)
