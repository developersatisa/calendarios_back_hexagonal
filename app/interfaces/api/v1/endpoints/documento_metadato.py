from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.infrastructure.db.database import SessionLocal
from app.infrastructure.db.repositories.documento_metadato_repository_sql import SqlDocumentoMetadatoRepository
from app.infrastructure.db.repositories.documento_repository_sql import SQLDocumentoRepository
from app.infrastructure.db.repositories.metadato_repositoy_sql import SQLMetadatoRepository
from app.application.services.documentos_metadato_service import DocumentoMetadatoService
from app.interfaces.schemas.documento_metadato import DocumentoMetadatoCreate, DocumentoMetadatoUpdate, DocumentoMetadatoOut
from app.domain.entities.documento_metadato import DocumentoMetadato

router = APIRouter(prefix="/documento-metadatos", tags=["DocumentoMetadato"])
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_service(db: Session = Depends(get_db)) -> DocumentoMetadatoService:
    repo = SqlDocumentoMetadatoRepository(db)
    doc_repo = SQLDocumentoRepository(db)
    meta_repo = SQLMetadatoRepository(db)
    return DocumentoMetadatoService(repo, doc_repo, meta_repo)

@router.post("", response_model=DocumentoMetadatoOut)
def crear(data: DocumentoMetadatoCreate, service: DocumentoMetadatoService = Depends(get_service)):
    return service.crear(DocumentoMetadato(id=None, **data.dict()))

@router.get("", response_model=List[DocumentoMetadatoOut])
def listar(service: DocumentoMetadatoService = Depends(get_service)):
    return service.listar()

@router.get("/{id}", response_model=DocumentoMetadatoOut)
def obtener(id: int, service: DocumentoMetadatoService = Depends(get_service)):
    doc = service.obtener_por_id(id)
    if not doc:
        raise HTTPException(status_code=404, detail="No encontrado")
    return doc

@router.put("", response_model=DocumentoMetadatoOut)
def actualizar(data: DocumentoMetadatoUpdate, service: DocumentoMetadatoService = Depends(get_service)):
    return service.actualizar(DocumentoMetadato(**data.dict()))

@router.delete("/{id}")
def eliminar(id: int, service: DocumentoMetadatoService = Depends(get_service)):
    service.eliminar(id)
    return {"detail": "Eliminado"}
