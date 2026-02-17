from pydantic import BaseModel, field_validator
from datetime import date, time
from typing import List, Optional

class UpdateFechaMasivoRequest(BaseModel):
    hito_id: int
    empresa_ids: List[int]
    nueva_fecha: date
    nueva_hora: Optional[time] = None
    fecha_desde: date
    fecha_hasta: date | None = None


    @field_validator('empresa_ids', mode='before')
    @classmethod
    def clean_empresa_ids(cls, v):
        """Limpia espacios y convierte strings a enteros"""
        if isinstance(v, list):
            cleaned = []
            for item in v:
                if isinstance(item, str):
                    # Eliminar espacios y convertir a entero
                    cleaned.append(int(item.strip()))
                else:
                    cleaned.append(int(item))
            return cleaned
        return v
