# app/interfaces/api/v1/endpoints/documentos_cumplimiento.py

import io
import os
import zipfile
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from app.infrastructure.db.database import SessionLocal

# Puertos de repositorio
from app.domain.repositories.documentos_cumplimiento_repository import DocumentosCumplimientoRepositoryPort as DocumentosCumplimientoRepository
from app.domain.repositories.cliente_proceso_hito_cumplimiento_repository import ClienteProcesoHitoCumplimientoRepository
from app.domain.repositories.cliente_proceso_hito_repository import ClienteProcesoHitoRepository
from app.domain.repositories.cliente_proceso_repository import ClienteProcesoRepository
from app.domain.repositories.cliente_repository import ClienteRepository

# Implementaciones concretas
from app.infrastructure.db.repositories.documentos_cumplimiento_repository_sql import SQLDocumentoCumplimientoRepository
from app.infrastructure.db.repositories.cliente_proceso_hito_cumplimiento_repository_sql import ClienteProcesoHitoCumplimientoRepositorySQL
from app.infrastructure.db.repositories.cliente_proceso_hito_repository_sql import ClienteProcesoHitoRepositorySQL
from app.infrastructure.db.repositories.cliente_proceso_repository_sql import ClienteProcesoRepositorySQL
from app.infrastructure.db.repositories.cliente_repository_sql import ClienteRepositorySQL

# Puerto de almacenamiento
from app.domain.services.document_storage_port import DocumentStoragePort
from app.infrastructure.file_storage.local_file_storage import LocalFileStorage

# Casos de uso
from app.application.use_cases.documentos_cumplimiento.crear_documentos_cumplimiento import CrearDocumentoCumplimientoUseCase

# Esquema de salida
from app.interfaces.schemas.documentos_cumplimiento import DocumentosCumplimientoResponse
from app.interfaces.api.security.auth import get_current_user

router = APIRouter(prefix="/documentos-cumplimiento", tags=["Documentos Cumplimiento"])

# — Dependencias de BD —
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_repo(db: Session = Depends(get_db)) -> DocumentosCumplimientoRepository:
    return SQLDocumentoCumplimientoRepository(db)

def get_repo_cumplimiento(db: Session = Depends(get_db)) -> ClienteProcesoHitoCumplimientoRepository:
    return ClienteProcesoHitoCumplimientoRepositorySQL(db)

def get_repo_cph(db: Session = Depends(get_db)) -> ClienteProcesoHitoRepository:
    return ClienteProcesoHitoRepositorySQL(db)

def get_repo_cp(db: Session = Depends(get_db)) -> ClienteProcesoRepository:
    return ClienteProcesoRepositorySQL(db)

def get_repo_cliente(db: Session = Depends(get_db)) -> ClienteRepository:
    return ClienteRepositorySQL(db)

# — Dependencia de almacenamiento de ficheros —
def get_storage() -> DocumentStoragePort:
    return LocalFileStorage()

# — Endpoints —

@router.get("", response_model=list[DocumentosCumplimientoResponse])
def listar_documentos_cumplimiento(
    repo_doc: DocumentosCumplimientoRepository = Depends(get_repo)
):
    return repo_doc.get_all()

@router.get("/cumplimiento/{cumplimiento_id}", response_model=list[DocumentosCumplimientoResponse])
def obtener_documentos_por_cumplimiento(
    cumplimiento_id: int,
    repo_doc: DocumentosCumplimientoRepository = Depends(get_repo)
):
    """
    Obtiene todos los documentos asociados a un cumplimiento específico.
    """
    documentos = repo_doc.get_by_cumplimiento_id(cumplimiento_id)
    return documentos

