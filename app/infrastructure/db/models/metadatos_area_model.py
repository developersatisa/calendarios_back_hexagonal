from sqlalchemy import Column, Integer, String, ForeignKey
from app.infrastructure.db.database import Base

class MetadatosAreaModel(Base):
    __tablename__ = "metadatos_area"

    id = Column(Integer, primary_key=True, index=True)
    id_metadato = Column(Integer, ForeignKey("metadatos.id"), nullable=False)
    codSubDepar = Column(String(50), nullable=False)
