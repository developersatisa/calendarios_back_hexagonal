# app/application/use_cases/documental_documentos/crear_documento_categoria.py

import os
import uuid
from datetime import datetime
from app.domain.entities.documental_documentos import DocumentalDocumentos
from app.domain.repositories.documental_documentos_repository import DocumentalDocumentosRepository
from app.domain.repositories.cliente_repository import ClienteRepository
from app.domain.services.document_storage_port import DocumentStoragePort

class CrearDocumentoCategoriaUseCase:
    def __init__(
        self,
        documento_repo: DocumentalDocumentosRepository,
        cliente_repo: ClienteRepository,
        storage: DocumentStoragePort
    ):
        self.documento_repo = documento_repo
        self.cliente_repo = cliente_repo
        self.storage = storage

    def execute(
        self,
        cliente_id: str,
        categoria_id: int,
        nombre_documento: str,
        original_file_name: str,
        content: bytes
    ) -> DocumentalDocumentos:
        # 1) Verificar que el cliente existe
        cliente = self.cliente_repo.obtener_por_id(cliente_id)
        if not cliente:
            raise ValueError(f"Cliente {cliente_id} no existe")

        cif = cliente.cif

        # 2) Generar nombre único manteniendo extensión
        ext = os.path.splitext(original_file_name)[1]
        stored_file_name = f"{uuid.uuid4().hex}{ext}"

        # 3) Guardar en disco bajo <ROOT>/<CIF>/<CATEGORIA_ID>/
        # Usamos el método save_with_category del storage
        self.storage.save_with_category(cif, str(categoria_id), stored_file_name, content)

        # 4) Construir entidad y persistir en BD
        nuevo_doc = DocumentalDocumentos(
            id=None,
            cliente_id=cliente_id,
            categoria_id=categoria_id,
            nombre_documento=nombre_documento,
            original_file_name=original_file_name,
            stored_file_name=stored_file_name,
            fecha_creacion=datetime.now()
        )

        return self.documento_repo.guardar(nuevo_doc)
