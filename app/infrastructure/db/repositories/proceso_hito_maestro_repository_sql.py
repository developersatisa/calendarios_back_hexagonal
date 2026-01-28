from app.domain.entities.proceso_hito_maestro import ProcesoHitoMaestro
from app.domain.repositories.proceso_hito_maestro_repository import ProcesoHitoMaestroRepository
from app.infrastructure.db.models import ProcesoHitoMaestroModel
from app.infrastructure.db.models import HitoModel

class ProcesoHitoMaestroRepositorySQL(ProcesoHitoMaestroRepository):
    def __init__(self, session):
        self.session = session

    def guardar(self, relacion: ProcesoHitoMaestro):
        modelo = ProcesoHitoMaestroModel(**relacion.__dict__)
        self.session.add(modelo)
        self.session.commit()
        self.session.refresh(modelo)
        return modelo

    def listar(self):
        return self.session.query(ProcesoHitoMaestroModel).all()

    def obtener_por_id(self, id: int):
        return self.session.query(ProcesoHitoMaestroModel).filter_by(id=id).first()

    def eliminar(self, id: int):
        relacion = self.obtener_por_id(id)
        if not relacion:
            return None
        self.session.delete(relacion)
        self.session.commit()
        return True

    def listar_por_proceso(self, id_proceso: int):
        # Hacer JOIN para obtener los datos completos del hito
        return self.session.query(ProcesoHitoMaestroModel, HitoModel).join(
            HitoModel, ProcesoHitoMaestroModel.hito_id == HitoModel.id
        ).filter(ProcesoHitoMaestroModel.proceso_id == id_proceso).all()

    def eliminar_por_hito_id(self, hito_id: int):
        """Elimina todos los registros de proceso_hito_maestro asociados a un hito específico"""
        eliminados = self.session.query(ProcesoHitoMaestroModel).filter(
            ProcesoHitoMaestroModel.hito_id == hito_id
        ).delete(synchronize_session=False)

        self.session.commit()
        return eliminados
