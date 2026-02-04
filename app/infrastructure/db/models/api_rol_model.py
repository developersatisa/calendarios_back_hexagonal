from sqlalchemy import Column, Integer, String, Boolean
from app.infrastructure.db.database import Base

class ApiRolModel(Base):
    __tablename__ = "api_roles"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    admin = Column(Boolean, default=False)
