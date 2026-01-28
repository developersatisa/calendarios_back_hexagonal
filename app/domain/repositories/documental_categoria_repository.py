from abc import ABC, abstractmethod
from typing import List
from app.domain.entities.documental_categoria import DocumentalCategoria

class DocumentalCategoriaRepository(ABC):

    @abstractmethod
    def guardar(self, doc: DocumentalCategoria) -> DocumentalCategoria:
        pass

    @abstractmethod
    def actualizar(self, doc: DocumentalCategoria) -> DocumentalCategoria:
        pass

    @abstractmethod
    def eliminar(self, cat_id: int) -> None:
        pass

    @abstractmethod
    def obtener_por_id(self, doc_id: int) -> DocumentalCategoria | None:
        pass

    @abstractmethod
    def obtener_por_cliente(self, cliente_id: str) -> List[DocumentalCategoria]:
        pass

    @abstractmethod
    def listar(self) -> List[DocumentalCategoria]:
        pass
