from app.domain.repositories.proceso_repository import ProcesoRepository

def actualizar_proceso(id: int, data: dict, repo: ProcesoRepository):
    proceso_existente = repo.obtener_por_id(id)
    if not proceso_existente:
        return None
    return repo.actualizar(id, data)

