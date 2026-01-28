from abc import ABC, abstractmethod
from app.domain.entities.plantilla_proceso import PlantillaProceso

class PlantillaProcesoRepository(ABC):

    @abstractmethod
    def guardar(self, relacion: PlantillaProceso):
        pass

    @abstractmethod
    def listar(self):
        pass

    @abstractmethod
    def eliminar(self):
        pass

    @abstractmethod
    def eliminar_por_plantilla(self):
        pass

    @abstractmethod
    def obtener_por_id(self):
        pass

    @abstractmethod
    def listar_procesos_por_plantilla(self):
        pass
