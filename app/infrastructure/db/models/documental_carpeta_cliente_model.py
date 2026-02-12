from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.infrastructure.db.database import Base

class DocumentalCarpetaClienteModel(Base):
    __tablename__ = "documental_carpeta_cliente"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(String(9), ForeignKey("clientes.idcliente"), nullable=False)
    proceso_id = Column(Integer, ForeignKey("proceso.id"), nullable=False)
    carpeta_id = Column(Integer, ForeignKey("documental_carpeta_proceso.id"), nullable=False)
