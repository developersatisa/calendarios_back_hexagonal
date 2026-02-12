import os
import uuid
from datetime import datetime
from app.domain.entities.documental_carpeta_documentos import DocumentalCarpetaDocumentos
from app.domain.repositories.documental_carpeta_documentos_repository import DocumentalCarpetaDocumentosRepository
from app.infrastructure.db.repositories.documental_carpeta_documentos_repository_sql import DocumentalCarpetaDocumentosRepositorySQL
from app.domain.services.document_storage_port import DocumentStoragePort

class CrearDocumentalCarpetaDocumentoUseCase:
    def __init__(
        self,
        repo: DocumentalCarpetaDocumentosRepositorySQL,
        storage: DocumentStoragePort
    ):
        self.repo = repo
        self.storage = storage

    def execute(
        self,
        carpeta_id: int,
        original_file_name: str,
        content: bytes,
        autor: str,
        codSubDepar: str = None
    ) -> DocumentalCarpetaDocumentos:
        # 1. Obtener CIF del cliente asociado a la carpeta
        cif_cliente = self.repo.get_cliente_cif_by_carpeta_id(carpeta_id)
        if not cif_cliente:
            raise ValueError("Carpeta o Cliente no encontrado")

        # 2. Generar nombre único para el archivo almacenado
        ext = os.path.splitext(original_file_name)[1]
        unique_filename = f"{uuid.uuid4().hex}{ext}"

        # 3. Definir rutas de almacenamiento
        # Ruta base CIF: /documentos/calendarios/<CIF>
        cif_path = os.path.join("/documentos", "calendarios", cif_cliente)
        # Ruta categoría: gestor_documental/<ID_CARPETA>
        category_path = os.path.join("gestor_documental", str(carpeta_id))

        # 4. Guardar archivo físico usando save_with_category
        self.storage.save_with_category(cif_path, category_path, unique_filename, content)

        # 5. Construir stored_file_name para la base de datos (relativo a cif_path, o absoluto según se requiera)
        # En el caso de cumplimiento se guardaba "documentos_cumplimiento/<ID>/<uuid>"
        # Aquí seguiremos el mismo patrón: "gestor_documental/<ID_CARPETA>/<uuid>"
        # OJO: El código anterior en endpoint usaba ruta ABSOLUTA en stored_file_name.
        # "file_path = os.path.join(storage_dir, file.filename)" donde storage_dir era absoluto.
        # Para ser consistentes con el cambio solicitado ("hacerlo como al subir un documento en cumplimientos"),
        # deberíamos guardar la ruta relativa que permita reconstruir la ubicación junto con el CIF base.

        # PERO, el modelo actual y la lógica anterior guardaban la ruta COMPLETA o relativa al root.
        # Si cambiamos a usar DocumentStoragePort con `save_with_category`, la lógica de `get` luego esperará
        # base + stored_name.
        # En `documentos_cumplimiento` se guarda: os.path.join(category_path, stored_file_name) -> "documentos_cumplimiento/123/uuid.pdf"

        # Vamos a replicar ese comportamiento.
        stored_file_relative_path = os.path.join(category_path, unique_filename)

        # Si se requiere la ruta absoluta completa para retrocompatibilidad directa sin cambiar el `get`,
        # tendríamos que ver cómo se lee. El endpoint `upload` anterior guardaba:
        # /documentos/calendarios/{cif}/gestor_documental/{id}/{filename}

        # Voy a asumir que debemos guardar la ruta relativa igual que en cumplimiento para uniformidad,
        # PERO si el sistema actual de lectura espera ruta absoluta, esto podría romper lectura.
        # Revisando `DocumentalCarpetaDocumentosRepositorySQL`, no hay lógica de lectura de fichero, solo de entidad.
        # Quien lea el fichero usará `stored_file_name`.

        # Si el usuario pide "hacerlo como al subir un documento en cumplimientos", usaré esa lógica.
        # No obstante, para asegurar que funcione con el sistema de ficheros local si alguien usa `open(stored_file_name)`,
        # esto podría ser un cambio.
        # En `documentos_cumplimiento.py` (descargar), se hace:
        # cif_path = ...
        # storage.get(cif_path, doc.stored_file_name)

        # Por tanto, guardaré la ruta relativa "gestor_documental/{id}/{uuid}".

        entity = DocumentalCarpetaDocumentos(
            id=0,
            carpeta_id=carpeta_id,
            nombre_documento=original_file_name, # Usamos el nombre original como nombre del documento
            original_file_name=original_file_name,
            stored_file_name=stored_file_relative_path,
            autor=autor,
            codSubDepar=codSubDepar,
            eliminado=False,
            fecha_creacion=datetime.now(),
            fecha_actualizacion=datetime.now()
        )

        return self.repo.create(entity)
