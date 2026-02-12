from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DocumentalCarpetaDocumentosBase(BaseModel):
    carpeta_id: int
    nombre_documento: str
    original_file_name: str
    stored_file_name: str
    autor: str
    codSubDepar: Optional[str] = None
    eliminado: bool = False

class DocumentalCarpetaDocumentosCreate(DocumentalCarpetaDocumentosBase):
    pass

class DocumentalCarpetaDocumentosUpdate(BaseModel):
    nombre_documento: Optional[str] = None
    eliminado: Optional[bool] = None

class DocumentalCarpetaDocumentosRead(DocumentalCarpetaDocumentosBase):
    id: int
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    departamento: Optional[str] = None
    # Legacy properties just in case
    success: Optional[bool] = True
    message: Optional[str] = "Documento procesado correctamente"
    class Config:
        orm_mode = True
