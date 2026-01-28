from datetime import date
from typing import List
from app.domain.repositories.cliente_proceso_hito_repository import ClienteProcesoHitoRepository

def actualizar_fecha_masivo(
    repo: ClienteProcesoHitoRepository,
    hito_id: int,
    cliente_ids: List[int],
    nueva_fecha: date,
    fecha_desde: date,
    fecha_hasta: date | None = None
) -> int:
    """
    Casos de uso para actualizar masivamente la fecha límite de un hito en múltiples clientes.
    Devuelve la cantidad de registros actualizados.
    """
    return repo.actualizar_fecha_masivo(
        hito_id=hito_id,
        cliente_ids=cliente_ids,
        nueva_fecha=nueva_fecha,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )
