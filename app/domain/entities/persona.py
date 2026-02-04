from dataclasses import dataclass
from typing import Optional

@dataclass
class Persona:
    NIF: str
    Nombre: str
    Apellido1: str
    Apellido2: Optional[str] = None
    email: Optional[str] = None
    admin: bool = False
    id_api_rol: Optional[int] = None
