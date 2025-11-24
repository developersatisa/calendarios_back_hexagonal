from abc import ABC, abstractmethod
from typing import List
from app.domain.entities.documentos_cumplimiento import DocumentosCumplimiento

class DocumentosCumplimientoRepositoryPort(ABC):
    @abstractmethod
    def create(self, doc: DocumentosCumplimiento) -> DocumentosCumplimiento:
        pass

    @abstractmethod
    def update(self, doc: DocumentosCumplimiento) -> DocumentosCumplimiento:
        pass

    @abstractmethod
    def delete(self, doc_id: int) -> None:
        pass

    @abstractmethod
    def get_by_id(self, doc_id: int) -> DocumentosCumplimiento | None:
        pass

    @abstractmethod
    def get_all(self) -> List[DocumentosCumplimiento]:
        pass

    @abstractmethod
    def get_by_cumplimiento_id(self, cumplimiento_id: int) -> List[DocumentosCumplimiento]:
        pass
