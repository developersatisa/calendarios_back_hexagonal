from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.infrastructure.db.database import SessionLocal
from app.infrastructure.db.repositories.cliente_proceso_hito_repository_sql import ClienteProcesoHitoRepositorySQL
from app.application.services.cliente_proceso_hito_status_service import ClienteProcesoHitoStatusService

router = APIRouter(prefix="/status-todos-clientes", tags=["Status Todos los Clientes"])

# — Dependencias —

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_repository(db: Session = Depends(get_db)):
    return ClienteProcesoHitoRepositorySQL(db)

def get_service(repository: ClienteProcesoHitoRepositorySQL = Depends(get_repository)):
    return ClienteProcesoHitoStatusService(repository)

# — Endpoints —

@router.get("/hitos", summary="Obtener todos los hitos habilitados de todos los clientes",
            description="Devuelve todos los hitos habilitados de todos los clientes con información relacionada (cliente, proceso, hito maestro) y el último cumplimiento si existe.")
def get_status_todos_clientes(
    fecha_limite_desde: Optional[str] = Query(None, description="Filtrar por fecha límite desde (YYYY-MM-DD)"),
    fecha_limite_hasta: Optional[str] = Query(None, description="Filtrar por fecha límite hasta (YYYY-MM-DD)"),
    cliente_id: Optional[str] = Query(None, description="Filtrar por ID de cliente"),
    proceso_id: Optional[int] = Query(None, description="Filtrar por ID de proceso"),
    hito_id: Optional[int] = Query(None, description="Filtrar por ID de hito"),
    ordenar_por: Optional[str] = Query("fecha_limite", description="Campo para ordenar (fecha_limite, cliente_nombre, proceso_nombre)"),
    orden: Optional[str] = Query("asc", description="Orden (asc o desc)"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Límite de resultados"),
    offset: Optional[int] = Query(None, ge=0, description="Offset para paginación"),
    service: ClienteProcesoHitoStatusService = Depends(get_service)
):
    try:
        # Validar fechas
        if fecha_limite_desde:
            try:
                date.fromisoformat(fecha_limite_desde)
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de fecha_limite_desde inválido. Use YYYY-MM-DD")

        if fecha_limite_hasta:
            try:
                date.fromisoformat(fecha_limite_hasta)
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de fecha_limite_hasta inválido. Use YYYY-MM-DD")

        filtros = {
            'fecha_limite_desde': date.fromisoformat(fecha_limite_desde) if fecha_limite_desde else None,
            'fecha_limite_hasta': date.fromisoformat(fecha_limite_hasta) if fecha_limite_hasta else None,
            'cliente_id': cliente_id,
            'proceso_id': proceso_id,
            'hito_id': hito_id,
            'ordenar_por': ordenar_por,
            'orden': orden
        }

        paginacion = {
            'limit': limit,
            'offset': offset
        }

        return service.obtener_reporte_status(filtros, paginacion)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener hitos: {str(e)}")


@router.get("/exportar-excel", summary="Exportar status de todos los clientes a Excel",
            description="Genera y descarga un archivo Excel con el estado de los hitos filtrados, utilizando colores para indicar el estado de cumplimiento.")
def exportar_status_todos_excel(
    fecha_limite_desde: Optional[str] = Query(None, alias="fecha_desde", description="Filtrar por fecha límite desde (YYYY-MM-DD)"),
    fecha_limite_hasta: Optional[str] = Query(None, alias="fecha_hasta", description="Filtrar por fecha límite hasta (YYYY-MM-DD)"),
    cliente_id: Optional[str] = Query(None, description="Filtrar por ID de cliente"),
    proceso_nombre: Optional[str] = Query(None, description="Filtrar por nombre del proceso"),
    hito_id: Optional[int] = Query(None, description="Filtrar por ID de hito"),
    estados: Optional[str] = Query(None, description="Filtrar por estados (separados por coma): cumplido_en_plazo,cumplido_fuera_plazo,vence_hoy,pendiente_fuera_plazo,pendiente_en_plazo"),
    tipos: Optional[str] = Query(None, description="Filtrar por tipos (separados por coma): Atisa,Cliente,Terceros"),
    search_term: Optional[str] = Query(None, description="Búsqueda de texto libre en proceso_nombre y hito_nombre"),
    service: ClienteProcesoHitoStatusService = Depends(get_service)
):
    try:
        # Validar fechas (opcional, pero buena práctica)
        if fecha_limite_desde:
            try:
                date.fromisoformat(fecha_limite_desde)
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de fecha_limite_desde inválido. Use YYYY-MM-DD")

        if fecha_limite_hasta:
            try:
                date.fromisoformat(fecha_limite_hasta)
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de fecha_limite_hasta inválido. Use YYYY-MM-DD")

        filtros = {
            'fecha_limite_desde': date.fromisoformat(fecha_limite_desde) if fecha_limite_desde else None,
            'fecha_limite_hasta': date.fromisoformat(fecha_limite_hasta) if fecha_limite_hasta else None,
            'cliente_id': cliente_id,
            'proceso_nombre': proceso_nombre,
            'hito_id': hito_id,
            'estados': estados,
            'tipos': tipos,
            'search_term': search_term
        }

        output = service.exportar_reporte_excel(filtros)

        filename = f"status_todos_clientes_{date.today().strftime('%Y-%m-%d')}.xlsx"
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename={filename}',
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al exportar Excel: {str(e)}")
