# app/interfaces/schemas/documentos_cumplimiento.py

from pydantic import BaseModel

class DocumentosCumplimientoResponse(BaseModel):
    id: int
    cumplimiento_id: int
    nombre_documento: str
    original_file_name: str
    stored_file_name: str

    class Config:
        from_attributes = True
