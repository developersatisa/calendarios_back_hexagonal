from app.domain.entities.metadatos_area import MetadatosArea
from app.domain.repositories.metadatos_area_repository import MetadatosAreaRepository
from app.domain.repositories.metadato_repository import MetadatoRepository

class CrearMetadatosAreaUseCase:
    def __init__(self, metadatos_area_repo: MetadatosAreaRepository, metadato_repo: MetadatoRepository):
        self.metadatos_area_repo = metadatos_area_repo
        self.metadato_repo = metadato_repo

    def execute(self, id_metadato: int, codSubDepar: str) -> MetadatosArea:
        metadato = self.metadato_repo.get_by_id(id_metadato)
        if not metadato:
            raise ValueError("El metadato no existe")
        if metadato.global_ == 1:
            raise ValueError("No se puede asociar un metadato global a un área")

        entidad = MetadatosArea(
            id=None,
            id_metadato=id_metadato,
            codSubDepar=codSubDepar
        )
        return self.metadatos_area_repo.save(entidad)
