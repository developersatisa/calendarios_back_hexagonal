from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.api_rol import ApiRol

class ApiRolRepository(ABC):
    @abstractmethod
    def crear(self, email: str, admin: bool = True) -> ApiRol:
        """Crea un nuevo rol de administrador para un email."""
        pass

    @abstractmethod
    def buscar_por_email(self, email: str) -> Optional[ApiRol]:
        """Busca un rol de administrador por email."""
        pass

    @abstractmethod
    def listar(self) -> list[ApiRol]:
        """Devuelve la lista completa de roles de administrador."""
        pass

    @abstractmethod
    def actualizar(self, id: int, admin: bool) -> Optional[ApiRol]:
        """Actualiza el rol de administrador para un email."""
        pass
