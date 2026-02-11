from app.domain.entities.metadatos_area import MetadatosArea
from app.infrastructure.db.models.metadatos_area_model import MetadatosAreaModel

class MetadatosAreaMapper:

    @staticmethod
    def to_entity(model: MetadatosAreaModel) -> MetadatosArea:
        return MetadatosArea(
            id=model.id,
            id_metadato=model.id_metadato,
            codSubDepar=model.codSubDepar
        )

    @staticmethod
    def to_model(entity: MetadatosArea) -> MetadatosAreaModel:
        return MetadatosAreaModel(
            id=entity.id,
            id_metadato=entity.id_metadato,
            codSubDepar=entity.codSubDepar
        )
