# app/infrastructure/db/models/cliente_proceso_hito_model.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey,Date, Time
from sqlalchemy.orm import relationship
from app.infrastructure.db.database import Base

class ClienteProcesoHitoModel(Base):
    __tablename__ = "cliente_proceso_hito"

    id = Column(Integer, primary_key=True, index=True)
    cliente_proceso_id = Column(Integer, ForeignKey("cliente_proceso.id"), nullable=False)
    hito_id = Column(Integer, ForeignKey("proceso_hito_maestro.id_hito"), nullable=False)
    estado = Column(String(50), nullable=False)
    fecha_estado = Column(DateTime, nullable=True)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=True)
    hora_limite = Column(Time, nullable=True)
    tipo = Column(String(255), nullable=False)

    cliente_proceso = relationship("ClienteProcesoModel", backref="hitos_cliente")
    hito = relationship("ProcesoHitoMaestroModel",
                       foreign_keys=[hito_id],
                       primaryjoin="ClienteProcesoHitoModel.hito_id == ProcesoHitoMaestroModel.id_hito")
