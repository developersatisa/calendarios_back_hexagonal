from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AuditoriaCalendariosCreate(BaseModel):
    cliente_id: str
    hito_id: int
    campo_modificado: str
    valor_anterior: str = ""
    valor_nuevo: str = ""
    observaciones: Optional[str] = None
    motivo: Optional[int] = None
    usuario: str
    codSubDepar: Optional[str] = None


class AuditoriaCalendariosUpdate(BaseModel):
    campo_modificado: Optional[str] = None
    valor_anterior: Optional[str] = None
    valor_nuevo: Optional[str] = None
    observaciones: Optional[str] = None
    motivo: Optional[int] = None
    usuario: Optional[str] = None
    codSubDepar: Optional[str] = None


class AuditoriaCalendariosResponse(BaseModel):
    id: int
    cliente_id: str
    hito_id: int
    campo_modificado: str
    valor_anterior: str
    valor_nuevo: str
    observaciones: Optional[str] = None
    motivo: Optional[int] = None
    motivo_descripcion: Optional[str] = None
    usuario: str
    nombre_usuario: Optional[str] = None
    codSubDepar: Optional[str] = None
    fecha_modificacion: datetime
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Campos enriquecidos (de joins)
    hito_nombre: Optional[str] = None
    proceso_nombre: Optional[str] = None
    nombre_subdepar: Optional[str] = None
    tipo: Optional[str] = None
    critico: Optional[bool] = None
    obligatorio: Optional[bool] = None
    fecha_limite_anterior: Optional[str] = None
    fecha_limite_actual: Optional[str] = None
    momento_cambio: Optional[str] = None

    class Config:
        orm_mode = True
