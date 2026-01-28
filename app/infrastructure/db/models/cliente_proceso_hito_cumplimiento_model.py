# app/infrastructure/db/models/cliente_proceso_hito_cumplimiento_model.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date, Time
from sqlalchemy.orm import relationship
from app.infrastructure.db.database import Base

class ClienteProcesoHitoCumplimientoModel(Base):
    __tablename__ = "cliente_proceso_hito_cumplimiento"

    id = Column(Integer, primary_key=True, index=True)
    cliente_proceso_hito_id = Column(Integer, ForeignKey("cliente_proceso_hito.id"), nullable=False)
    fecha = Column(Date, nullable=False)
    hora = Column(Time, nullable=False)
    observacion = Column(String(255), nullable=True)
    usuario = Column(String(255), nullable=False)
    fecha_creacion = Column(DateTime, nullable=True)

    cliente_proceso_hito = relationship("ClienteProcesoHitoModel", backref="cumplimientos")
