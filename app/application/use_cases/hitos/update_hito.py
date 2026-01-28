from app.domain.repositories.hito_repository import HitoRepository

def actualizar_hito(id: int, data: dict, repo: HitoRepository):
    hito_existente = repo.obtener_por_id(id)
    if not hito_existente:
        return None

    return repo.actualizar(id, data)
