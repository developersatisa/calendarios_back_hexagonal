from fastapi import APIRouter, Depends, HTTPException, Body, Path, Query
from sqlalchemy.orm import Session
from app.infrastructure.db.database import SessionLocal
from app.infrastructure.db.repositories.cliente_proceso_hito_repository_sql import ClienteProcesoHitoRepositorySQL
from app.application.use_cases.cliente_proceso_hito.actualizar_fecha_masivo import actualizar_fecha_masivo
from app.interfaces.schemas.cliente_proceso_hito_api import UpdateFechaMasivoRequest

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

@router.get("", summary="Listar todas las relaciones cliente-proceso-hito",
    description="Devuelve todas las relaciones entre clientes, procesos e hitos registradas.")
def listar(repo = Depends(get_repo)):
    return repo.listar()

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
    hito_id: int = Path(..., description="ID del hito (maestro)"),
    fecha_desde: str = Query(..., description="Fecha ISO (YYYY-MM-DD) desde la cual deshabilitar los hitos"),
    repo = Depends(get_repo)
):
    try:
        resultado = repo.deshabilitar_desde_fecha_por_hito(hito_id, fecha_desde)
        return {
            "mensaje": "Hitos deshabilitados exitosamente",
            "hitos_afectados": resultado['hitos_afectados'],
            "cliente_procesos_deshabilitados": resultado['cliente_procesos_deshabilitados'],
            "fecha_desde": fecha_desde,
            "resumen": f"Se deshabilitaron {resultado['hitos_afectados']} hitos y {len(resultado['cliente_procesos_deshabilitados'])} procesos de cliente"
        }
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
        fecha_desde=data.fecha_desde,
        fecha_hasta=data.fecha_hasta
    )

    return {
        "mensaje": "Actualización masiva completada",
        "registros_actualizados": count
    }
