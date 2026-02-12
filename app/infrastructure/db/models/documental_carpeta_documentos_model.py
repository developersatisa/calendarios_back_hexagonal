from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.infrastructure.db.database import Base
from datetime import datetime

class DocumentalCarpetaDocumentosModel(Base):
    __tablename__ = "documental_carpeta_documentos"

    id = Column(Integer, primary_key=True, index=True)
    carpeta_id = Column(Integer, ForeignKey("documental_carpeta_cliente.id"), nullable=False)
    nombre_documento = Column(String(255), nullable=False)
    original_file_name = Column(String(255), nullable=False)
    stored_file_name = Column(String(255), nullable=False)
    autor = Column(String(255), nullable=False) # numeross del usuario
    codSubDepar = Column(String(6), nullable=True, default=None)
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.now())
    fecha_actualizacion = Column(DateTime, nullable=False, default=datetime.now())
    eliminado = Column(Boolean, nullable=False, default=False)
