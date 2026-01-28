from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from app.infrastructure.db.database import Base


class RolesModel(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)
    admin = Column(Integer, nullable=False, default=0)
