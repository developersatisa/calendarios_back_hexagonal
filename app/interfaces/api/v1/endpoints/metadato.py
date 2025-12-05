from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.interfaces.schemas.metadato import MetadatoCreate, MetadatoRead, MetadatoUpdate
from app.infrastructure.db.database import SessionLocal
from app.domain.entities.metadato import Metadato
from app.infrastructure.db.repositories.metadato_repositoy_sql import SQLMetadatoRepository
from app.infrastructure.db.repositories.metadatos_area_repository_sql import SQLMetadatosAreaRepository
from app.application.use_cases.metadato.obtener_metadatos_visibles import ObtenerMetadatosVisibles
from app.infrastructure.services.empleado_ceco_provider import EmpleadoCecoProvider

router = APIRouter(prefix="/metadatos", tags=["Metadatos"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_repo(db: Session = Depends(get_db)):
    return SQLMetadatoRepository(db)

@router.get("/")
def listar_metadatos(
    page: Optional[int] = Query(None, ge=1, description="Página actual"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Cantidad de resultados por página (máximo 10000)"),
    sort_field: Optional[str] = Query(None, description="Campo por el cual ordenar"),
    sort_direction: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Dirección de ordenación: asc o desc"),
    repo = Depends(get_repo)
):
    metadatos = repo.get_all()
    total = len(metadatos)

    # Aplicar ordenación si se especifica
    if sort_field and hasattr(metadatos[0] if metadatos else None, sort_field):
        reverse = sort_direction == "desc"

        # Función de ordenación que maneja valores None
        def sort_key(metadato):
            value = getattr(metadato, sort_field, None)
            if value is None:
                return ""  # Los valores None van al final

            # Manejo especial para diferentes tipos de campos
            if sort_field in ["id", "global_", "activo"]:
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return 0
            else:
                # Para campos de texto (nombre, descripcion, tipo_generacion),
                # convertir a minúsculas para ordenación insensible a mayúsculas
                return str(value).lower()

        metadatos.sort(key=sort_key, reverse=reverse)

    # Aplicar paginación después de ordenar
    if page is not None and limit is not None:
        start = (page - 1) * limit
        end = start + limit
        metadatos = metadatos[start:end]

    return {
        "total": total,
        "metadatos": metadatos
    }

@router.get("/visibles", response_model=list[MetadatoRead])
def obtener_metadatos_visibles(
    email: str = Query(...),
    db: Session = Depends(get_db)
):
    metadato_repo = SQLMetadatoRepository(db)
    area_repo = SQLMetadatosAreaRepository(db)
    ceco_provider = EmpleadoCecoProvider(db)
    use_case = ObtenerMetadatosVisibles(metadato_repo, area_repo, ceco_provider)
    return use_case.execute(email)

@router.get("/{metadato_id}", response_model=MetadatoRead)
def obtener_metadato(metadato_id: int, repo = Depends(get_repo)):
    result = repo.get_by_id(metadato_id)
    if not result:
        raise HTTPException(status_code=404, detail="Metadato no encontrado")
    return result

@router.post("", response_model=MetadatoRead)
def crear_metadato(payload: MetadatoCreate, repo = Depends(get_repo)):
    return repo.save(payload)

@router.put("/{metadato_id}", response_model=MetadatoRead)
def actualizar_metadato(
    metadato_id: int,
    payload: MetadatoUpdate,
    repo = Depends(get_repo)
):
    metadato = Metadato(
        id=metadato_id,
        nombre=payload.nombre,
        descripcion=payload.descripcion or "",
        tipo_generacion=payload.tipo_generacion,
        global_=payload.global_,
        activo=payload.activo
    )
    return repo.update(metadato_id, metadato)

@router.delete("/{metadato_id}", status_code=204)
def eliminar_metadato(metadato_id: int, repo = Depends(get_repo)):
    repo.delete(metadato_id)
