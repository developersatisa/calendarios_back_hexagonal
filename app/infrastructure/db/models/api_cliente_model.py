from sqlalchemy import Column, Integer, String, Boolean
from app.infrastructure.db.database import Base

class ApiClienteModel(Base):
    __tablename__ = "api_clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre_cliente = Column(String(255), nullable=False)
    api_key = Column(String(255), unique=True, nullable=False)
    activo = Column(Boolean, default=True)
    email = Column(String(255), nullable=False)
