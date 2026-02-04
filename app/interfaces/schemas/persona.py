from pydantic import BaseModel
from typing import Optional

class PersonaBase(BaseModel):
    NIF: str
    Nombre: str
    Apellido1: str
    Apellido2: Optional[str] = None
    email: Optional[str] = None

class PersonaResponse(PersonaBase):
    admin: bool
    id_api_rol: Optional[int] = None
    pass

    class Config:
        from_attributes = True
