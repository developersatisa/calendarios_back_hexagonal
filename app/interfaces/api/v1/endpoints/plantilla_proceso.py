from fastapi import APIRouter, Depends, HTTPException, Body, Path
from sqlalchemy.orm import Session
from app.infrastructure.db.database import SessionLocal
from app.infrastructure.db.repositories.plantilla_proceso_repository_sql import PlantillaProcesoRepositorySQL

from app.domain.entities.plantilla_proceso import PlantillaProceso

router = APIRouter(prefix="/plantilla-procesos", tags=["PlantillaProceso"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_repo(db: Session = Depends(get_db)):
    return PlantillaProcesoRepositorySQL(db)

@router.post("", summary="Crear relación plantilla-proceso",
    description="Crea una relación entre una plantilla y un proceso especificando sus IDs.")
def crear(
    data: dict = Body(..., example={
        "plantilla_id": 1,
        "proceso_id": 2
    }),
    repo = Depends(get_repo)
):
     relacion = PlantillaProceso(
        proceso_id=data["proceso_id"],
        plantilla_id=data["plantilla_id"]
    )
     return repo.guardar(relacion)


@router.get("", summary="Listar relaciones plantilla-proceso",
    description="Devuelve todas las relaciones entre plantillas y procesos.")
def listar(repo = Depends(get_repo)):
    return {
        "plantillaProcesos": repo.listar()
    }
@router.get("/plantilla/{id_plantilla}", summary="Procesos por plantilla",
    description="Devuelve todos los procesos asociados a una plantilla específica.")
def procesos_por_plantilla(
    id_plantilla: int = Path(..., description="ID de la plantilla a consultar"),
    repo = Depends(get_repo)
):
    return repo.listar_procesos_por_plantilla(id_plantilla)

@router.delete("/{id}", summary="Eliminar relación plantilla-proceso",
    description="Elimina una relación específica entre una plantilla y un proceso por su ID.")
def eliminar(
    id: int = Path(..., description="ID de la relación a eliminar"),
    repo = Depends(get_repo)
):
    ok = repo.eliminar(id)
    if not ok:
        raise HTTPException(status_code=404, detail="Relación no encontrada")
    return {"mensaje": "Relación eliminada"}

@router.delete("/plantilla/{id_plantilla}", summary="Eliminar todas las relaciones de una plantilla",
    description="Elimina todas las relaciones entre una plantilla y sus procesos asociados.")
def eliminar_por_plantilla(
    id_plantilla: int = Path(..., description="ID de la plantilla cuyas relaciones quieres eliminar"),
    repo = Depends(get_repo)
):
    ok = repo.eliminar_por_plantilla(id_plantilla)
    if not ok:
        raise HTTPException(status_code=404, detail="No se encontraron relaciones para la plantilla")
    return {"mensaje": "Relaciones eliminadas"}
