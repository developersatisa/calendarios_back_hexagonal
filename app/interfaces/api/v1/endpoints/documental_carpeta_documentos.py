import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Path
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.infrastructure.db.database import SessionLocal
from app.infrastructure.db.repositories.documental_carpeta_documentos_repository_sql import DocumentalCarpetaDocumentosRepositorySQL
from app.interfaces.schemas.documental_carpeta_documentos import (
    DocumentalCarpetaDocumentosUpdate
)
from app.application.use_cases.documental_carpeta_documentos.crear_documental_carpeta_documento import CrearDocumentalCarpetaDocumentoUseCase
from app.domain.services.document_storage_port import DocumentStoragePort
from app.infrastructure.file_storage.local_file_storage import LocalFileStorage

router = APIRouter(prefix="/documental-carpeta-documentos", tags=["Documental Carpeta Documentos"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_repo(db: Session = Depends(get_db)):
    return DocumentalCarpetaDocumentosRepositorySQL(db)

def get_storage() -> DocumentStoragePort:
    return LocalFileStorage()

@router.get("", summary="Listar todos los documentos",
    description="Devuelve todos los documentos registrados en el sistema.")
def get_all(repo: DocumentalCarpetaDocumentosRepositorySQL = Depends(get_repo)):
    return repo.get_all()

@router.get("/descargar/{id}", summary="Descargar documento por ID",
    description="Descarga el archivo físico de un documento específico según su ID.")
def descargar_documento(
    id: int = Path(..., description="ID del documento a descargar"),
    repo: DocumentalCarpetaDocumentosRepositorySQL = Depends(get_repo),
    storage: DocumentStoragePort = Depends(get_storage)
):
    # 1) Obtener el documento de la BD
    doc = repo.get_by_id(id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    # 2) Obtener el CIF del cliente asociado a la carpeta
    cif_cliente = repo.get_cliente_cif_by_carpeta_id(doc.carpeta_id)
    if not cif_cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado para esta carpeta")

    # 3) Construir la ruta base del CIF (igual que en el use case de crear)
    cif_path = os.path.join("/documentos", "calendarios", cif_cliente)

    # 4) Leer el archivo del almacenamiento
    try:
        contenido = storage.get(cif_path, doc.stored_file_name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Archivo no encontrado en el almacenamiento")
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"Error al leer el archivo: {str(e)}")

    # 5) Determinar el tipo MIME
    nombre_archivo = doc.original_file_name or doc.stored_file_name
    ext = os.path.splitext(nombre_archivo)[1].lower()
    mime_types = {
        ".pdf": "application/pdf",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xls": "application/vnd.ms-excel",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".txt": "text/plain",
        ".csv": "text/csv",
        ".zip": "application/zip",
    }
    media_type = mime_types.get(ext, "application/octet-stream")

    return Response(
        content=contenido,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{nombre_archivo}"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )


@router.get("/{id}", summary="Obtener documento por ID",
    description="Devuelve un documento específico según su ID.")
def get_by_id(
    id: int = Path(..., description="ID del documento a consultar"),
    repo: DocumentalCarpetaDocumentosRepositorySQL = Depends(get_repo)
):
    entity = repo.get_by_id(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return entity

@router.get("/carpeta/{carpeta_id}", summary="Listar documentos por carpeta",
    description="Devuelve todos los documentos de una carpeta específica, con paginación y ordenación.")
def get_by_carpeta(
    carpeta_id: int = Path(..., description="ID de la carpeta a consultar"),
    page: Optional[int] = Query(None, ge=1, description="Página actual"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Cantidad de resultados por página"),
    sort_field: Optional[str] = Query("fecha_creacion", description="Campo por el cual ordenar"),
    sort_direction: Optional[str] = Query("desc", regex="^(asc|desc)$", description="Dirección de ordenación: asc o desc"),
    repo: DocumentalCarpetaDocumentosRepositorySQL = Depends(get_repo)
):
    # Valores por defecto para la paginación si no se proporcionan
    current_page = page if page else 1
    current_limit = limit if limit else 100
    skip = (current_page - 1) * current_limit

    documentos = repo.get_by_carpeta_id(carpeta_id, skip=skip, limit=current_limit, sort_field=sort_field, sort_direction=sort_direction)
    total = repo.count_by_carpeta_id(carpeta_id)

    return {
        "total": total,
        "page": current_page,
        "limit": current_limit,
        "documentos": documentos
    }

@router.post("/upload/{carpeta_id}", summary="Subir documento a carpeta",
    description="Sube un archivo a una carpeta específica.")
async def upload_documento(
    carpeta_id: int = Path(..., description="ID de la carpeta destino"),
    autor: str = Form(...),
    codSubDepar: Optional[str] = Form(None),
    file: UploadFile = File(...),
    repo: DocumentalCarpetaDocumentosRepositorySQL = Depends(get_repo),
    storage: DocumentStoragePort = Depends(get_storage)
):
    use_case = CrearDocumentalCarpetaDocumentoUseCase(repo, storage)

    content = await file.read()

    try:
        return use_case.execute(
            carpeta_id=carpeta_id,
            original_file_name=file.filename,
            content=content,
            autor=autor,
            codSubDepar=codSubDepar
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("", summary="Crear documento",
    description="Crea un documento subiendo un archivo con los datos del formulario.")
async def create(
    carpeta_id: int = Form(...),
    autor: str = Form(...),
    codSubDepar: Optional[str] = Form(None),
    file: UploadFile = File(...),
    repo: DocumentalCarpetaDocumentosRepositorySQL = Depends(get_repo),
    storage: DocumentStoragePort = Depends(get_storage)
):
    use_case = CrearDocumentalCarpetaDocumentoUseCase(repo, storage)

    content = await file.read()

    try:
        return use_case.execute(
            carpeta_id=carpeta_id,
            original_file_name=file.filename,
            content=content,
            autor=autor,
            codSubDepar=codSubDepar
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{id}", summary="Actualizar documento",
    description="Actualiza un documento existente por su ID.")
def update(
    id: int = Path(..., description="ID del documento a actualizar"),
    payload: DocumentalCarpetaDocumentosUpdate = None,
    repo: DocumentalCarpetaDocumentosRepositorySQL = Depends(get_repo)
):
    current = repo.get_by_id(id)
    if not current:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    if payload.nombre_documento is not None:
        current.nombre_documento = payload.nombre_documento

    updated = repo.update(id, current)
    return updated

@router.delete("/{id}", summary="Eliminar documento",
    description="Elimina un documento existente por su ID.")
def delete(
    id: int = Path(..., description="ID del documento a eliminar"),
    repo: DocumentalCarpetaDocumentosRepositorySQL = Depends(get_repo)
):
    success = repo.delete(id)
    if not success:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return {"mensaje": "Documento eliminado"}
