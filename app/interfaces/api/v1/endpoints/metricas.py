from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.infrastructure.db.database import SessionLocal
from app.application.services.metricas_service import MetricasService
from app.interfaces.schemas.metricas import (
    CumplimientoHitosSchema,
    HitosPorProcesoSchema,
    TiempoResolucionSchema,
    HitosVencidosSchema,
    ClientesInactivosSchema,
    VolumenMensualSchema,
    ResumenMetricasSchema
)

router = APIRouter(prefix="/metricas", tags=["Metricas"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/cumplimiento-hitos", response_model=CumplimientoHitosSchema)
async def get_cumplimiento_hitos(
    cliente_id: Optional[str] = Query(None, description="Filtrar por ID de cliente"),
    db: Session = Depends(get_db)
):
    """
    Obtiene el porcentaje de cumplimiento de hitos (todos los hitos disponibles o filtrados por cliente)
    """
    metricas_service = MetricasService(db)
    return metricas_service.get_cumplimiento_hitos(cliente_id=cliente_id)

@router.get("/hitos-por-proceso", response_model=HitosPorProcesoSchema)
async def get_hitos_por_proceso(
    cliente_id: Optional[str] = Query(None, description="Filtrar por ID de cliente"),
    db: Session = Depends(get_db)
):
    """
    Obtiene el total de hitos abiertos/pendientes por tipo de proceso (todos los procesos disponibles o filtrados por cliente)
    """
    metricas_service = MetricasService(db)
    return metricas_service.get_hitos_por_proceso(cliente_id=cliente_id)

@router.get("/tiempo-resolucion", response_model=TiempoResolucionSchema)
async def get_tiempo_resolucion(
    cliente_id: Optional[str] = Query(None, description="Filtrar por ID de cliente"),
    db: Session = Depends(get_db)
):
    """
    Obtiene el tiempo medio de resolución de hitos (todos los hitos disponibles o filtrados por cliente)
    """
    metricas_service = MetricasService(db)
    return metricas_service.get_tiempo_resolucion(cliente_id=cliente_id)

@router.get("/hitos-vencidos", response_model=HitosVencidosSchema)
async def get_hitos_vencidos(
    db: Session = Depends(get_db)
):
    """
    Obtiene alertas de hitos vencidos sin cerrar (todos los hitos disponibles)
    """
    metricas_service = MetricasService(db)
    return metricas_service.get_hitos_vencidos()

@router.get("/clientes-inactivos", response_model=ClientesInactivosSchema)
async def get_clientes_inactivos(
    db: Session = Depends(get_db)
):
    """
    Obtiene clientes sin hitos activos (todos los clientes disponibles)
    """
    metricas_service = MetricasService(db)
    return metricas_service.get_clientes_inactivos()

@router.get("/volumen-mensual", response_model=VolumenMensualSchema)
async def get_volumen_mensual(
    cliente_id: Optional[str] = Query(None, description="Filtrar por ID de cliente"),
    db: Session = Depends(get_db)
):
    """
    Obtiene el volumen mensual de hitos (todos los hitos disponibles o filtrados por cliente)
    """
    metricas_service = MetricasService(db)
    return metricas_service.get_volumen_mensual(cliente_id=cliente_id)

@router.get("/resumen", response_model=ResumenMetricasSchema)
async def get_resumen_metricas(
    db: Session = Depends(get_db)
):
    """
    Obtiene el resumen de todas las métricas para el dashboard general (todos los datos disponibles)
    """
    metricas_service = MetricasService(db)
    return metricas_service.get_resumen_metricas()
