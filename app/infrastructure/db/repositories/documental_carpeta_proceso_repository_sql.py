from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.domain.entities.documental_carpeta_proceso import DocumentalCarpetaProceso
from app.domain.repositories.documental_carpeta_proceso_repository import DocumentalCarpetaProcesoRepository
from app.infrastructure.db.models.documental_carpeta_proceso_model import DocumentalCarpetaProcesoModel
from app.infrastructure.db.models.documental_carpeta_cliente_model import DocumentalCarpetaClienteModel
from app.infrastructure.db.models.documental_carpeta_documentos_model import DocumentalCarpetaDocumentosModel
from app.infrastructure.db.models.cliente_proceso_model import ClienteProcesoModel

class DocumentalCarpetaProcesoRepositorySQL(DocumentalCarpetaProcesoRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[DocumentalCarpetaProceso]:
        models = self.db.query(DocumentalCarpetaProcesoModel).filter(DocumentalCarpetaProcesoModel.eliminado == False).all()
        return [self._to_entity(model) for model in models]

    def get_by_id(self, id: int) -> Optional[DocumentalCarpetaProceso]:
        model = self.db.query(DocumentalCarpetaProcesoModel).filter(DocumentalCarpetaProcesoModel.id == id, DocumentalCarpetaProcesoModel.eliminado == False).first()
        return self._to_entity(model) if model else None

    def get_by_proceso_id(self, proceso_id: int) -> List[DocumentalCarpetaProceso]:
        models = self.db.query(DocumentalCarpetaProcesoModel).filter(DocumentalCarpetaProcesoModel.proceso_id == proceso_id, DocumentalCarpetaProcesoModel.eliminado == False).all()
        return [self._to_entity(model) for model in models]

    def create(self, entity: DocumentalCarpetaProceso) -> DocumentalCarpetaProceso:
        model = DocumentalCarpetaProcesoModel(
            proceso_id=entity.proceso_id,
            nombre=entity.nombre,
            descripcion=entity.descripcion,
            eliminado=entity.eliminado
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)

        # Buscar clientes con este proceso y crear la carpeta para ellos
        clientes_procesos = self.db.query(ClienteProcesoModel).filter(
            ClienteProcesoModel.proceso_id == model.proceso_id
        ).all()

        for cp in clientes_procesos:
            # Verificar si ya existe (para evitar duplicados aunque debería ser nuevo)
            exists = self.db.query(DocumentalCarpetaClienteModel).filter(
                DocumentalCarpetaClienteModel.cliente_id == cp.cliente_id,
                DocumentalCarpetaClienteModel.carpeta_id == model.id
            ).first()

            if not exists:
                carpeta_cliente = DocumentalCarpetaClienteModel(
                    cliente_id=cp.cliente_id,
                    proceso_id=model.proceso_id,
                    carpeta_id=model.id
                )
                self.db.add(carpeta_cliente)

        self.db.commit()

        return self._to_entity(model)

    def update(self, id: int, entity: DocumentalCarpetaProceso) -> Optional[DocumentalCarpetaProceso]:
        model = self.db.query(DocumentalCarpetaProcesoModel).filter(DocumentalCarpetaProcesoModel.id == id).first()
        if not model:
            return None

        # Actualizar campos
        model.nombre = entity.nombre
        if entity.descripcion is not None:
             model.descripcion = entity.descripcion
        if entity.eliminado is not None:
             model.eliminado = entity.eliminado

        model.fecha_actualizacion = datetime.now()

        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def delete(self, id: int) -> bool:
        model = self.db.query(DocumentalCarpetaProcesoModel).filter(DocumentalCarpetaProcesoModel.id == id).first()
        if not model:
            return False

        # Soft delete Proceso Folder
        model.eliminado = True
        model.fecha_actualizacion = datetime.now()

        # Soft delete associated documents
        # 1. Get all client folders for this process folder
        client_folders = self.db.query(DocumentalCarpetaClienteModel).filter(DocumentalCarpetaClienteModel.carpeta_id == id).all()
        client_folder_ids = [f.id for f in client_folders]

        # 2. Update all documents in those folders
        if client_folder_ids:
            self.db.query(DocumentalCarpetaDocumentosModel).filter(
                DocumentalCarpetaDocumentosModel.carpeta_id.in_(client_folder_ids)
            ).update(
                {
                    DocumentalCarpetaDocumentosModel.eliminado: True,
                    DocumentalCarpetaDocumentosModel.fecha_actualizacion: datetime.now()
                },
                synchronize_session=False
            )

        self.db.commit()
        return True

    def _to_entity(self, model: DocumentalCarpetaProcesoModel) -> DocumentalCarpetaProceso:
        return DocumentalCarpetaProceso(
            id=model.id,
            proceso_id=model.proceso_id,
            nombre=model.nombre,
            descripcion=model.descripcion,
            eliminado=model.eliminado,
            fecha_creacion=model.fecha_creacion,
            fecha_actualizacion=model.fecha_actualizacion
        )
