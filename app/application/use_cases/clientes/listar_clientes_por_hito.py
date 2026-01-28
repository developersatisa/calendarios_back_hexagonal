from typing import List
from app.domain.entities.cliente import Cliente
from app.domain.repositories.cliente_repository import ClienteRepository

def listar_clientes_por_hito(repo: ClienteRepository, hito_id: int) -> List[Cliente]:
    """
    Lista todos los clientes que tienen un hito específico asignado en su calendario.
    """
    return repo.listar_por_hito_id(hito_id)
