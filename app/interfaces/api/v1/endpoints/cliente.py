from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.infrastructure.db.database import SessionLocal
from app.infrastructure.db.repositories.cliente_repository_sql import ClienteRepositorySQL

router = APIRouter(prefix="/clientes", tags=["Cliente"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_repo(db: Session = Depends(get_db)):
    return ClienteRepositorySQL(db)
@router.get("", summary="Listar clientes",
    description="Devuelve la lista completa de clientes registrados en el sistema.")
def obtener_todos(
    page: Optional[int] = Query(None, ge=1, description="Página actual"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Cantidad de resultados por página"),
    sort_field: Optional[str] = Query(None, description="Campo por el cual ordenar"),
    sort_direction: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Dirección de ordenación: asc o desc"),
    repo = Depends(get_repo)
):
    clientes = repo.listar()
    total = len(clientes)

    # Aplicar ordenación si se especifica
    if sort_field and hasattr(clientes[0] if clientes else None, sort_field):
        reverse = sort_direction == "desc"

        # Función de ordenación que maneja valores None
        def sort_key(cliente):
            value = getattr(cliente, sort_field, None)
            if value is None:
                return ""  # Los valores None van al final
            # Si es numérico (como idcliente), convertir a número para ordenación correcta
            if sort_field == "idcliente":
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return 0
            # Para campos de texto, convertir a minúsculas para ordenación insensible a mayúsculas
            return str(value).lower()

        clientes.sort(key=sort_key, reverse=reverse)

    # Aplicar paginación después de ordenar
    if page is not None and limit is not None:
        start = (page - 1) * limit
        end = start + limit
        clientes = clientes[start:end]

    if not clientes:
        raise HTTPException(status_code=404, detail="No se encontraron clientes")

    return {
        "total": total,
        "clientes": clientes
    }

@router.get("/nombre/{nombre}", summary="Buscar clientes por nombre",
    description="Busca clientes que contengan el nombre proporcionado.")
def buscar_nombre(
    nombre: str = Path(..., description="Nombre (o parte) del cliente a buscar"),
    repo = Depends(get_repo)
):
    clientes = repo.buscar_por_nombre(nombre)
    if not clientes:
        raise HTTPException(status_code=404, detail="No se encontraron clientes con ese nombre")
    return clientes

@router.get("/cif/{cif}", summary="Buscar cliente por CIF",
    description="Busca un cliente específico por su CIF.")
def buscar_cif(
    cif: str = Path(..., description="CIF del cliente a buscar"),
    repo = Depends(get_repo)
):
    cliente = repo.buscar_por_cif(cif)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

@router.get("/{id}", summary="Obtener cliente por ID",
    description="Devuelve la información de un cliente específico por su ID.")
def get_hito(
    id: int = Path(..., description="ID del cliente a consultar"),
    repo = Depends(get_repo)
):
    cliente = repo.obtener_por_id(id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente
