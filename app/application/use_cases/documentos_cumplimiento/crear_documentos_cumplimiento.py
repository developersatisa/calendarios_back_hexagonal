# app/application/use_cases/documentos_cumplimiento/crear_documentos_cumplimiento.py

import os
import uuid
from app.domain.entities.documentos_cumplimiento import DocumentosCumplimiento
from app.domain.repositories.documentos_cumplimiento_repository import DocumentosCumplimientoRepositoryPort
from app.domain.repositories.cliente_proceso_hito_cumplimiento_repository import ClienteProcesoHitoCumplimientoRepository
from app.domain.repositories.cliente_proceso_hito_repository import ClienteProcesoHitoRepository
from app.domain.repositories.cliente_proceso_repository import ClienteProcesoRepository
from app.domain.repositories.cliente_repository import ClienteRepository
from app.domain.services.document_storage_port import DocumentStoragePort

class CrearDocumentoCumplimientoUseCase:
    def __init__(
        self,
        documentos_cumplimiento_repo: DocumentosCumplimientoRepositoryPort,
        cumplimiento_repo: ClienteProcesoHitoCumplimientoRepository,
        cph_repo: ClienteProcesoHitoRepository,
        cp_repo: ClienteProcesoRepository,
        cliente_repo: ClienteRepository,
        storage: DocumentStoragePort
    ):
        self.documentos_cumplimiento_repo = documentos_cumplimiento_repo
        self.cumplimiento_repo = cumplimiento_repo
        self.cph_repo = cph_repo
        self.cp_repo = cp_repo
        self.cliente_repo = cliente_repo
        self.storage = storage

    def execute(
        self,
        cumplimiento_id: int,
        nombre_documento: str,
        original_file_name: str,
        content: bytes,
        autor: str = None,
        codSubDepar: str = None
    ) -> DocumentosCumplimiento:
        # 1) Recuperar ClienteProcesoHitoCumplimiento (retorna modelo)
        cumplimiento_model = self.cumplimiento_repo.obtener_por_id(cumplimiento_id)
        if not cumplimiento_model:
            raise ValueError(f"ClienteProcesoHitoCumplimiento {cumplimiento_id} no existe")

        # 2) Con ese cumplimiento.cliente_proceso_hito_id, recuperar ClienteProcesoHito
        cph = self.cph_repo.obtener_por_id(cumplimiento_model.cliente_proceso_hito_id)
        if not cph:
            raise ValueError(f"ClienteProcesoHito {cumplimiento_model.cliente_proceso_hito_id} no existe")

        # 3) Con ese cph.cliente_proceso_id, recuperar ClienteProceso
        cp = self.cp_repo.obtener_por_id(cph.cliente_proceso_id)
        if not cp:
            raise ValueError(f"ClienteProceso {cph.cliente_proceso_id} no existe")

        # 4) Con cp.cliente_id, recuperar Cliente
        cliente = self.cliente_repo.obtener_por_id(cp.cliente_id)
        if not cliente:
            raise ValueError(f"Cliente {cp.cliente_id} no existe")

        cif = cliente.cif

        # 5) Generar nombre único manteniendo extensión
        ext = os.path.splitext(original_file_name)[1]
        stored_file_name = f"{uuid.uuid4().hex}{ext}"

        # 6) Guardar en disco bajo /documentos/calendarios/<CIF>/documentos_cumplimiento/<ID>/
        # Usamos ruta absoluta /documentos para ignorar FILE_STORAGE_ROOT si está definido
        cif_path = os.path.join("/documentos", "calendarios", cif)
        category_path = os.path.join("documentos_cumplimiento", str(cumplimiento_id))

        self.storage.save_with_category(cif_path, category_path, stored_file_name, content)

        # Guardamos en BD la ruta relativa desde el CIF (category + filename)
        # Esto permite que al recuperar recuperemos con cif="documentos/calendarios/<CIF>" y stored_name="<category>/<file>"
        stored_file_relative_path = os.path.join(category_path, stored_file_name)

        # 7) Construir entidad y persistir en BD
        nuevo_doc = DocumentosCumplimiento(
            id=None,
            cumplimiento_id=cumplimiento_id,
            nombre_documento=nombre_documento,
            original_file_name=original_file_name,
            stored_file_name=stored_file_relative_path,
            autor=autor,
            codSubDepar=codSubDepar
        )
        return self.documentos_cumplimiento_repo.create(nuevo_doc)
