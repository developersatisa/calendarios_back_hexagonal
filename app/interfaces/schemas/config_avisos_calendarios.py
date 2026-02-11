from typing import Optional
from pydantic import BaseModel, Field, validator
from datetime import time, datetime

class ConfigAvisoCalendarioBase(BaseModel):
    cliente_id: str = Field(..., max_length=9, description="ID identifying the client")
    codSubDepar: str = Field(..., max_length=10, description="Department code (codSubDepar)")

    # Vence Hoy
    aviso_vence_hoy: bool = False
    temporicidad_vence_hoy: Optional[int] = None
    tiempo_vence_hoy: Optional[int] = None
    hora_vence_hoy: Optional[time] = None

    # Proximo Vencimiento
    aviso_proximo_vencimiento: bool = False
    temporicidad_proximo_vencimiento: Optional[int] = None
    tiempo_proximo_vencimiento: Optional[int] = None
    hora_proximo_vencimiento: Optional[time] = None
    dias_proximo_vencimiento: Optional[int] = None

    # Vencido
    aviso_vencido: bool = False
    temporicidad_vencido: Optional[int] = None
    tiempo_vencido: Optional[int] = None
    hora_vencido: Optional[time] = None

    # Global Config
    config_global: Optional[bool] = False
    temporicidad_global: Optional[int] = None
    tiempo_global: Optional[int] = None
    hora_global: Optional[time] = None

    @validator('hora_vence_hoy', 'hora_proximo_vencimiento', 'hora_vencido', 'hora_global', pre=True)
    def parse_time(cls, v):
        if isinstance(v, str):
            try:
                return datetime.strptime(v, '%H:%M:%S').time()
            except ValueError:
                return datetime.strptime(v, '%H:%M').time()
        return v

class ConfigAvisoCalendarioCreate(ConfigAvisoCalendarioBase):
    pass

class ConfigAvisoCalendarioUpdate(BaseModel):
    # All fields optional for update
    cliente_id: Optional[str] = Field(None, max_length=9)
    codSubDepar: Optional[str] = Field(None, max_length=10)

    aviso_vence_hoy: Optional[bool] = None
    temporicidad_vence_hoy: Optional[int] = None
    tiempo_vence_hoy: Optional[int] = None
    hora_vence_hoy: Optional[time] = None

    aviso_proximo_vencimiento: Optional[bool] = None
    temporicidad_proximo_vencimiento: Optional[int] = None
    tiempo_proximo_vencimiento: Optional[int] = None
    hora_proximo_vencimiento: Optional[time] = None
    dias_proximo_vencimiento: Optional[int] = None

    aviso_vencido: Optional[bool] = None
    temporicidad_vencido: Optional[int] = None
    tiempo_vencido: Optional[int] = None
    hora_vencido: Optional[time] = None

    config_global: Optional[bool] = None
    temporicidad_global: Optional[int] = None
    tiempo_global: Optional[int] = None
    hora_global: Optional[time] = None

    @validator('hora_vence_hoy', 'hora_proximo_vencimiento', 'hora_vencido', 'hora_global', pre=True)
    def parse_time(cls, v):
        if isinstance(v, str):
            try:
                return datetime.strptime(v, '%H:%M:%S').time()
            except ValueError:
                try:
                    return datetime.strptime(v, '%H:%M').time()
                except ValueError:
                    raise ValueError('Invalid time format. Use HH:MM:SS or HH:MM')
        return v

class ConfigAvisoCalendarioResponse(ConfigAvisoCalendarioBase):
    id: int

    class Config:
        orm_mode = True
