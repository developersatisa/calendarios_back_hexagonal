from abc import ABC, abstractmethod
from typing import List, Optional, Any
from app.domain.entities.cliente import Cliente

class ClienteRepository(ABC):

    @abstractmethod
    def listar(self) -> List[Cliente]:
        pass

    @abstractmethod
    def buscar_por_nombre(self, nombre: str) -> List[Cliente]:
        pass

    @abstractmethod
    def buscar_por_cif(self, cif: str) -> Optional[Cliente]:
        pass

    @abstractmethod
    def obtener_por_id(self, id: str) -> Optional[Cliente]:
        """Obtiene un cliente por su ID"""
        pass

    @abstractmethod
    def listar_por_hito_id(self, hito_id: int) -> List[Cliente]:
        """Lista clientes que tienen un hito específico en su calendario"""
        pass

    @abstractmethod
    def listar_empresas_usuario(self, email: str) -> List[Cliente]:
        """Lista empresas a las que pertenece un usuario"""
        pass

    @abstractmethod
    def listar_con_departamentos(self, limit: int, offset: int, search: Optional[str] = None, sort_field: Optional[str] = None, sort_direction: str = "asc") -> tuple[List[Any], int]:
        """Lista clientes que tienen departamentos, con paginación y búsqueda"""
        pass
