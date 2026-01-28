from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AuditoriaCalendariosCreate(BaseModel):
    cliente_id: str
    hito_id: int
    campo_modificado: str
    valor_anterior: str = ""
    valor_nuevo: str = ""
    usuario_modificacion: str
    observaciones: Optional[str] = None

class AuditoriaCalendariosUpdate(BaseModel):
    campo_modificado: Optional[str] = None
    valor_anterior: Optional[str] = None
    valor_nuevo: Optional[str] = None
    usuario_modificacion: Optional[str] = None
    observaciones: Optional[str] = None

class AuditoriaCalendariosResponse(BaseModel):
    id: int
    cliente_id: str
    hito_id: int
    campo_modificado: str
    valor_anterior: str
    valor_nuevo: str
    usuario_modificacion: str
    fecha_modificacion: datetime
    observaciones: Optional[str] = None

    class Config:
        orm_mode = True
