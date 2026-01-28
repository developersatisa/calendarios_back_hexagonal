from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.auditoria_calendarios import AuditoriaCalendarios


class AuditoriaCalendariosRepository(ABC):
    @abstractmethod
    async def create(self, auditoria: AuditoriaCalendarios) -> AuditoriaCalendarios:
        pass

    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[AuditoriaCalendarios]:
        pass

    @abstractmethod
    async def get_by_hito(self, id_hito: int) -> List[AuditoriaCalendarios]:
        pass

    @abstractmethod
    async def get_by_cliente(self, id_cliente: str) -> List[AuditoriaCalendarios]:
        pass
