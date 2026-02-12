from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.documental_carpeta_proceso import DocumentalCarpetaProceso

class DocumentalCarpetaProcesoRepository(ABC):
    @abstractmethod
    def get_all(self) -> List[DocumentalCarpetaProceso]:
        pass

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[DocumentalCarpetaProceso]:
        pass

    @abstractmethod
    def get_by_proceso_id(self, proceso_id: int) -> List[DocumentalCarpetaProceso]:
        pass

    @abstractmethod
    def create(self, entity: DocumentalCarpetaProceso) -> DocumentalCarpetaProceso:
        pass

    @abstractmethod
    def update(self, id: int, entity: DocumentalCarpetaProceso) -> Optional[DocumentalCarpetaProceso]:
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        pass
