from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.persona import Persona

class PersonaRepository(ABC):
    @abstractmethod
    def listar(self) -> List[Persona]:
        pass

    @abstractmethod
    def buscar_por_email(self, email: str) -> Optional[Persona]:
        pass

    @abstractmethod
    def buscar_por_nif(self, nif: str) -> Optional[Persona]:
        pass
