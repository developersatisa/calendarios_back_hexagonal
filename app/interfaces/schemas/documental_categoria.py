from pydantic import BaseModel
from typing import Optional

class DocumentalCategoriaCreate(BaseModel):
    cliente_id: str
    nombre: str

class DocumentalCategoriaUpdate(BaseModel):
    nombre: Optional[str] = None

class DocumentalCategoriaResponse(BaseModel):
    id: int
    cliente_id: str
    nombre: str

    class Config:
        orm_mode = True
