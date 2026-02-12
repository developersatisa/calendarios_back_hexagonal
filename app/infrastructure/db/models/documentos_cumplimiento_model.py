from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.infrastructure.db.database import Base

class DocumentoCumplimientoModel(Base):
    __tablename__ = "documentos_cumplimiento"

    id = Column(Integer, primary_key=True, index=True)
    cumplimiento_id = Column(Integer, ForeignKey("cliente_proceso_hito_cumplimiento.id"), nullable=False)
    nombre_documento = Column(String(255), nullable=False)
    original_file_name = Column(String(255), nullable=False)
    stored_file_name = Column(String(255), nullable=False)
    autor = Column(String(255), nullable=True)
    codSubDepar = Column(String(6), nullable=True)
    fecha_creacion = Column(DateTime, server_default=func.now(), nullable=False)

    cumplimiento = relationship("ClienteProcesoHitoCumplimientoModel", backref="documentos")
