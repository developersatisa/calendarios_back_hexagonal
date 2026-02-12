from pydantic import BaseModel

class DocumentalCarpetaClienteBase(BaseModel):
    cliente_id: str
    proceso_id: int
    carpeta_id: int

class DocumentalCarpetaClienteCreate(DocumentalCarpetaClienteBase):
    pass

class DocumentalCarpetaClienteUpdate(BaseModel):
    # Normalmente estas relaciones no se actualizan parcialmente, pero lo dejamos por consistencia
    pass

class DocumentalCarpetaClienteRead(DocumentalCarpetaClienteBase):
    id: int
    nombre_carpeta: str | None = None
    class Config:
        orm_mode = True
