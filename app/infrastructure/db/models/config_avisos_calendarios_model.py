# app/infrastructure/db/models/config_avisos_calendarios_model.py

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, UniqueConstraint, Time
from app.infrastructure.db.database import Base

class ConfigAvisoCalendarioModel(Base):
    __tablename__ = "config_avisos_calendarios"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(String(9), ForeignKey("clientes.idcliente"), nullable=False)
    codSubDepar = Column(String(6), nullable=False)

    aviso_vence_hoy = Column(Boolean, nullable=False)
    temporicidad_vence_hoy = Column(Integer, nullable=True)
    tiempo_vence_hoy = Column(Integer, nullable=True)
    hora_vence_hoy = Column(Time, nullable=True)

    aviso_proximo_vencimiento = Column(Boolean, nullable=False)
    temporicidad_proximo_vencimiento = Column(Integer, nullable=True)
    tiempo_proximo_vencimiento = Column(Integer, nullable=True)
    hora_proximo_vencimiento = Column(Time, nullable=True)
    dias_proximo_vencimiento = Column(Integer, nullable=True)

    aviso_vencido = Column(Boolean, nullable=False)
    temporicidad_vencido = Column(Integer, nullable=True)
    tiempo_vencido = Column(Integer, nullable=True)
    hora_vencido = Column(Time, nullable=True)

    config_global = Column(Boolean, nullable=True)
    temporicidad_global = Column(Integer, nullable=True)
    tiempo_global = Column(Integer, nullable=True)
    hora_global = Column(Time, nullable=True)

    __table_args__ = (
        UniqueConstraint('cliente_id', 'codSubDepar', name='uq_config_aviso_cliente_subdepar'),
    )
