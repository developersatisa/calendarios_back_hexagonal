from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from app.domain.services.user_mapping_service import UserMappingService

class UserMappingServiceImpl(UserMappingService):
    def __init__(self, session: Session):
        self.session = session
    
    def get_api_cliente_id_by_email(self, email: str) -> Optional[int]:
        """
        Obtiene el id_api_cliente basado en el email del usuario.
        
        Para usuarios de ATISA (SSO), asumimos que están asociados al api_cliente_id = 1
        que representa a ATISA. En el futuro esto podría ser más sofisticado.
        """
        # Por ahora, para usuarios de SSO (ATISA), retornamos el id 1
        # Esto podría cambiarse para hacer una consulta más específica si se necesita
        # mapear diferentes emails a diferentes api_cliente_id
        
        # Verificamos que el email tenga un dominio válido de ATISA
        if email and ("@atisa.es" in email.lower() or "@atisa-grupo.com" in email.lower()):
            # Para usuarios de ATISA, retornamos id 1 (esto podría ser configurable)
            return 1
        
        return None