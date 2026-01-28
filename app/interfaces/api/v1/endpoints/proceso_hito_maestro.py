from fastapi import APIRouter, Depends, HTTPException, Body, Path
from sqlalchemy.orm import Session
from app.infrastructure.db.database import SessionLocal
from app.infrastructure.db.repositories.proceso_hito_maestro_repository_sql import ProcesoHitoMaestroRepositorySQL
from app.domain.entities.proceso_hito_maestro import ProcesoHitoMaestro


router = APIRouter(prefix="/proceso-hitos", tags=["ProcesoHitoMaestro"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_repo(db: Session = Depends(get_db)):
    return ProcesoHitoMaestroRepositorySQL(db)

@router.post("", summary="Crear relación proceso-hito",
    description="Crea una relación entre un proceso y un hito, especificando sus IDs.")
def crear(
    data: dict = Body(..., example={
        "proceso_id": 1,
        "hito_id": 2
    }),
    repo = Depends(get_repo)
):
    relacion = ProcesoHitoMaestro(
        id=data.get("id"),
        proceso_id=data["proceso_id"],
        hito_id=data["hito_id"]
    )
    return repo.guardar(relacion)

@router.get("", summary="Listar relaciones proceso-hito",
    description="Devuelve todas las relaciones entre procesos e hitos registradas.")
def listar(repo = Depends(get_repo)):
    return {
        "procesoHitos" : repo.listar()
    }


@router.delete("/{id}", summary="Eliminar relación proceso-hito",
    description="Elimina una relación entre un proceso y un hito por su ID.")
def delete(
    id: int = Path(..., description="ID de la relación a eliminar"),
    repo = Depends(get_repo)
):
    resultado = repo.eliminar(id)
    if not resultado:
        raise HTTPException(status_code=404, detail="relacion no encontrada")
    return {"mensaje": "relacion eliminada"}

@router.delete("/hito/{hito_id}", summary="Eliminar relaciones por hito_id",
    description="Elimina todas las relaciones proceso-hito asociadas a un hito específico.")
def delete_por_hito(
    hito_id: int = Path(..., description="ID del hito cuyas relaciones se eliminarán"),
    repo = Depends(get_repo)
):
    eliminados = repo.eliminar_por_hito_id(hito_id)
    if eliminados == 0:
        raise HTTPException(status_code=404, detail="No se encontraron relaciones para el hito indicado")
    return {"mensaje": "relaciones eliminadas", "eliminados": eliminados}
