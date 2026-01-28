from abc import ABC, abstractmethod
from app.domain.entities.proceso_hito_maestro import ProcesoHitoMaestro

class ProcesoHitoMaestroRepository(ABC):

    @abstractmethod
    def guardar(self, relacion: ProcesoHitoMaestro):
        pass

    @abstractmethod
    def listar(self):
        pass

    @abstractmethod
    def eliminar(self, id: int):
        pass

    @abstractmethod
    def obtener_por_id(self, id: int):
        pass

    @abstractmethod
    def listar_por_proceso(self, id_proceso: str):
        pass

    @abstractmethod
    def eliminar_por_hito_id(self, hito_id: int):
        pass
