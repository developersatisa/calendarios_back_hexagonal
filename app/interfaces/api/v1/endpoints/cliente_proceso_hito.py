from fastapi import APIRouter, Depends, HTTPException, Body, Path, Query
from fastapi.responses import StreamingResponse
from app.application.services.cliente_proceso_hito_status_service import ClienteProcesoHitoStatusService
from typing import Optional, List
from datetime import date
from sqlalchemy.orm import Session
from app.infrastructure.db.database import SessionLocal
from app.infrastructure.db.repositories.cliente_proceso_hito_repository_sql import ClienteProcesoHitoRepositorySQL
from app.application.use_cases.cliente_proceso_hito.actualizar_fecha_masivo import actualizar_fecha_masivo
from app.interfaces.schemas.cliente_proceso_hito_api import UpdateFechaMasivoRequest, UpdateDeshabilitarHitoRequest

from app.domain.entities.cliente_proceso_hito import ClienteProcesoHito

router = APIRouter(prefix="/cliente-proceso-hitos", tags=["ClienteProcesoHito"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_repo(db: Session = Depends(get_db)):
    return ClienteProcesoHitoRepositorySQL(db)

def get_service(repo: ClienteProcesoHitoRepositorySQL = Depends(get_repo)):
    return ClienteProcesoHitoStatusService(repo)

@router.post("/cliente-proceso-hitos", tags=["ClienteProcesoHito"], summary="Crear relación cliente-proceso-hito",
    description="Crea una nueva relación entre un cliente, proceso e hito especificando los IDs correspondientes y fecha límite.")
def crear(
    data: dict = Body(..., example={
        "cliente_proceso_id": 1,
        "hito_id": 2,
        "estado": "pendiente",
        "fecha_limite": "2023-01-05",
        "fecha_estado": "2023-01-01",
        "hora_limite": "12:00:00",
        "tipo": "Atisa"
    }),
    repo = Depends(get_repo)
):
    hito = ClienteProcesoHito(
        cliente_proceso_id=data["cliente_proceso_id"],
        hito_id=data["hito_id"],
        estado=data["estado"],
        fecha_estado=data.get("fecha_estado"),
        fecha_limite=data.get("fecha_limite"),
        hora_limite=data.get("hora_limite"),
        tipo=data["tipo"]
    )
    return repo.guardar(hito)

@router.get("/filtros", summary="Obtener filtros disponibles",
    description="Devuelve la lista de procesos e hitos disponibles para el mes, año y cliente seleccionados.")
def obtener_filtros(
    anio: int = Query(..., description="Año a filtrar"),
    mes: int = Query(..., description="Mes a filtrar"),
    cliente_id: Optional[str] = Query(None, description="Cliente a filtrar"),
    repo = Depends(get_repo)
):
    return repo.obtener_filtros(anio, mes, cliente_id)

@router.get("/fecha", summary="Obtener IDs por mes y año",

    description="Devuelve una lista de IDs de cliente_proceso_hito filtrada por mes y año.")
def obtener_por_fecha(
    anio: int = Query(..., description="Año a filtrar (YYYY)"),
    mes: int = Query(..., description="Mes a filtrar (1-12)"),
    cliente_id: Optional[str] = Query(None, description="Filtrar por ID de cliente"),
    proceso_ids: Optional[List[int]] = Query(None, description="Filtrar por lista de IDs de procesos"),
    hito_ids: Optional[List[int]] = Query(None, description="Filtrar por lista de IDs de hitos"),
    page: Optional[int] = Query(None, ge=1, description="Página actual"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Cantidad de resultados por página"),
    sort_by: Optional[str] = Query(None, description="Campo por el cual ordenar (id, fecha_limite, hora_limite, cliente, hito, proceso, estado)"),
    order: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Dirección de ordenación: asc o desc"),
    repo = Depends(get_repo)
):
    try:
        items = repo.obtener_por_fecha(anio, mes, cliente_id, proceso_ids, hito_ids)

        # Aplicar ordenación
        if sort_by:
            reverse = order == "desc"
            def sort_key(item):
                val = item.get(sort_by)
                if val is None:
                    return ""
                # Manejo especial para fechas si es necesario, pero aquí ya vienen como objetos date
                return str(val).lower() if isinstance(val, str) else val

            try:
                items.sort(key=sort_key, reverse=reverse)
            except Exception:
                pass

        total = len(items)

        # Aplicar paginación
        if page is not None and limit is not None:
            start = (page - 1) * limit
            end = start + limit
            items = items[start:end]

        return {
            "anio": anio,
            "mes": mes,
            "total": total,
            "items": items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener IDs: {str(e)}")

@router.get("/status-todos-clientes/hitos", summary="Listar hitos de clientes asignados al usuario",
    description="Devuelve el estado de hitos de los clientes asociados al email proporcionado.")
def status_todos_clientes_hitos(
    email: str = Query(..., description="Email del usuario para filtrar clientes"),
    fecha_limite_desde: Optional[date] = Query(None, alias="fecha_desde"),
    fecha_limite_hasta: Optional[date] = Query(None, alias="fecha_hasta"),
    cliente_id: Optional[str] = Query(None),
    proceso_id: Optional[int] = Query(None),
    hito_id: Optional[int] = Query(None),
    proceso_nombre: Optional[str] = Query(None),
    tipos: Optional[str] = Query(None),
    search_term: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    order: Optional[str] = Query("asc"),
    page: int = Query(1, ge=1),
    limit: Optional[int] = Query(100, ge=0),
    repo: ClienteProcesoHitoRepositorySQL = Depends(get_repo)
):
    filtros = {
        "fecha_limite_desde": fecha_limite_desde,
        "fecha_limite_hasta": fecha_limite_hasta,
        "cliente_id": cliente_id,
        "proceso_id": proceso_id,
        "hito_id": hito_id,
        "proceso_nombre": proceso_nombre,
        "tipos": tipos,
        "search_term": search_term,
        "ordenar_por": sort_by,
        "orden": order
    }

    paginacion = {}
    if limit is not None and limit > 0:
        paginacion = {
            "offset": (page - 1) * limit,
            "limit": limit
        }

    try:
        registros, total = repo.ejecutar_reporte_status_todos_clientes_por_usuario(filtros, paginacion, email)

        data = []
        for r in registros:
            ultimo_cumplimiento = None
            if r.cumplimiento_id:
                ultimo_cumplimiento = {
                    "id": r.cumplimiento_id,
                    "fecha": r.cumplimiento_fecha.isoformat() if r.cumplimiento_fecha else None,
                    "hora": str(r.cumplimiento_hora) if r.cumplimiento_hora else None,
                    "observacion": r.cumplimiento_observacion,
                    "usuario": r.cumplimiento_usuario,
                    "fecha_creacion": r.cumplimiento_fecha_creacion.isoformat() if r.cumplimiento_fecha_creacion else None,
                    "num_documentos": int(r.num_documentos or 0)
                }

            item = {
                "id": r.id,
                "cliente_proceso_id": r.cliente_proceso_id,
                "hito_id": r.hito_id,
                "estado": r.estado,
                "fecha_estado": r.fecha_estado.isoformat() if r.fecha_estado else None,
                "fecha_limite": r.fecha_limite.isoformat() if r.fecha_limite else None,
                "hora_limite": str(r.hora_limite) if r.hora_limite else None,
                "tipo": r.tipo,
                "habilitado": bool(r.habilitado),
                "cliente_id": str(r.cliente_id or ""),
                "cliente_nombre": str(r.cliente_nombre or "").strip(),
                "proceso_id": r.proceso_id,
                "proceso_nombre": str(r.proceso_nombre or "").strip(),
                "hito_nombre": str(r.hito_nombre or "").strip(),
                "obligatorio": bool(getattr(r, 'hito_obligatorio', 0) == 1),
                "critico": bool(getattr(r, 'hito_critico', False)),
                "ultimo_cumplimiento": ultimo_cumplimiento
            }
            data.append(item)

        return {
            "hitos": data,
            "total": total
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener reporte: {str(e)}")


@router.get("/status-todos-clientes/exportar-excel", summary="Exportar status de clientes asignados a Excel",
    description="Genera y descarga un archivo Excel con el estado de los hitos de los clientes asociados al email proporcionado.")
def exportar_status_todos_excel_por_usuario(
    email: str = Query(..., description="Email del usuario para filtrar clientes"),
    fecha_limite_desde: Optional[date] = Query(None),
    fecha_limite_hasta: Optional[date] = Query(None),
    cliente_id: Optional[str] = Query(None),
    proceso_id: Optional[int] = Query(None),
    hito_id: Optional[int] = Query(None),
    proceso_nombre: Optional[str] = Query(None),
    tipos: Optional[str] = Query(None),
    search_term: Optional[str] = Query(None),
    estados: Optional[str] = Query(None, description="Filtrar por estados (separados por coma)"),
    service: ClienteProcesoHitoStatusService = Depends(get_service)
):
    try:
        filtros = {
            "fecha_limite_desde": fecha_limite_desde,
            "fecha_limite_hasta": fecha_limite_hasta,
            "cliente_id": cliente_id,
            "proceso_id": proceso_id,
            "hito_id": hito_id,
            "proceso_nombre": proceso_nombre,
            "tipos": tipos,
            "search_term": search_term,
            "estados": estados
        }

        output = service.exportar_reporte_excel_por_usuario(filtros, email)

        filename = f"status_mis_clientes_{date.today().strftime('%Y-%m-%d')}.xlsx"
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename={filename}',
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al exportar Excel: {str(e)}")

@router.get("", summary="Listar todas las relaciones cliente-proceso-hito",
    description="Devuelve todas las relaciones entre clientes, procesos e hitos registradas.")
def listar(repo = Depends(get_repo)):
    return repo.listar()

@router.put("/update-masivo", summary="Actualización masiva de fechas",
    description="Actualiza la fecha límite de un hito para múltiples empresas, afectando solo a registros futuros (>= fecha_desde).")
def update_fecha_masivo(
    data: UpdateFechaMasivoRequest,
    repo: ClienteProcesoHitoRepositorySQL = Depends(get_repo)
):
    count = actualizar_fecha_masivo(
        repo=repo,
        hito_id=data.hito_id,
        cliente_ids=data.empresa_ids,
        nueva_fecha=data.nueva_fecha,
        nueva_hora=data.nueva_hora,
        fecha_desde=data.fecha_desde,
        fecha_hasta=data.fecha_hasta
    )

    return {
        "mensaje": "Actualización masiva completada",
        "registros_actualizados": count
    }

@router.get("/{id}", summary="Obtener relación por ID",
    description="Devuelve una relación cliente-proceso-hito específica según su ID.")
def get(
    id: int = Path(..., description="ID de la relación a consultar"),
    repo = Depends(get_repo)
):
    hito = repo.obtener_por_id(id)
    if not hito:
        raise HTTPException(status_code=404, detail="No encontrado")
    return hito

@router.put("/{id}", summary="Actualizar relación cliente-proceso-hito",
    description="Actualiza una relación cliente-proceso-hito existente por su ID.")
def actualizar(
    id: int = Path(..., description="ID de la relación a actualizar"),
    data: dict = Body(..., example={
        "estado": "completado",
        "fecha_estado": "2023-01-05T10:30:00",
        "habilitado": True
    }),
    repo = Depends(get_repo)
):
    try:
        # Validar que el registro existe
        hito_existente = repo.obtener_por_id(id)
        if not hito_existente:
            raise HTTPException(status_code=404, detail="Registro no encontrado")

        # Realizar la actualización
        hito_actualizado = repo.actualizar(id, data)
        if not hito_actualizado:
            raise HTTPException(status_code=500, detail="Error al actualizar el registro")

        return {
            "mensaje": "Registro actualizado exitosamente",
            "id": hito_actualizado.id,
            "datos_actualizados": {
                "estado": hito_actualizado.estado,
                "fecha_estado": hito_actualizado.fecha_estado.isoformat() if hito_actualizado.fecha_estado else None,
                "habilitado": hito_actualizado.habilitado
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.delete("/{id}", summary="Eliminar relación",
    description="Elimina una relación cliente-proceso-hito existente por su ID.")
def delete(
    id: int = Path(..., description="ID de la relación a eliminar"),
    repo = Depends(get_repo)
):
    ok = repo.eliminar(id)
    if not ok:
        raise HTTPException(status_code=404, detail="No encontrado")
    return {"mensaje": "Eliminado"}

@router.get("/cliente-proceso/{id_cliente_proceso}", summary="Listar hitos de un proceso de cliente",
    description="Devuelve todos los hitos asociados a un proceso de cliente específico.")
def get_hitos_por_proceso(
    id_cliente_proceso: int = Path(..., description="ID del proceso de cliente"),
    repo = Depends(get_repo)
):
    hitos = repo.obtener_por_cliente_proceso_id(id_cliente_proceso)
    if not hitos:
        raise HTTPException(status_code=404, detail="No se encontraron hitos para este proceso")
    return hitos

@router.get("/habilitados", summary="Listar hitos habilitados",
    description="Devuelve solo los hitos que están habilitados (habilitado=True).")
def listar_habilitados(repo = Depends(get_repo)):
    return repo.listar_habilitados()

@router.get("/cliente-proceso/{id_cliente_proceso}/habilitados", summary="Listar hitos habilitados de un proceso de cliente",
    description="Devuelve solo los hitos habilitados asociados a un proceso de cliente específico.")
def get_hitos_habilitados_por_proceso(
    id_cliente_proceso: int = Path(..., description="ID del proceso de cliente"),
    repo = Depends(get_repo)
):
    hitos = repo.obtener_habilitados_por_cliente_proceso_id(id_cliente_proceso)
    if not hitos:
        raise HTTPException(status_code=404, detail="No se encontraron hitos habilitados para este proceso")
    return hitos

@router.put("/hito/{hito_id}/deshabilitar-desde", summary="Deshabilitar hitos de un hito desde una fecha",
    description="Deshabilita (habilitado=False) todos los ClienteProcesoHito de un hito_id a partir de una fecha (inclusive). Si todos los hitos de un cliente_proceso quedan deshabilitados, también deshabilita el cliente_proceso.")
def deshabilitar_hitos_por_hito_desde(
    data: UpdateDeshabilitarHitoRequest,
    hito_id: int = Path(..., description="ID del hito (maestro)"),
    repo: ClienteProcesoHitoRepositorySQL = Depends(get_repo)
):
    try:
        if not data.fecha_desde:
             raise HTTPException(status_code=400, detail="Debe proporcionar 'fecha_desde' en el cuerpo de la solicitud")

        resultado = repo.deshabilitar_desde_fecha_por_hito(hito_id, data.fecha_desde, cliente_id=data.cliente_id)
        return {
            "mensaje": "Hitos deshabilitados exitosamente",
            "detalles": resultado
        }
    except HTTPException:
        raise
    except ValueError as e:
         raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al deshabilitar hitos: {str(e)}")

@router.put("/sincronizar-cliente-proceso/{cliente_proceso_id}", summary="Sincronizar estado de cliente_proceso",
    description="Verifica y actualiza el estado de habilitado de un cliente_proceso basado en sus hitos habilitados.")
def sincronizar_cliente_proceso(
    cliente_proceso_id: int = Path(..., description="ID del cliente_proceso a sincronizar"),
    repo = Depends(get_repo)
):
    try:
        resultado = repo.sincronizar_estado_cliente_proceso(cliente_proceso_id)

        if resultado['actualizado']:
            return {
                "mensaje": "Estado de cliente_proceso actualizado",
                "cliente_proceso_id": cliente_proceso_id,
                "actualizado": True,
                "estado_anterior": resultado['estado_anterior'],
                "estado_nuevo": resultado['estado_nuevo'],
                "hitos_habilitados": resultado['hitos_habilitados']
            }
        else:
            return {
                "mensaje": "Estado de cliente_proceso ya estaba correcto",
                "cliente_proceso_id": cliente_proceso_id,
                "actualizado": False,
                "estado_actual": resultado['estado_actual'],
                "hitos_habilitados": resultado['hitos_habilitados']
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al sincronizar cliente_proceso: {str(e)}")
