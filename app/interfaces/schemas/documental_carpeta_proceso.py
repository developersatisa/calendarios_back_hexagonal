from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DocumentalCarpetaProcesoBase(BaseModel):
    proceso_id: int
    nombre: str
    descripcion: Optional[str] = None
    eliminado: bool = False

class DocumentalCarpetaProcesoCreate(DocumentalCarpetaProcesoBase):
    pass

class DocumentalCarpetaProcesoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    eliminado: Optional[bool] = None

class DocumentalCarpetaProcesoRead(DocumentalCarpetaProcesoBase):
    id: int
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    class Config:
        orm_mode = True
