from dataclasses import dataclass

@dataclass
class ApiRol:
    id: int
    email: str
    admin: bool
