# app/infrastructure/db/repositories/plantilla_proceso_repository_sql.py

from app.domain.entities.plantilla_proceso import PlantillaProceso
from app.domain.repositories.plantilla_proceso_repository import PlantillaProcesoRepository
from app.infrastructure.db.models.plantilla_proceso_model import PlantillaProcesoModel

class PlantillaProcesoRepositorySQL(PlantillaProcesoRepository):
    def __init__(self, session):
        self.session = session

    def guardar(self, relacion: PlantillaProceso):
        modelo = PlantillaProcesoModel(**vars(relacion))
        self.session.add(modelo)
        self.session.commit()
        self.session.refresh(modelo)
        return modelo

    def listar(self):
        return self.session.query(PlantillaProcesoModel).all()

    def eliminar(self, id: int):
        relacion = self.session.query(PlantillaProcesoModel).filter_by(id=id).first()
        if not relacion:
            return None
        self.session.delete(relacion)
        self.session.commit()
        return True

    def obtener_por_id(self, id: int):
        return self.session.query(PlantillaProcesoModel).filter_by(id=id).first()

    def listar_procesos_por_plantilla(self, plantilla_id: int):
        return self.session.query(PlantillaProcesoModel).filter_by(plantilla_id=plantilla_id).all()
    
    def eliminar_por_plantilla(self, plantilla_id: int):
        relaciones = self.session.query(PlantillaProcesoModel).filter_by(plantilla_id=plantilla_id).all()
        if relaciones:
            for r in relaciones:
                self.session.delete(r)
            self.session.commit()
            return True
        return False
