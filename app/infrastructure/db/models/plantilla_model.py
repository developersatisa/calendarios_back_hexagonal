from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.infrastructure.db.database import Base

class PlantillaModel(Base):
    __tablename__ = "plantilla"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)    
    descripcion = Column(String(255), nullable=True)
    procesos = relationship("PlantillaProcesoModel", back_populates="plantilla", cascade="all, delete-orphan")

    