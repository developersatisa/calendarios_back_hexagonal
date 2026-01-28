from pydantic import BaseModel
from typing import List, Optional

class CumplimientoClienteSchema(BaseModel):
    clienteId: str
    clienteNombre: str
    porcentaje: float
    hitosTotales: int
    hitosCompletados: int

class CumplimientoHitosSchema(BaseModel):
    porcentajeGeneral: float
    tendencia: str
    clientesData: Optional[List[CumplimientoClienteSchema]] = None

class ProcesoDataSchema(BaseModel):
    nombreProceso: str
    hitosPendientes: int
    hitosCompletados: int

class ProcesoClienteDataSchema(BaseModel):
    clienteId: str
    clienteNombre: str
    procesosData: List[ProcesoDataSchema]

class HitosPorProcesoSchema(BaseModel):
    totalPendientes: int
    tendencia: str
    procesoData: List[ProcesoDataSchema]
    clientesData: Optional[List[ProcesoClienteDataSchema]] = None

class ResolucionDataSchema(BaseModel):
    periodo: str
    tiempoMedio: float

class ResolucionClienteDataSchema(BaseModel):
    clienteId: str
    clienteNombre: str
    tiempoMedioDias: float
    resolucionData: List[ResolucionDataSchema]

class TiempoResolucionSchema(BaseModel):
    tiempoMedioDias: float
    tendencia: str
    resolucionData: List[ResolucionDataSchema]
    clientesData: Optional[List[ResolucionClienteDataSchema]] = None

class HitoVencidoClienteSchema(BaseModel):
    clienteId: str
    clienteNombre: str
    totalVencidos: int

class HitosVencidosSchema(BaseModel):
    totalVencidos: int
    tendencia: str
    clientesData: Optional[List[HitoVencidoClienteSchema]] = None

class ClientesInactivosSchema(BaseModel):
    totalInactivos: int
    tendencia: str

class VolumenDataSchema(BaseModel):
    mes: str
    hitosCreados: int
    hitosCompletados: int

class VolumenClienteDataSchema(BaseModel):
    clienteId: str
    clienteNombre: str
    totalMesActual: int
    volumenData: List[VolumenDataSchema]

class VolumenMensualSchema(BaseModel):
    totalMesActual: int
    tendencia: str
    volumenData: List[VolumenDataSchema]
    clientesData: Optional[List[VolumenClienteDataSchema]] = None

class MetricaResumenNumericaSchema(BaseModel):
    valor: int
    tendencia: str

class ResumenMetricasSchema(BaseModel):
    hitosCompletados: MetricaResumenNumericaSchema
    hitosPendientes: MetricaResumenNumericaSchema
    hitosVencidos: MetricaResumenNumericaSchema
    clientesInactivos: MetricaResumenNumericaSchema
