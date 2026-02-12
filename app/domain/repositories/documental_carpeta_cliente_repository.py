from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.documental_carpeta_cliente import DocumentalCarpetaCliente

class DocumentalCarpetaClienteRepository(ABC):
    @abstractmethod
    def get_all(self) -> List[DocumentalCarpetaCliente]:
        pass

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[DocumentalCarpetaCliente]:
        pass

    @abstractmethod
    def get_by_cliente_id(self, cliente_id: str) -> List[DocumentalCarpetaCliente]:
        pass

    @abstractmethod
    def create(self, entity: DocumentalCarpetaCliente) -> DocumentalCarpetaCliente:
        pass

    @abstractmethod
    def update(self, id: int, entity: DocumentalCarpetaCliente) -> Optional[DocumentalCarpetaCliente]:
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        pass
