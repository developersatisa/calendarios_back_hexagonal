from sqlalchemy import Column, Integer, String, Date, Time
from app.infrastructure.db.database import Base
from sqlalchemy.orm import relationship

class HitoModel(Base):
    __tablename__ = "hito"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    fecha_limite = Column(Date, nullable=False)
    hora_limite = Column(Time, nullable=True)
    descripcion = Column(String(255), nullable=True)
    obligatorio = Column(Integer, nullable=False, default=0)  # 0 = No, 1 = Si
    tipo = Column(String(255), nullable=False)
    habilitado = Column(Integer, nullable=False, default=1)  # 0 = No, 1 = Si

    procesos = relationship("ProcesoHitoMaestroModel", back_populates="hito", cascade="all, delete-orphan")
