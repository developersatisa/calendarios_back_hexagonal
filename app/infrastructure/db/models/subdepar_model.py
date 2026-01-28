from sqlalchemy import Column, Integer, String, Date
from app.infrastructure.db.database import Base

class SubdeparModel(Base):
    __tablename__ = "subdepar"

    id = Column(Integer, primary_key=True, index=True)
    codidepar = Column(String(30), index=True)
    ceco = Column(String(4), index=True)
    codSubDepar = Column(String(6), index=True)
    nombre = Column(String(50), index=True)
    fechaini = Column(Date, index=True)
    fechafin = Column(Date, index=True)
