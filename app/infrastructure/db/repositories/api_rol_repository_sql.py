from sqlalchemy.orm import Session
from typing import Optional
from app.domain.entities.api_rol import ApiRol
from app.domain.repositories.api_rol_repository import ApiRolRepository
from app.infrastructure.db.models.api_rol_model import ApiRolModel

class SqlApiRolRepository(ApiRolRepository):
    def __init__(self, db: Session):
        self.db = db

    def crear(self, email: str, admin: bool = True) -> ApiRol:
        api_rol_model = ApiRolModel(email=email, admin=admin)
        self.db.add(api_rol_model)
        self.db.commit()
        self.db.refresh(api_rol_model)
        return ApiRol(id=api_rol_model.id, email=api_rol_model.email, admin=api_rol_model.admin)

    def buscar_por_email(self, email: str) -> Optional[ApiRol]:
        api_rol_model = self.db.query(ApiRolModel).filter(ApiRolModel.email == email).first()
        if not api_rol_model:
            return None
        return ApiRol(id=api_rol_model.id, email=api_rol_model.email, admin=api_rol_model.admin)

    def listar(self) -> list[ApiRol]:
        modelos = self.db.query(ApiRolModel).all()
        return [ApiRol(id=m.id, email=m.email, admin=m.admin) for m in modelos]

    def actualizar(self, id: int, admin: bool) -> Optional[ApiRol]:
        api_rol_model = self.db.query(ApiRolModel).filter(ApiRolModel.id == id).first()
        if not api_rol_model:
            return None
        api_rol_model.admin = admin
        self.db.commit()
        self.db.refresh(api_rol_model)
        return ApiRol(id=api_rol_model.id, email=api_rol_model.email, admin=api_rol_model.admin)
