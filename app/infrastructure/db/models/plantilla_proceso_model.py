from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.infrastructure.db.database import Base



class PlantillaProcesoModel(Base):
    __tablename__ = "plantilla_proceso"

    id = Column(Integer, primary_key=True, index=True)
    plantilla_id = Column(Integer, ForeignKey("plantilla.id"), nullable=False)
    proceso_id = Column(Integer, ForeignKey("proceso.id"), nullable=False)

    plantilla = relationship("PlantillaModel", back_populates="procesos")
    proceso = relationship("ProcesoModel", back_populates="plantillas")