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
    usuario_modificacion = Column(String(255), nullable=False)
    fecha_modificacion = Column(DateTime, nullable=False)
    observaciones = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
