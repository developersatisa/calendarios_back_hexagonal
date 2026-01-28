from app.domain.repositories.plantilla_repository import PlantillaRepository

def actualizar_plantilla(id: int, data: dict, repo: PlantillaRepository):
    plantilla_existente = repo.obtener_por_id(id)
    if not plantilla_existente:
        return None

    return repo.actualizar(id, data)