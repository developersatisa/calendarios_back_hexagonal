from dataclasses import dataclass

@dataclass
class ApiCliente:
    id: int
    nombre_cliente: str
    hashed_key: str
    activo: bool
    email: str
