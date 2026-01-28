from abc import ABC, abstractmethod
from typing import List
from app.domain.entities.documental_documentos import DocumentalDocumentos

class DocumentalDocumentosRepository(ABC):

    @abstractmethod
    def guardar(self, doc: DocumentalDocumentos) -> DocumentalDocumentos:
        pass

    @abstractmethod
    def actualizar(self, doc: DocumentalDocumentos) -> DocumentalDocumentos:
        pass

    @abstractmethod
    def eliminar(self, cat_id: int) -> None:
        pass

    @abstractmethod
    def obtener_por_id(self, doc_id: int) -> DocumentalDocumentos | None:
        pass

    @abstractmethod
    def listar(self) -> List[DocumentalDocumentos]:
        pass

    @abstractmethod
    def obtener_por_cliente_categoria(self, cliente_id: str, categoria_id: int) -> List[DocumentalDocumentos]:
        pass
