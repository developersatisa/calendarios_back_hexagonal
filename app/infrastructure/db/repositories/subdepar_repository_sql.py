from typing import List, Optional
from sqlalchemy.orm import Session
from app.domain.repositories.subdepar_repository import SubdeparRepository
from app.domain.entities.subdepar import Subdepar
from app.infrastructure.db.models.subdepar_model import SubdeparModel

class SubdeparRepositorySQL(SubdeparRepository):
    def __init__(self, session: Session):
        self.session = session

    def listar(self) -> List[Subdepar]:
        registros = self.session.query(SubdeparModel).all()
        return [self._mapear_modelo_a_entidad(r) for r in registros]

    def obtener_por_id(self, id: int) -> Optional[Subdepar]:
        registro = self.session.query(SubdeparModel).filter_by(id=id).first()
        return self._mapear_modelo_a_entidad(registro) if registro else None

    def _mapear_modelo_a_entidad(self, modelo: SubdeparModel) -> Subdepar:
        return Subdepar(
            id=modelo.id,
            codidepar=modelo.codidepar,
            ceco=modelo.ceco,
            codSubDepar=modelo.codSubDepar,
            nombre=modelo.nombre,
            fechaini=modelo.fechaini,
            fechafin=modelo.fechafin,
        )
