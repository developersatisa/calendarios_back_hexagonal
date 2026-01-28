from datetime import datetime
from app.domain.entities.auditoria_calendarios import AuditoriaCalendarios
from app.domain.repositories.auditoria_calendarios_repository import AuditoriaCalendariosRepository
from app.infrastructure.db.models.auditoria_calendarios_model import AuditoriaCalendariosModel
from app.infrastructure.db.models.hito_model import HitoModel
from app.infrastructure.db.models.cliente_proceso_hito_model import ClienteProcesoHitoModel
from app.infrastructure.db.models.proceso_hito_maestro_model import ProcesoHitoMaestroModel


class AuditoriaCalendariosRepositorySQL(AuditoriaCalendariosRepository):
    def __init__(self, session):
        self.session = session

    def guardar(self, auditoria: AuditoriaCalendarios):
        # Crear diccionario con todos los campos, estableciendo valores para campos de auditoría temporal
        data = {}
        current_time = datetime.utcnow()

        for k, v in auditoria.__dict__.items():
            if k == 'id' and v is None:
                continue  # Saltar el campo id si es None
            elif k in ['created_at', 'updated_at']:
                # Establecer valores de auditoría temporal desde el backend
                data[k] = current_time
            else:
                data[k] = v

        modelo = AuditoriaCalendariosModel(**data)
        self.session.add(modelo)
        self.session.commit()
        self.session.refresh(modelo)
        return modelo

    def listar(self):
        return self.session.query(AuditoriaCalendariosModel).all()

    def obtener_por_id(self, id: int):
        return self.session.query(AuditoriaCalendariosModel).filter_by(id=id).first()

    def obtener_por_hito(self, id_hito: int):
        return self.session.query(AuditoriaCalendariosModel).filter_by(hito_id=id_hito).all()

    def obtener_por_cliente(self, cliente_id: str):
        return self.session.query(
            AuditoriaCalendariosModel,
            HitoModel.nombre.label('nombre_hito')
        ).join(
            ClienteProcesoHitoModel, AuditoriaCalendariosModel.hito_id == ClienteProcesoHitoModel.id
        ).join(
            ProcesoHitoMaestroModel, ClienteProcesoHitoModel.hito_id == ProcesoHitoMaestroModel.hito_id
        ).join(
            HitoModel, ProcesoHitoMaestroModel.hito_id == HitoModel.id
        ).filter(AuditoriaCalendariosModel.cliente_id == cliente_id).all()

    # Implementación de métodos async del repositorio base
    async def create(self, auditoria: AuditoriaCalendarios) -> AuditoriaCalendarios:
        return self.guardar(auditoria)

    async def get_by_id(self, id: int):
        return self.obtener_por_id(id)

    async def get_by_hito(self, id_hito: int):
        return self.obtener_por_hito(id_hito)

    async def get_by_cliente(self, id_cliente: str):
        return self.obtener_por_cliente(id_cliente)
