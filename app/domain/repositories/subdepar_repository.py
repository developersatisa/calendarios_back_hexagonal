from abc import ABC, abstractmethod
from app.domain.entities.subdepar import Subdepar
from typing import List, Any, Dict, Optional

class SubdeparRepository(ABC):

    @abstractmethod
    def listar(self):
        pass

    @abstractmethod
    def obtener_por_id(self, id: int):
        pass
