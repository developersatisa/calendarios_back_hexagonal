from pydantic import BaseModel, field_validator
from datetime import date, time
from typing import List, Optional

class CumplimientoMasivoRequest(BaseModel):
    cliente_proceso_hito_ids: List[int]
    fecha: date
    hora: Optional[time] = None
    observacion: Optional[str] = None
    usuario: Optional[str] = None

    @field_validator('cliente_proceso_hito_ids', mode='before')
    @classmethod
    def clean_ids(cls, v):
        """Limpia espacios y convierte strings a enteros"""
        if isinstance(v, list):
            cleaned = []
            for item in v:
                if isinstance(item, str):
                    cleaned.append(int(item.strip()))
                else:
                    cleaned.append(int(item))
            return cleaned
        return v
