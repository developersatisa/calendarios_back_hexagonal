from fastapi import APIRouter, Depends, Query, Path, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.infrastructure.db.database import SessionLocal
from app.infrastructure.db.repositories.subdepar_repository_sql import SubdeparRepositorySQL

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_repo(db: Session = Depends(get_db)):
    return SubdeparRepositorySQL(db)

@router.get("/subdepartamentos", tags=["Subdepartamentos"], summary="Listar subdepartamentos",
    description="Devuelve la lista completa de subdepartamentos registrados en el sistema.")
def listar(
    page: Optional[int] = Query(None, ge=1, description="Página actual"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Cantidad de resultados por página"),
    sort_field: Optional[str] = Query(None, description="Campo por el cual ordenar"),
    sort_direction: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Dirección de ordenación: asc o desc"),
    repo = Depends(get_repo)
):
    subdepartamentos_raw = repo.listar()

    # Agrupar por ceco
    grouped_data = {}
    for sub in subdepartamentos_raw:
        if sub.ceco not in grouped_data:
            grouped_data[sub.ceco] = {
                "ceco": sub.ceco,
                "nombre": sub.nombre, # Asumimos el nombre del primero
                "cantidad": 0,
                "items": []
            }
        grouped_data[sub.ceco]["items"].append(sub)
        grouped_data[sub.ceco]["cantidad"] += 1

    # Convertir a lista
    subdepartamentos_grouped = list(grouped_data.values())
    total = len(subdepartamentos_grouped)

    # Aplicar ordenación si se especifica (sobre los grupos)
    if sort_field:
        reverse = sort_direction == "desc"

        def sort_key(group):
            # Si el campo existe en el nivel superior del grupo (ceco, nombre, cantidad)
            if sort_field in group:
                value = group[sort_field]
            # Si no, intentamos buscar en el primer item (limitado)
            elif group["items"] and hasattr(group["items"][0], sort_field):
                value = getattr(group["items"][0], sort_field, None)
            else:
                value = None

            if value is None:
                return ""

            # Manejo de tipos para ordenación
            if isinstance(value, (int, float)):
                return value
            return str(value).lower()

        subdepartamentos_grouped.sort(key=sort_key, reverse=reverse)

    # Aplicar paginación después de ordenar
    if page is not None and limit is not None:
        start = (page - 1) * limit
        end = start + limit
        subdepartamentos_grouped = subdepartamentos_grouped[start:end]

    if not subdepartamentos_grouped and page == 1:
        raise HTTPException(status_code=404, detail="No se encontraron subdepartamentos")

    return {
        "total": total,
        "subdepartamentos": subdepartamentos_grouped
    }

@router.get("/subdepartamentos/{id}", tags=["Subdepartamentos"], summary="Obtener subdepartamento por ID",
    description="Devuelve los datos de un subdepartamento específico según su ID.")
def obtener_por_id(
    id: int = Path(..., description="ID del subdepartamento a consultar"),
    repo = Depends(get_repo)
):
    subdepartamento = repo.obtener_por_id(id)
    if not subdepartamento:
        raise HTTPException(status_code=404, detail="Subdepartamento no encontrado")
    return subdepartamento

@router.get("/subdepartamentos/cliente/{id_cliente}", tags=["Subdepartamentos"], summary="Obtener subdepartamentos por cliente",
    description="Devuelve la lista de subdepartamentos (ceco y nombre) asociados a un cliente específico.")
def obtener_por_cliente(
    id_cliente: str = Path(..., description="ID del cliente a consultar"),
    repo = Depends(get_repo)
):
    subdepartamentos = repo.obtener_por_cliente(id_cliente)
    if not subdepartamentos:
        raise HTTPException(status_code=404, detail=f"No se encontraron subdepartamentos para el cliente {id_cliente}")
    return subdepartamentos
