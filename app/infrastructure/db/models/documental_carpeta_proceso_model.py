from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.infrastructure.db.database import Base
from datetime import datetime

class DocumentalCarpetaProcesoModel(Base):
    __tablename__ = "documental_carpeta_proceso"

    id = Column(Integer, primary_key=True, index=True)
    proceso_id = Column(Integer, ForeignKey("proceso.id"), nullable=False)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(String(255), nullable=True)
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.now())
    fecha_actualizacion = Column(DateTime, nullable=False, default=datetime.now())
    eliminado = Column(Boolean, nullable=False, default=False)
