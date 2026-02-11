from typing import List
from sqlalchemy.orm import Session
from app.domain.entities.metadatos_area import MetadatosArea
from app.domain.repositories.metadatos_area_repository import MetadatosAreaRepository
from app.infrastructure.db.models.metadatos_area_model import MetadatosAreaModel
from app.infrastructure.mappers.metadatos_area_mapper import MetadatosAreaMapper

class SQLMetadatosAreaRepository(MetadatosAreaRepository):
    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> List[MetadatosArea]:
        return [self._to_entity(m) for m in self.session.query(MetadatosAreaModel).all()]

    def get_by_id(self, id: int) -> MetadatosArea | None:
        m = self.session.query(MetadatosAreaModel).filter_by(id=id).first()
        return self._to_entity(m) if m else None

    def save(self, data: MetadatosArea) -> MetadatosArea:
        modelo = MetadatosAreaModel(
            id_metadato=data.id_metadato,
            codSubDepar=data.codSubDepar
        )
        self.session.add(modelo)
        self.session.commit()
        self.session.refresh(modelo)
        return self._to_entity(modelo)

    def delete(self, id: int) -> None:
        self.session.query(MetadatosAreaModel).filter_by(id=id).delete()
        self.session.commit()

    def delete_by_metadato_id(self, id_metadato: int) -> int:
        count = self.session.query(MetadatosAreaModel).filter_by(id_metadato=id_metadato).count()
        self.session.query(MetadatosAreaModel).filter_by(id_metadato=id_metadato).delete()
        self.session.commit()
        return count

    def _to_entity(self, m: MetadatosAreaModel) -> MetadatosArea:
        return MetadatosArea(
            id=m.id,
            id_metadato=m.id_metadato,
            codSubDepar=m.codSubDepar
        )

    def get_by_cod_subdepar_list(self, codigos_subdepar: List[str]) -> List[MetadatosArea]:
        if not codigos_subdepar:
            return []

        rows = self.session.query(MetadatosAreaModel).filter(
            MetadatosAreaModel.codSubDepar.in_(codigos_subdepar)
        ).all()

        return [MetadatosAreaMapper.to_entity(row) for row in rows]
