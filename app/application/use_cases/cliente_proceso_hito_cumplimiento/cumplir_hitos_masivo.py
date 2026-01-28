from datetime import date, time
from typing import List, Optional
from app.domain.repositories.cliente_proceso_hito_cumplimiento_repository import ClienteProcesoHitoCumplimientoRepository

def cumplir_hitos_masivo(
    repo: ClienteProcesoHitoCumplimientoRepository,
    cliente_proceso_hito_ids: List[int],
    fecha: date,
    hora: Optional[time] = None,
    observacion: Optional[str] = None,
    usuario: Optional[str] = None
) -> int:
    """
    Registra el cumplimiento de múltiples hitos específicos.
    """
    return repo.cumplir_masivo(
        cliente_proceso_hito_ids=cliente_proceso_hito_ids,
        fecha=fecha,
        hora=hora,
        observacion=observacion,
        usuario=usuario
    )
