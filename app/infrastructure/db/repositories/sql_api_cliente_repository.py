from sqlalchemy.orm import Session
from app.domain.entities.api_cliente import ApiCliente
from app.domain.repositories.api_cliente_repository import ApiClienteRepository
from app.infrastructure.db.models.api_cliente_model import ApiClienteModel

class SqlApiClienteRepository(ApiClienteRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_nombre(self, nombre_cliente: str) -> ApiCliente | None:
        row = self.db.query(ApiClienteModel).filter(ApiClienteModel.nombre_cliente == nombre_cliente).first()
        if not row:
            return None
        return ApiCliente(
            id=row.id,
            nombre_cliente=row.nombre_cliente,
            hashed_key=row.api_key,
            activo=row.activo,
            email=row.nombre_cliente
        )
