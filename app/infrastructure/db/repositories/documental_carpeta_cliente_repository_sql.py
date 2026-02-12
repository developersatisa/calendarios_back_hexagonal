from typing import List, Optional
from sqlalchemy.orm import Session
from app.domain.entities.documental_carpeta_cliente import DocumentalCarpetaCliente
from app.domain.repositories.documental_carpeta_cliente_repository import DocumentalCarpetaClienteRepository
from app.infrastructure.db.models.documental_carpeta_cliente_model import DocumentalCarpetaClienteModel
from app.infrastructure.db.models.documental_carpeta_proceso_model import DocumentalCarpetaProcesoModel

class DocumentalCarpetaClienteRepositorySQL(DocumentalCarpetaClienteRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[DocumentalCarpetaCliente]:
        models = self.db.query(DocumentalCarpetaClienteModel).all()
        return [self._to_entity(model) for model in models]

    def get_by_id(self, id: int) -> Optional[DocumentalCarpetaCliente]:
        model = self.db.query(DocumentalCarpetaClienteModel).filter(DocumentalCarpetaClienteModel.id == id).first()
        return self._to_entity(model) if model else None

    def get_by_cliente_id(self, cliente_id: str) -> List[DocumentalCarpetaCliente]:
        results = (
            self.db.query(DocumentalCarpetaClienteModel, DocumentalCarpetaProcesoModel.nombre)
            .join(DocumentalCarpetaProcesoModel, DocumentalCarpetaClienteModel.carpeta_id == DocumentalCarpetaProcesoModel.id)
            .filter(
                DocumentalCarpetaClienteModel.cliente_id == cliente_id,
                DocumentalCarpetaProcesoModel.eliminado == False
            )
            .all()
        )
        return [self._to_entity(row[0], nombre_carpeta=row[1]) for row in results]

    def create(self, entity: DocumentalCarpetaCliente) -> DocumentalCarpetaCliente:
        model = DocumentalCarpetaClienteModel(
            cliente_id=entity.cliente_id,
            proceso_id=entity.proceso_id,
            carpeta_id=entity.carpeta_id
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def update(self, id: int, entity: DocumentalCarpetaCliente) -> Optional[DocumentalCarpetaCliente]:
        model = self.db.query(DocumentalCarpetaClienteModel).filter(DocumentalCarpetaClienteModel.id == id).first()
        if not model:
            return None

        model.cliente_id = entity.cliente_id
        model.proceso_id = entity.proceso_id
        model.carpeta_id = entity.carpeta_id

        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def delete(self, id: int) -> bool:
        model = self.db.query(DocumentalCarpetaClienteModel).filter(DocumentalCarpetaClienteModel.id == id).first()
        if not model:
            return False
        self.db.delete(model)
        self.db.commit()
        return True

    def _to_entity(self, model: DocumentalCarpetaClienteModel, nombre_carpeta: str = None) -> DocumentalCarpetaCliente:
        return DocumentalCarpetaCliente(
            id=model.id,
            cliente_id=model.cliente_id,
            proceso_id=model.proceso_id,
            carpeta_id=model.carpeta_id,
            nombre_carpeta=nombre_carpeta
        )
