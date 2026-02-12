from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.documental_carpeta_documentos import DocumentalCarpetaDocumentos

class DocumentalCarpetaDocumentosRepository(ABC):
    @abstractmethod
    def get_all(self) -> List[DocumentalCarpetaDocumentos]:
        pass

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[DocumentalCarpetaDocumentos]:
        pass

    @abstractmethod
    def get_by_carpeta_id(self, carpeta_id: int, skip: int = 0, limit: int = 100, sort_field: str = "fecha_creacion", sort_direction: str = "desc") -> List[DocumentalCarpetaDocumentos]:
        pass

    @abstractmethod
    def count_by_carpeta_id(self, carpeta_id: int) -> int:
        pass

    @abstractmethod
    def get_cliente_cif_by_carpeta_id(self, carpeta_id: int) -> Optional[str]:
        pass

    @abstractmethod
    def create(self, entity: DocumentalCarpetaDocumentos) -> DocumentalCarpetaDocumentos:
        pass

    @abstractmethod
    def update(self, id: int, entity: DocumentalCarpetaDocumentos) -> Optional[DocumentalCarpetaDocumentos]:
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        pass
