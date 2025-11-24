# app/infrastructure/db/repositories/documentos_cumplimiento_repository_sql.py

from sqlalchemy.orm import Session
from typing import List

from app.domain.entities.documentos_cumplimiento import DocumentosCumplimiento
from app.domain.repositories.documentos_cumplimiento_repository import DocumentosCumplimientoRepositoryPort
from app.infrastructure.db.models.documentos_cumplimiento_model import DocumentoCumplimientoModel

class SQLDocumentoCumplimientoRepository(DocumentosCumplimientoRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> List[DocumentosCumplimiento]:
        modelos = self.session.query(DocumentoCumplimientoModel).all()
        return [self._to_entity(m) for m in modelos]

    def get_by_cumplimiento_id(self, cumplimiento_id: int) -> List[DocumentosCumplimiento]:
        modelos = (
            self.session
            .query(DocumentoCumplimientoModel)
            .filter_by(cumplimiento_id=cumplimiento_id)
            .all()
        )
        return [self._to_entity(m) for m in modelos]

    def get_by_id(self, doc_id: int) -> DocumentosCumplimiento | None:
        m = (
            self.session
            .query(DocumentoCumplimientoModel)
            .filter_by(id=doc_id)
            .first()
        )
        return self._to_entity(m) if m else None

    def create(self, doc: DocumentosCumplimiento) -> DocumentosCumplimiento:
        modelo = DocumentoCumplimientoModel(
            cumplimiento_id=doc.cumplimiento_id,
            nombre_documento=doc.nombre_documento,
            original_file_name=doc.original_file_name,
            stored_file_name=doc.stored_file_name
        )
        self.session.add(modelo)
        self.session.commit()
        self.session.refresh(modelo)
        return self._to_entity(modelo)

    def update(self, doc: DocumentosCumplimiento) -> DocumentosCumplimiento:
        modelo = (
            self.session
            .query(DocumentoCumplimientoModel)
            .filter_by(id=doc.id)
            .first()
        )
        if not modelo:
            raise ValueError(f"DocumentoCumplimiento {doc.id} no existe")
        # Actualizamos ambos campos de nombre
        modelo.nombre_documento = doc.nombre_documento
        modelo.original_file_name = doc.original_file_name
        modelo.stored_file_name = doc.stored_file_name
        self.session.commit()
        self.session.refresh(modelo)
        return self._to_entity(modelo)

    def delete(self, doc_id: int) -> None:
        (
            self.session
            .query(DocumentoCumplimientoModel)
            .filter_by(id=doc_id)
            .delete()
        )
        self.session.commit()

    def _to_entity(self, m: DocumentoCumplimientoModel) -> DocumentosCumplimiento:
        return DocumentosCumplimiento(
            id=m.id,
            cumplimiento_id=m.cumplimiento_id,
            nombre_documento=m.nombre_documento,
            original_file_name=m.original_file_name,
            stored_file_name=m.stored_file_name
        )
