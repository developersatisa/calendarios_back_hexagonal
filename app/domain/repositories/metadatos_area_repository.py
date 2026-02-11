from abc import ABC, abstractmethod
from typing import List
from app.domain.entities.metadatos_area import MetadatosArea

class MetadatosAreaRepository(ABC):

    @abstractmethod
    def get_all(self) -> List[MetadatosArea]: pass

    @abstractmethod
    def get_by_id(self, id: int) -> MetadatosArea | None: pass

    @abstractmethod
    def save(self, metadatos_area: MetadatosArea) -> MetadatosArea: pass

    @abstractmethod
    def delete(self, id: int) -> None: pass

    @abstractmethod
    def delete_by_metadato_id(self, id_metadato: int) -> int: pass

    @abstractmethod
    def get_by_cod_subdepar_list(self, codigos_subdepar: List[str]) -> List[MetadatosArea]:
        pass
