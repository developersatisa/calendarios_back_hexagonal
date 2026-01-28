from abc import ABC, abstractmethod
from app.domain.entities.cliente_proceso_hito_cumplimiento import ClienteProcesoHitoCumplimiento
from typing import Optional

class ClienteProcesoHitoCumplimientoRepository(ABC):

    @abstractmethod
    def guardar(self, cliente_proceso_hito_cumplimiento: ClienteProcesoHitoCumplimiento):
        pass

    @abstractmethod
    def listar(self):
        pass

    @abstractmethod
    def obtener_por_id(self, id: int):
        pass

    @abstractmethod
    def actualizar(self, id: int, data: dict):
        pass

    @abstractmethod
    def eliminar(self, id: int):
        pass

    @abstractmethod
    def obtener_por_cliente_proceso_hito_id(self, cliente_proceso_hito_id: int):
        pass

    @abstractmethod
    def obtener_historial_por_cliente_id(self, cliente_id: str, proceso_id: int = None, hito_id: int = None,
                                        fecha_desde: str = None, fecha_hasta: str = None):
        pass

    @abstractmethod
    def cumplir_masivo(self, cliente_proceso_hito_ids: list[int], fecha: str, hora: str = None,
                      observacion: str = None, usuario: str = None):
        """Registra cumplimiento masivo para múltiples hitos específicos"""
        pass
