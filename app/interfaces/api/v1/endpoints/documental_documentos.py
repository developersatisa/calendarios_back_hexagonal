from fastapi import APIRouter, Depends, HTTPException, Query, Path, File, Form, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from app.infrastructure.db.database import SessionLocal
from app.infrastructure.db.repositories.documental_documentos_repository_sql import SqlDocumentalDocumentosRepository
from app.infrastructure.db.repositories.cliente_repository_sql import ClienteRepositorySQL
from app.infrastructure.file_storage.local_file_storage import LocalFileStorage
from app.interfaces.schemas.documental_documentos import (
    DocumentalDocumentosCreate,
    DocumentalDocumentosUpdate,
    DocumentalDocumentosResponse
)
from app.domain.entities.documental_documentos import DocumentalDocumentos
from app.application.use_cases.documental_documentos.crear_documento_categoria import CrearDocumentoCategoriaUseCase

router = APIRouter(prefix="/documental-documentos", tags=["Documental Documentos"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_repo(db: Session = Depends(get_db)):
    return SqlDocumentalDocumentosRepository(session=db)

def get_cliente_repo(db: Session = Depends(get_db)):
    return ClienteRepositorySQL(session=db)

def get_storage():
    return LocalFileStorage()

@router.get("/",
           summary="Listar todos los documentos",
           description="Devuelve todos los documentos registrados en el sistema.")
def listar(
    page: Optional[int] = Query(None, ge=1, description="Página actual"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Cantidad de resultados por página (máximo 10000)"),
    sort_field: Optional[str] = Query(None, description="Campo por el cual ordenar"),
    sort_direction: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Dirección de ordenación: asc o desc"),
    repo = Depends(get_repo)
):
    documental_documentos = repo.listar()
    total = len(documental_documentos)

    if sort_field and documental_documentos and hasattr(documental_documentos[0], sort_field):
        reverse = sort_direction == "desc"

        def sort_key(documento):
            value = getattr(documento, sort_field, None)
            if value is None:
                return ""
            if sort_field == "id":
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return 0
            else:
                return str(value).lower()

        documental_documentos.sort(key=sort_key, reverse=reverse)

    if page is not None and limit is not None:
        start = (page - 1) * limit
        end = start + limit
        documental_documentos = documental_documentos[start:end]

    return {
        "total": total,
        "documental_documentos": documental_documentos
    }

@router.get("/{id}",
           summary="Obtener documento por ID",
           description="Devuelve un documento específico por su ID.")
def obtener_por_id(
    id: int = Path(..., description="ID del documento"),
    repo = Depends(get_repo)
):
    documento = repo.obtener_por_id(id)
    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return documento

@router.post("", summary="Crear documento", description="Crea un nuevo documento en el sistema.")
async def crear_documento(
    cliente_id: str = Form(...),
    categoria_id: int = Form(...),
    nombre_documento: str = Form(...),
    file: UploadFile = File(...),
    repo = Depends(get_repo),
    cliente_repo = Depends(get_cliente_repo),
    storage = Depends(get_storage)
):
    # Leer el contenido del archivo
    contenido = await file.read()

    # Crear el caso de uso
    uc = CrearDocumentoCategoriaUseCase(
        documento_repo=repo,
        cliente_repo=cliente_repo,
        storage=storage
    )

    try:
        return uc.execute(
            cliente_id=cliente_id,
            categoria_id=categoria_id,
            nombre_documento=nombre_documento,
            original_file_name=file.filename,
            content=contenido
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{id}", summary="Actualizar documento", description="Actualiza un documento existente en el sistema.")
async def actualizar(
    id: int,
    nombre_documento: str | None = Form(None),
    file: UploadFile | None = File(None),
    repo = Depends(get_repo),
    storage = Depends(get_storage),
    cliente_repo = Depends(get_cliente_repo)
):
    # Obtener el documento existente
    documento_existente = repo.obtener_por_id(id)
    if not documento_existente:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    # Obtener el cliente para usar su CIF
    cliente = cliente_repo.obtener_por_id(documento_existente.cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # Preparar datos de actualización
    update_data = {}

    if nombre_documento is not None:
        update_data['nombre_documento'] = nombre_documento

    # Si se está actualizando el archivo
    if file is not None:
        try:
            # Leer el nuevo contenido
            nuevo_contenido = await file.read()

            # Generar nuevo nombre de archivo
            import uuid
            import os
            ext = os.path.splitext(file.filename)[1]
            nuevo_stored_name = f"{uuid.uuid4().hex}{ext}"

            # Eliminar archivo anterior usando CIF del cliente
            storage.delete_with_category(
                cliente.cif,  # Usar CIF en lugar de ID del cliente
                str(documento_existente.categoria_id),
                documento_existente.stored_file_name
            )

            # Guardar nuevo archivo usando CIF del cliente
            storage.save_with_category(
                cliente.cif,  # Usar CIF en lugar de ID del cliente
                str(documento_existente.categoria_id),
                nuevo_stored_name,
                nuevo_contenido
            )

            # Actualizar datos del archivo
            update_data['original_file_name'] = file.filename
            update_data['stored_file_name'] = nuevo_stored_name

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al procesar archivo: {str(e)}")

    # Actualizar en la base de datos
    documento_actualizado = repo.actualizar(id, update_data)
    if not documento_actualizado:
        raise HTTPException(status_code=500, detail="Error al actualizar documento")

    return documento_actualizado

@router.delete("/{id}", summary="Eliminar documento", description="Elimina un documento existente en el sistema.")
def eliminar(
    id: int,
    repo = Depends(get_repo),
    storage = Depends(get_storage),
    cliente_repo = Depends(get_cliente_repo)
):
    # Primero obtener el documento para tener acceso a sus datos
    documento = repo.obtener_por_id(id)
    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    # Obtener el cliente para usar su CIF
    cliente = cliente_repo.obtener_por_id(documento.cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    try:
        # Eliminar el archivo físico usando la nueva estructura de carpetas y CIF del cliente
        storage.delete_with_category(
            cliente.cif,  # Usar CIF en lugar de ID del cliente
            str(documento.categoria_id),
            documento.stored_file_name
        )

        # Eliminar el registro de la base de datos
        repo.eliminar(id)
        return {"message": "Documento eliminado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar archivo: {str(e)}")

@router.get("/cliente/{cliente_id}/categoria/{categoria_id}",
           summary="Obtener documentos por cliente y categoría",
           description="Devuelve todos los documentos de un cliente en una categoría específica.")
def obtener_por_cliente_categoria(
    cliente_id: str = Path(..., description="ID del cliente"),
    categoria_id: int = Path(..., description="ID de la categoría"),
    repo = Depends(get_repo)
):
    documentos = repo.obtener_por_cliente_categoria(cliente_id, categoria_id)
    if not documentos:
        return {"total": 0, "documentos": []}

    return {
        "total": len(documentos),
        "documentos": documentos
    }

@router.get("/descargar/{id}",
           summary="Descargar documento",
           description="Descarga un documento específico por su ID.")
async def descargar_documento(
    id: int = Path(..., description="ID del documento"),
    repo = Depends(get_repo),
    storage = Depends(get_storage),
    cliente_repo = Depends(get_cliente_repo)
):
    documento = repo.obtener_por_id(id)
    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    try:
        # Obtener el cliente para usar su CIF
        cliente = cliente_repo.obtener_por_id(documento.cliente_id)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        # Construir la ruta completa del archivo usando el CIF del cliente
        import os
        from app.config import settings

        # Asegurar que FILE_STORAGE_ROOT no termine en barra para evitar problemas con os.path.join
        storage_root = settings.FILE_STORAGE_ROOT.rstrip('/')

        file_path = os.path.join(
            storage_root,
            str(cliente.cif).strip(),# Usar CIF en lugar de ID del cliente y limpiar espacios en blanco
            str(documento.categoria_id),
            documento.stored_file_name
        )

        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            # Agregar información de debug
            debug_info = {
                "error": "Archivo físico no encontrado",
                "ruta_buscada": file_path,
                "storage_root": storage_root,
                "cif_cliente": cliente.cif,
                "cliente_id": documento.cliente_id,
                "categoria_id": documento.categoria_id,
                "stored_file_name": documento.stored_file_name,
                "directorio_existe": os.path.exists(os.path.dirname(file_path))
            }
            raise HTTPException(status_code=404, detail=debug_info)

        # Verificar que el archivo no esté vacío
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise HTTPException(status_code=500, detail="Archivo vacío o corrupto")

        # Detectar el tipo MIME basado en la extensión
        import mimetypes
        mime_type, _ = mimetypes.guess_type(documento.original_file_name)
        if not mime_type:
            mime_type = "application/octet-stream"

        # Usar FileResponse para mejor manejo de archivos
        from fastapi.responses import FileResponse

        return FileResponse(
            path=file_path,
            filename=documento.original_file_name,
            media_type=mime_type,
            headers={
                "Content-Length": str(file_size),
                "Cache-Control": "no-cache",
                "Accept-Ranges": "bytes"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al descargar archivo: {str(e)}")

@router.get("/{id}/verificar",
           summary="Verificar estado del documento",
           description="Verifica el estado del documento y archivo físico para depuración.")
def verificar_documento(
    id: int = Path(..., description="ID del documento"),
    repo = Depends(get_repo),
    storage = Depends(get_storage),
    cliente_repo = Depends(get_cliente_repo)
):
    documento = repo.obtener_por_id(id)
    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    try:
        # Obtener el cliente para usar su CIF
        cliente = cliente_repo.obtener_por_id(documento.cliente_id)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        import os
        from app.config import settings

        # Construir ruta del archivo usando CIF del cliente
        # Asegurar que FILE_STORAGE_ROOT no termine en barra para evitar problemas con os.path.join
        storage_root = settings.FILE_STORAGE_ROOT.rstrip('/')

        file_path = os.path.join(
            storage_root,
            cliente.cif,  # Usar CIF en lugar de ID del cliente
            str(documento.categoria_id),
            documento.stored_file_name
        )

        # Información del documento
        info = {
            "documento": {
                "id": documento.id,
                "cliente_id": documento.cliente_id,
                "cif_cliente": cliente.cif,
                "categoria_id": documento.categoria_id,
                "nombre_documento": documento.nombre_documento,
                "original_file_name": documento.original_file_name,
                "stored_file_name": documento.stored_file_name
            },
            "archivo_fisico": {
                "existe": os.path.exists(file_path),
                "ruta_completa": file_path,
                "tamaño_bytes": os.path.getsize(file_path) if os.path.exists(file_path) else None,
                "permisos": oct(os.stat(file_path).st_mode)[-3:] if os.path.exists(file_path) else None
            },
            "configuracion": {
                "FILE_STORAGE_ROOT": settings.FILE_STORAGE_ROOT,
                "storage_root_limpio": storage_root,
                "directorio_cliente_existe": os.path.exists(os.path.join(storage_root, cliente.cif)),
                "directorio_categoria_existe": os.path.exists(os.path.join(storage_root, cliente.cif, str(documento.categoria_id)))
            }
        }

        return info

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al verificar documento: {str(e)}")
