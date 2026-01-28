# app/infrastructure/db/models/documento_categoria_model.py

from sqlalchemy import Column, Integer, String, ForeignKey
from app.infrastructure.db.database import Base

class DocumentalCategoriaModel(Base):
    __tablename__ = "documental_categorias"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(String(9), ForeignKey("clientes.idcliente"), nullable=False)
    nombre = Column(String(255), nullable=False)
