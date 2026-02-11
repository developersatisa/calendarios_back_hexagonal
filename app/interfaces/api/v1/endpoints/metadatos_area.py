from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.infrastructure.db.database import SessionLocal
from app.domain.repositories.metadatos_area_repository import MetadatosAreaRepository
from app.interfaces.schemas.metadatos_area import MetadatosAreaCreate, MetadatosAreaRead
from app.infrastructure.db.repositories.metadatos_area_repository_sql import SQLMetadatosAreaRepository
from app.infrastructure.db.repositories.metadato_repositoy_sql import SQLMetadatoRepository
from app.application.use_cases.metadatos_area.crear_metadatos_area import CrearMetadatosAreaUseCase

router = APIRouter(prefix="/metadatos-area", tags=["Metadatos Area"])
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_repo(db: Session = Depends(get_db)):
    return SQLMetadatosAreaRepository(db)

def get_repo_metadato(db: Session = Depends(get_db)):
    return SQLMetadatoRepository(db)

@router.get("", response_model=list[MetadatosAreaRead])
def listar(repo: MetadatosAreaRepository = Depends(get_repo)):
    return repo.get_all()

@router.get("/{id}", response_model=MetadatosAreaRead)
def obtener(id: int, repo: MetadatosAreaRepository = Depends(get_repo)):
    result = repo.get_by_id(id)
    if not result:
        raise HTTPException(status_code=404, detail="No encontrado")
    return result

@router.post("", response_model=MetadatosAreaRead)
def crear(payload: MetadatosAreaCreate, repo: MetadatosAreaRepository = Depends(get_repo), repo_metadato: SQLMetadatoRepository = Depends(get_repo_metadato)):

    use_case = CrearMetadatosAreaUseCase(repo, repo_metadato)
    try:
        result = use_case.execute(
            id_metadato=payload.id_metadato,
            codSubDepar=payload.codSubDepar
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{id}", status_code=204)
def eliminar(id: int, repo: MetadatosAreaRepository = Depends(get_repo)):
    repo.delete(id)

@router.delete("/metadato/{id_metadato}")
def eliminar_por_metadato(id_metadato: int, repo: MetadatosAreaRepository = Depends(get_repo)):
    count = repo.delete_by_metadato_id(id_metadato)
    return {"message": f"Se eliminaron {count} registros con id_metadato {id_metadato}"}
