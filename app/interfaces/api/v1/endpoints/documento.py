# app/interfaces/api/v1/endpoints/documento.py

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.infrastructure.db.database import SessionLocal

# Puertos de repositorio
from app.domain.repositories.documento_repository import DocumentoRepositoryPort as DocumentoRepository
from app.domain.repositories.cliente_proceso_hito_repository import ClienteProcesoHitoRepository
from app.domain.repositories.cliente_proceso_repository import ClienteProcesoRepository
from app.domain.repositories.cliente_repository import ClienteRepository

# Implementaciones concretas
from app.infrastructure.db.repositories.documento_repository_sql import SQLDocumentoRepository
from app.infrastructure.db.repositories.cliente_proceso_hito_repository_sql import ClienteProcesoHitoRepositorySQL
from app.infrastructure.db.repositories.cliente_proceso_repository_sql import ClienteProcesoRepositorySQL
from app.infrastructure.db.repositories.cliente_repository_sql import ClienteRepositorySQL

# Puerto de almacenamiento
from app.domain.services.document_storage_port import DocumentStoragePort
from app.infrastructure.file_storage.local_file_storage import LocalFileStorage

# Casos de uso
from app.application.use_cases.documento.crear_documento import CrearDocumentoUseCase
from app.application.use_cases.documento.actualizar_documento import ActualizarDocumentoUseCase
from app.application.use_cases.documento.eliminar_documento import EliminarDocumentoUseCase

# Esquema de salida
from app.interfaces.schemas.documento import DocumentoResponse

router = APIRouter(prefix="/documentos", tags=["Documentos"])

# — Dependencias de BD —
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_repo(db: Session = Depends(get_db)) -> DocumentoRepository:
    return SQLDocumentoRepository(db)

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

@router.get("", response_model=list[DocumentoResponse])
def listar_documentos(
    repo_doc: DocumentoRepository = Depends(get_repo)
):
    return repo_doc.get_all()

@router.get("/{id}", response_model=DocumentoResponse)
def obtener_documento(
    id: int,
    repo_doc: DocumentoRepository = Depends(get_repo)
):
    doc = repo_doc.get_by_id(id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return doc

@router.post("", response_model=DocumentoResponse)
async def crear_documento(
    cliente_proceso_hito_id: int = Form(...),
    nombre_documento: str = Form(...),
    file: UploadFile = File(...),
    repo_doc: DocumentoRepository          = Depends(get_repo),
    repo_cph: ClienteProcesoHitoRepository = Depends(get_repo_cph),
    repo_cp: ClienteProcesoRepository      = Depends(get_repo_cp),
    repo_cliente: ClienteRepository        = Depends(get_repo_cliente),
    storage: DocumentStoragePort           = Depends(get_storage),
):
    uc = CrearDocumentoUseCase(
        documento_repo=repo_doc,
        cph_repo=repo_cph,
        cp_repo=repo_cp,
        cliente_repo=repo_cliente,
        storage=storage,
    )
    contenido = await file.read()
    try:
        return uc.execute(
            cliente_proceso_hito_id=cliente_proceso_hito_id,
            nombre_documento=nombre_documento,
            original_file_name=file.filename,
            content=contenido
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{id}", response_model=DocumentoResponse)
async def actualizar_documento(
    id: int,
    nombre_documento: str | None      = Form(None),     # ← opcional
    file: UploadFile  | None          = File(None),
    repo_doc: DocumentoRepository     = Depends(get_repo),
    repo_cph: ClienteProcesoHitoRepository = Depends(get_repo_cph),
    repo_cp: ClienteProcesoRepository      = Depends(get_repo_cp),
    repo_cliente: ClienteRepository        = Depends(get_repo_cliente),
    storage: DocumentStoragePort           = Depends(get_storage),
):
    uc = ActualizarDocumentoUseCase(repo_doc, repo_cph, repo_cp, repo_cliente, storage)

    nuevo_nombre_doc        = nombre_documento
    nuevo_original_file     = file.filename if file else None
    nuevo_contenido         = await file.read() if file else None

    try:
        return uc.execute(
            id_documento              = id,
            nuevo_nombre_documento    = nuevo_nombre_doc,
            nuevo_original_file_name  = nuevo_original_file,
            nuevo_content             = nuevo_contenido,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{id}", status_code=204)
def eliminar_documento(
    id: int,
    repo_doc: DocumentoRepository          = Depends(get_repo),
    repo_cph: ClienteProcesoHitoRepository = Depends(get_repo_cph),
    repo_cp: ClienteProcesoRepository      = Depends(get_repo_cp),
    repo_cliente: ClienteRepository        = Depends(get_repo_cliente),
    storage: DocumentStoragePort           = Depends(get_storage),
):
    uc = EliminarDocumentoUseCase(
        documento_repo=repo_doc,
        cph_repo=repo_cph,
        cp_repo=repo_cp,
        cliente_repo=repo_cliente,
        storage=storage,
    )
    try:
        uc.execute(id_documento=id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