@router.get("/{id}", response_model=DocumentosCumplimientoResponse)
def obtener_documento_cumplimiento(
    id: int,
    repo_doc: DocumentosCumplimientoRepository = Depends(get_repo)
):
    doc = repo_doc.get_by_id(id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento cumplimiento no encontrado")
    return doc

@router.post("", response_model=DocumentosCumplimientoResponse)
async def crear_documento_cumplimiento(
    cumplimiento_id: int = Form(...),
    autor: str = Form(...),
    codSubDepar: str = Form(...),
    file: UploadFile = File(...),
    repo_doc: DocumentosCumplimientoRepository = Depends(get_repo),
    repo_cumplimiento: ClienteProcesoHitoCumplimientoRepository = Depends(get_repo_cumplimiento),
    repo_cph: ClienteProcesoHitoRepository = Depends(get_repo_cph),
    repo_cp: ClienteProcesoRepository = Depends(get_repo_cp),
    repo_cliente: ClienteRepository = Depends(get_repo_cliente),
    storage: DocumentStoragePort = Depends(get_storage),
    user: dict = Depends(get_current_user)
):

    uc = CrearDocumentoCumplimientoUseCase(
        documentos_cumplimiento_repo=repo_doc,
        cumplimiento_repo=repo_cumplimiento,
        cph_repo=repo_cph,
        cp_repo=repo_cp,
        cliente_repo=repo_cliente,
        storage=storage,
    )
    contenido = await file.read()
    try:
        return uc.execute(
            cumplimiento_id=cumplimiento_id,
            nombre_documento=file.filename,
            original_file_name=file.filename,
            content=contenido,
            autor=autor,
            codSubDepar=codSubDepar
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/cumplimiento/{cumplimiento_id}/descargar")
async def descargar_documentos_cumplimiento(
    cumplimiento_id: int,
    repo_doc: DocumentosCumplimientoRepository = Depends(get_repo),
    repo_cumplimiento: ClienteProcesoHitoCumplimientoRepository = Depends(get_repo_cumplimiento),
    repo_cph: ClienteProcesoHitoRepository = Depends(get_repo_cph),
    repo_cp: ClienteProcesoRepository = Depends(get_repo_cp),
    repo_cliente: ClienteRepository = Depends(get_repo_cliente),
    storage: DocumentStoragePort = Depends(get_storage),
):
    """
    Descarga los documentos de un cumplimiento en un archivo ZIP.
    Incluso si hay un solo documento, se descarga como ZIP para consistencia del front.
    """
    # 1) Obtener todos los documentos del cumplimiento
    documentos = repo_doc.get_by_cumplimiento_id(cumplimiento_id)

    if not documentos:
        raise HTTPException(status_code=404, detail="No se encontraron documentos para este cumplimiento")

    # 2) Obtener el CIF del cliente siguiendo la cadena
    cumplimiento_model = repo_cumplimiento.obtener_por_id(cumplimiento_id)
    if not cumplimiento_model:
        raise HTTPException(status_code=404, detail="Cumplimiento no encontrado")

    cph = repo_cph.obtener_por_id(cumplimiento_model.cliente_proceso_hito_id)
    if not cph:
        raise HTTPException(status_code=404, detail="ClienteProcesoHito no encontrado")

    cp = repo_cp.obtener_por_id(cph.cliente_proceso_id)
    if not cp:
        raise HTTPException(status_code=404, detail="ClienteProceso no encontrado")

    cliente = repo_cliente.obtener_por_id(cp.cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    cif = cliente.cif

    # 3) Crear un ZIP (siempre, incluso para un solo archivo)
    zip_buffer = io.BytesIO()
    nombres_usados = set()

    try:
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            archivos_incluidos = 0
            for doc in documentos:
                try:
                    contenido = storage.get(cif, doc.stored_file_name)
                    if not contenido:
                        continue

                    # Gestionar nombre del archivo y evitar duplicados en el ZIP
                    nombre_base = doc.original_file_name or doc.stored_file_name
                    nombre_archivo = nombre_base
                    contador = 1

                    while nombre_archivo in nombres_usados:
                        nombre_sin_ext, ext = os.path.splitext(nombre_base)
                        nombre_archivo = f"{nombre_sin_ext}_{contador}{ext}"
                        contador += 1

                    nombres_usados.add(nombre_archivo)
                    zip_file.writestr(nombre_archivo, contenido)
                    archivos_incluidos += 1
                except FileNotFoundError:
                    continue
                except Exception:
                    continue

        if archivos_incluidos == 0:
            raise HTTPException(status_code=404, detail="No se pudieron recuperar los archivos del almacenamiento")

        zip_buffer.seek(0)

        # Log para depuración
        print(f"DEBUG: Generado ZIP para cumplimiento {cumplimiento_id}. Archivos: {archivos_incluidos}. Tamaño: {zip_buffer.getbuffer().nbytes} bytes")

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="documentos_cumplimiento_{cumplimiento_id}.zip"',
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al crear el archivo ZIP: {str(e)}")
