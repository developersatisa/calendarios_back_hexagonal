from datetime import date, time
from typing import List, Optional
from app.domain.repositories.cliente_proceso_hito_repository import ClienteProcesoHitoRepository

def actualizar_fecha_masivo(
    repo: ClienteProcesoHitoRepository,
    hito_id: int,
    cliente_ids: List[int],
    nueva_fecha: date,
    nueva_hora: Optional[time],
    fecha_desde: date,
    fecha_hasta: date | None = None
) -> int:
    """
    Casos de uso para actualizar masivamente la fecha y hora límite de un hito en múltiples clientes.
    Devuelve la cantidad de registros actualizados.
    """
    return repo.actualizar_fecha_masivo(
        hito_id=hito_id,
        cliente_ids=cliente_ids,
        nueva_fecha=nueva_fecha,
        nueva_hora=nueva_hora,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )
