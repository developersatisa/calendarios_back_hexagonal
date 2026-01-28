from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DocumentalDocumentosCreate(BaseModel):
    cliente_id: str
    categoria_id: int
    nombre_documento: str
    original_file_name: str
    stored_file_name: str

class DocumentalDocumentosUpdate(BaseModel):
    cliente_id: Optional[str] = None
    categoria_id: Optional[int] = None
    nombre_documento: Optional[str] = None
    original_file_name: Optional[str] = None
    stored_file_name: Optional[str] = None

class DocumentalDocumentosResponse(BaseModel):
    id: int
    cliente_id: str
    categoria_id: int
    nombre_documento: str
    original_file_name: str
    stored_file_name: str
    fecha_creacion: Optional[datetime] = None

    class Config:
        orm_mode = True
