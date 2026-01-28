from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class AdminHitosDepartamentoRepository(ABC):
    @abstractmethod
    def listar_hitos_departamentos(
        self,
        mes: Optional[int] = None,
        anio: Optional[int] = None,
        cod_subdepar: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Lista hitos agrupados por departamento y proceso con filtros opcionales."""
        pass

    @abstractmethod
    def actualizar_hito_departamento(
        self,
        cliente_proceso_hito_id: int,
        data: Dict[str, Any],
    ) -> Any | None:
        """Actualiza campos del hito a nivel de cliente_proceso_hito para un departamento.

        Debe permitir actualizar, al menos: estado, fecha_limite, hora_limite y tipo.
        Devuelve el registro actualizado o None si no existe.
        """
        pass
