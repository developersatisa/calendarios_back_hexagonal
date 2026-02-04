from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from app.domain.services.user_mapping_service import UserMappingService
from app.infrastructure.db.models.api_cliente_model import ApiClienteModel

class UserMappingServiceImpl(UserMappingService):
    def __init__(self, session: Session):
        self.session = session

    def get_api_cliente_id_by_email(self, email: str) -> Optional[int]:
        """
        Obtiene el id_api_cliente basado en el email del usuario usando la tabla api_clientes.
        Busca un registro donde el email coincida con el email.
        """
        if not email:
            return None

        # Validar dominio de ATISA primero
        if not ("@atisa.es" in email.lower() or "@atisa-grupo.com" in email.lower()):
            return None

        # Buscar en la tabla api_clientes por email = email
        # Usamos ilike para búsqueda insensible a mayúsculas/minúsculas
        cliente = self.session.query(ApiClienteModel).filter(
            ApiClienteModel.email.ilike(email.strip()),
            ApiClienteModel.activo == True
        ).first()

        if cliente:
            return cliente.id

        return None
