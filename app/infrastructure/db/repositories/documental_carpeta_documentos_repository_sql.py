from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.domain.entities.documental_carpeta_documentos import DocumentalCarpetaDocumentos
from app.domain.repositories.documental_carpeta_documentos_repository import DocumentalCarpetaDocumentosRepository
from app.infrastructure.db.models.documental_carpeta_documentos_model import DocumentalCarpetaDocumentosModel
from app.infrastructure.db.models.documental_carpeta_cliente_model import DocumentalCarpetaClienteModel
from app.infrastructure.db.models.cliente_model import ClienteModel
from sqlalchemy import text

class DocumentalCarpetaDocumentosRepositorySQL(DocumentalCarpetaDocumentosRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[DocumentalCarpetaDocumentos]:
        models = self.db.query(DocumentalCarpetaDocumentosModel).filter(DocumentalCarpetaDocumentosModel.eliminado == False).all()
        return [self._to_entity(model) for model in models]

    def get_by_id(self, id: int) -> Optional[DocumentalCarpetaDocumentos]:
        model = self.db.query(DocumentalCarpetaDocumentosModel).filter(DocumentalCarpetaDocumentosModel.id == id, DocumentalCarpetaDocumentosModel.eliminado == False).first()
        return self._to_entity(model) if model else None

    def get_by_carpeta_id(self, carpeta_id: int, skip: int = 0, limit: int = 100, sort_field: str = "fecha_creacion", sort_direction: str = "desc") -> List[DocumentalCarpetaDocumentos]:
        # Mapeo de campos de ordenación seguros
        sort_mapping = {
            "nombre_documento": "d.nombre_documento",
            "original_file_name": "d.original_file_name",
            "autor": "autor",
            "fecha_creacion": "d.fecha_creacion",
            "fecha_actualizacion": "d.fecha_actualizacion"
        }

        order_col = sort_mapping.get(sort_field, "d.fecha_creacion")
        direction = "DESC" if sort_direction and sort_direction.lower() == "desc" else "ASC"

        query_str = f"""
            SELECT d.id, d.carpeta_id, d.nombre_documento, d.original_file_name, d.stored_file_name,
                   CASE
                       WHEN p.Nombre IS NOT NULL THEN ISNULL(p.Nombre, '') + ' ' + ISNULL(p.Apellido1, '') + ' ' + ISNULL(p.Apellido2, '')
                       ELSE d.autor
                   END as autor,
                   d.codSubDepar, sd.nombre as departamento,
                   d.eliminado, d.fecha_creacion, d.fecha_actualizacion
            FROM documental_carpeta_documentos d
            LEFT JOIN [BI DW RRHH DEV].dbo.Persona p ON p.Numeross = d.autor
            LEFT JOIN subdepar sd ON sd.codSubDePar = d.codSubDepar
            WHERE d.carpeta_id = :carpeta_id AND d.eliminado = 0
            ORDER BY {order_col} {direction}
            OFFSET :skip ROWS FETCH NEXT :limit ROWS ONLY
        """

        query = text(query_str)
        results = self.db.execute(query, {"carpeta_id": carpeta_id, "skip": skip, "limit": limit}).fetchall()

        documents = []
        for row in results:
            doc = DocumentalCarpetaDocumentos(
                id=row.id,
                carpeta_id=row.carpeta_id,
                nombre_documento=row.nombre_documento,
                original_file_name=row.original_file_name,
                stored_file_name=row.stored_file_name,
                autor=row.autor,
                codSubDepar=row.codSubDepar,
                departamento=row.departamento,
                eliminado=row.eliminado,
                fecha_creacion=row.fecha_creacion,
                fecha_actualizacion=row.fecha_actualizacion
            )
            documents.append(doc)
        return documents

    def count_by_carpeta_id(self, carpeta_id: int) -> int:
        query = text("SELECT COUNT(*) FROM documental_carpeta_documentos WHERE carpeta_id = :carpeta_id AND eliminado = 0")
        result = self.db.execute(query, {"carpeta_id": carpeta_id}).scalar()
        return result or 0

    def get_cliente_cif_by_carpeta_id(self, carpeta_id: int) -> Optional[str]:
        result = (
            self.db.query(ClienteModel.cif)
            .join(DocumentalCarpetaClienteModel, ClienteModel.idcliente == DocumentalCarpetaClienteModel.cliente_id)
            .filter(DocumentalCarpetaClienteModel.id == carpeta_id)
            .first()
        )
        return result[0] if result else None

    def create(self, entity: DocumentalCarpetaDocumentos) -> DocumentalCarpetaDocumentos:
        model = DocumentalCarpetaDocumentosModel(
            carpeta_id=entity.carpeta_id,
            nombre_documento=entity.nombre_documento,
            original_file_name=entity.original_file_name,
            stored_file_name=entity.stored_file_name,
            autor=entity.autor,
            codSubDepar=entity.codSubDepar,
            eliminado=entity.eliminado
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def update(self, id: int, entity: DocumentalCarpetaDocumentos) -> Optional[DocumentalCarpetaDocumentos]:
        model = self.db.query(DocumentalCarpetaDocumentosModel).filter(DocumentalCarpetaDocumentosModel.id == id).first()
        if not model:
            return None

        if entity.nombre_documento is not None:
             model.nombre_documento = entity.nombre_documento
        if entity.eliminado is not None:
             model.eliminado = entity.eliminado

        model.fecha_actualizacion = datetime.now()

        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def delete(self, id: int) -> bool:
        model = self.db.query(DocumentalCarpetaDocumentosModel).filter(DocumentalCarpetaDocumentosModel.id == id).first()
        if not model:
            return False

        # Soft delete: update eliminado field and timestamp
        model.eliminado = True
        model.fecha_actualizacion = datetime.now()

        self.db.commit()
        return True

    def _to_entity(self, model: DocumentalCarpetaDocumentosModel) -> DocumentalCarpetaDocumentos:
        return DocumentalCarpetaDocumentos(
            id=model.id,
            carpeta_id=model.carpeta_id,
            nombre_documento=model.nombre_documento,
            original_file_name=model.original_file_name,
            stored_file_name=model.stored_file_name,
            autor=model.autor,
            codSubDepar=model.codSubDepar,
            eliminado=model.eliminado,
            fecha_creacion=model.fecha_creacion,
            fecha_actualizacion=model.fecha_actualizacion
        )
