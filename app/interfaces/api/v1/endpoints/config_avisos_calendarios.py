from typing import List
from fastapi import APIRouter, Depends, HTTPException, Body, Path
from sqlalchemy.orm import Session
from app.infrastructure.db.database import SessionLocal
from app.infrastructure.db.repositories.config_avisos_calendarios_repository_sql import ConfigAvisoCalendarioRepositorySQL
from app.domain.entities.config_avisos_calendarios import ConfigAvisoCalendario
from app.interfaces.schemas.config_avisos_calendarios import (
    ConfigAvisoCalendarioCreate,
    ConfigAvisoCalendarioUpdate,
    ConfigAvisoCalendarioResponse
)

router = APIRouter(prefix="/config-avisos-calendarios", tags=["Configuración Avisos Calendarios"])

def get_repo():
    db = SessionLocal()
    try:
        yield ConfigAvisoCalendarioRepositorySQL(db)
    finally:
        db.close()

@router.get("", summary="Listar configuraciones de avisos", response_model=List[ConfigAvisoCalendarioResponse])
def listar(repo: ConfigAvisoCalendarioRepositorySQL = Depends(get_repo)):
    return repo.listar()

@router.get("/{id}", summary="Obtener configuración por ID", response_model=ConfigAvisoCalendarioResponse)
def obtener(id: int = Path(..., description="ID de la configuración"), repo: ConfigAvisoCalendarioRepositorySQL = Depends(get_repo)):
    config = repo.obtener_por_id(id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    return config

@router.get("/subdepar/{cod_sub_depar}", summary="Obtener configuración por Código Sub-Departamento", response_model=ConfigAvisoCalendarioResponse)
def obtener_por_codigo(cod_sub_depar: str, repo: ConfigAvisoCalendarioRepositorySQL = Depends(get_repo)):
    config = repo.obtener_por_cod_sub_depar(cod_sub_depar)
    if not config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    return config

@router.post("", summary="Crear configuración de avisos", response_model=ConfigAvisoCalendarioResponse)
def crear(
    config_in: ConfigAvisoCalendarioCreate,
    repo: ConfigAvisoCalendarioRepositorySQL = Depends(get_repo)
):
    try:
        # Convert Pydantic model to Domain Entity
        nuevo_config = ConfigAvisoCalendario(**config_in.dict())
        return repo.guardar(nuevo_config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{id}", summary="Actualizar configuración de avisos", response_model=ConfigAvisoCalendarioResponse)
def actualizar(
    id: int,
    config_in: ConfigAvisoCalendarioUpdate,
    repo: ConfigAvisoCalendarioRepositorySQL = Depends(get_repo)
):
    # Filter out None values to only update provided fields
    update_data = config_in.dict(exclude_unset=True)
    actualizado = repo.actualizar(id, update_data)
    if not actualizado:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    return actualizado

@router.delete("/{id}", summary="Eliminar configuración de avisos")
def eliminar(id: int, repo: ConfigAvisoCalendarioRepositorySQL = Depends(get_repo)):
    if not repo.eliminar(id):
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    return {"message": "Configuración eliminada exitosamente"}
