from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional
from app.infrastructure.db.database import SessionLocal
from app.infrastructure.db.repositories.persona_repository_sql import PersonaRepositorySQL
from app.interfaces.schemas.persona import PersonaResponse


from app.infrastructure.db.repositories.api_rol_repository_sql import SqlApiRolRepository

router = APIRouter(prefix="/personas", tags=["Persona"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_repo(db: Session = Depends(get_db)):
    return PersonaRepositorySQL(db)

def _enrich_persona_with_admin_status(persona, db: Session):
    if persona and persona.email:
        # Populate admin status and id_api_rol from new ApiRol repository
        repo_rol = SqlApiRolRepository(db)
        rol = repo_rol.buscar_por_email(persona.email)

        if rol:
            persona.admin = rol.admin
            persona.id_api_rol = rol.id
        else:
            persona.admin = False
            persona.id_api_rol = None

    return persona

@router.get("", summary="Listar personas",
    description="Devuelve la lista completa de personas desde la tabla externa, con paginación y ordenación.")
def listar_personas(
    page: Optional[int] = Query(None, ge=1, description="Página actual"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Cantidad de resultados por página"),
    sort_field: Optional[str] = Query(None, description="Campo por el cual ordenar"),
    sort_direction: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Dirección de ordenación: asc o desc"),
    repo: PersonaRepositorySQL = Depends(get_repo),
    db: Session = Depends(get_db)
):
    personas = repo.listar()
    total = len(personas)

    # Aplicar ordenación si se especifica
    if sort_field and hasattr(personas[0] if personas else None, sort_field):
        reverse = sort_direction == "desc"

        def sort_key(persona):
            value = getattr(persona, sort_field, None)
            if value is None:
                return ""
            return str(value).lower()

        personas.sort(key=sort_key, reverse=reverse)

    # Aplicar paginación
    if page is not None and limit is not None:
        start = (page - 1) * limit
        end = start + limit
        personas = personas[start:end]

    # Enrich with admin status only for the returning page

    repo_rol = SqlApiRolRepository(db)

    for p in personas:
        if p.email:
            # Get Admin Status and ID
            rol = repo_rol.buscar_por_email(p.email)
            if rol:
                p.admin = rol.admin
                p.id_api_rol = rol.id
            else:
                p.admin = False
                p.id_api_rol = None

    return {
        "total": total,
        "personas": personas
    }

@router.get("/email/{email}", response_model=PersonaResponse, summary="Buscar persona por email")
def buscar_por_email(
    email: str = Path(..., description="Email de la persona"),
    repo: PersonaRepositorySQL = Depends(get_repo),
    db: Session = Depends(get_db)
):
    persona = repo.buscar_por_email(email)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")

    return _enrich_persona_with_admin_status(persona, db)

@router.get("/nif/{nif}", response_model=PersonaResponse, summary="Buscar persona por NIF")
def buscar_por_nif(
    nif: str = Path(..., description="NIF de la persona"),
    repo: PersonaRepositorySQL = Depends(get_repo),
    db: Session = Depends(get_db)
):
    persona = repo.buscar_por_nif(nif)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")

    return _enrich_persona_with_admin_status(persona, db)
