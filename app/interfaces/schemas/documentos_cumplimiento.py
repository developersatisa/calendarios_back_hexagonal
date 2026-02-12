# app/interfaces/schemas/documentos_cumplimiento.py

from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class DocumentosCumplimientoResponse(BaseModel):
    id: int
    cumplimiento_id: int
    nombre_documento: str
    original_file_name: str
    stored_file_name: str
    autor: Optional[str] = None
    codSubDepar: Optional[str] = None
    fecha_creacion: Optional[datetime] = None

    class Config:
        from_attributes = True
