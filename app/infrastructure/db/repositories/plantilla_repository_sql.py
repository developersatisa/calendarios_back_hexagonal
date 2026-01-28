from app.domain.repositories.plantilla_repository import PlantillaRepository
from app.domain.entities.plantilla import Plantilla
from app.infrastructure.db.models import PlantillaModel

class PlantillaRepositorySQL(PlantillaRepository):
    def __init__(self, session):
        self.session = session

    def guardar(self, plantilla: Plantilla):
        modelo = PlantillaModel(**vars(plantilla))
        self.session.add(modelo)
        self.session.commit()
        self.session.refresh(modelo)
        return modelo

    def actualizar(self, id: int, data: dict):
        plantilla = self.session.query(PlantillaModel).filter_by(id=id).first()
        if not plantilla:
            return None

        for key, value in data.items():
            setattr(plantilla, key, value)

        self.session.commit()
        self.session.refresh(plantilla)
        return plantilla

    def listar(self):
        return self.session.query(PlantillaModel).all()
    
    def obtener_por_id(self, id: int):
        return self.session.query(PlantillaModel).filter_by(id=id).first()

    def eliminar(self, id: int):
        plantilla = self.session.query(PlantillaModel).filter_by(id=id).first()
        if not plantilla:
            return None
        self.session.delete(plantilla)
        self.session.commit()
        return True