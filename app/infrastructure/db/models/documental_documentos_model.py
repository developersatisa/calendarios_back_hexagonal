# app/infrastructure/db/models/documental_documentos_model.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from app.infrastructure.db.database import Base

class DocumentalDocumentosModel(Base):
    __tablename__ = "documental_documentos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(String(9), ForeignKey("clientes.idcliente"), nullable=False)
    categoria_id = Column(Integer, ForeignKey("documental_categorias.id"), nullable=False)
    nombre_documento = Column(String(255), nullable=False)
    original_file_name = Column(String(255), nullable=False)
    stored_file_name = Column(String(255), nullable=False)
    fecha_creacion = Column(DateTime, nullable=True)
