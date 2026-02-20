from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from app.infrastructure.db.database import Base

class AuditoriaCalendariosModel(Base):
    __tablename__ = "auditoria_calendarios"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(String(9), ForeignKey("clientes.idcliente"), nullable=False)
    hito_id = Column(Integer, ForeignKey("hito.id"), nullable=False)
    campo_modificado = Column(String(255), nullable=False)
    valor_anterior = Column(String(255), nullable=False)
    valor_nuevo = Column(String(255), nullable=False)
    observaciones = Column(String(255), nullable=True)
    motivo = Column(Integer, nullable=True)
    usuario = Column(String(255), nullable=False) # numeross del usuario
    codSubDepar = Column(String(6), nullable=True, default=None)
    fecha_modificacion = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
