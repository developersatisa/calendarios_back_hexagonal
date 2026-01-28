from abc import ABC, abstractmethod
from typing import Optional

class UserMappingService(ABC):
    """Servicio para mapear usuarios con sus clientes API"""
    
    @abstractmethod
    def get_api_cliente_id_by_email(self, email: str) -> Optional[int]:
        """Obtiene el id_api_cliente basado en el email del usuario"""
        pass