from pydantic import BaseModel, validator
from datetime import date
from typing import Optional

class GenerarClienteProcesoRequest(BaseModel):
    cliente_id: str
    proceso_id: int
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None

    @validator('cliente_id')
    def limpiar_cliente_id(cls, v: str) -> str:
        if v:
            return v.strip()  # Elimina espacios al inicio y final
        return v
