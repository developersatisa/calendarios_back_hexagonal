from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.config_avisos_calendarios import ConfigAvisoCalendario

class ConfigAvisoCalendarioRepository(ABC):
    @abstractmethod
    def listar(self) -> List[ConfigAvisoCalendario]:
        pass

    @abstractmethod
    def obtener_por_id(self, id: int) -> Optional[ConfigAvisoCalendario]:
        pass

    @abstractmethod
    def guardar(self, config_aviso: ConfigAvisoCalendario) -> ConfigAvisoCalendario:
        pass

    @abstractmethod
    def actualizar(self, id: int, data: dict) -> Optional[ConfigAvisoCalendario]:
        pass

    @abstractmethod
    def eliminar(self, id: int) -> bool:
        pass
