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
    limit: Optional[int] = Query(None, ge=1, le=100, description="Cantidad de resultados por página"),
    sort_field: Optional[str] = Query(None, description="Campo por el cual ordenar"),
    sort_direction: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Dirección de ordenación: asc o desc"),
    repo = Depends(get_repo)
):
    subdepartamentos = repo.listar()
    total = len(subdepartamentos)

    # Aplicar ordenación si se especifica
    if sort_field and hasattr(subdepartamentos[0] if subdepartamentos else None, sort_field):
        reverse = sort_direction == "desc"

        # Función de ordenación que maneja valores None
        def sort_key(subdepar):
            value = getattr(subdepar, sort_field, None)
            if value is None:
                return ""  # Los valores None van al final

            # Manejo especial para diferentes tipos de campos
            if sort_field == "id":
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return 0
            elif sort_field in ["fechaini", "fechafin"]:
                try:
                    # Convertir fecha a timestamp para ordenación
                    from datetime import datetime, date
                    if isinstance(value, str):
                        return datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()
                    elif isinstance(value, date):
                        return datetime.combine(value, datetime.min.time()).timestamp()
                    elif hasattr(value, 'timestamp'):
                        return value.timestamp()
                    else:
                        return 0
                except (ValueError, TypeError):
                    return 0
            else:
                # Para campos de texto (codidepar, ceco, codSubDepar, nombre),
                # convertir a minúsculas para ordenación insensible a mayúsculas
                return str(value).lower()

        subdepartamentos.sort(key=sort_key, reverse=reverse)

    # Aplicar paginación después de ordenar
    if page is not None and limit is not None:
        start = (page - 1) * limit
        end = start + limit
        subdepartamentos = subdepartamentos[start:end]

    if not subdepartamentos:
        raise HTTPException(status_code=404, detail="No se encontraron subdepartamentos")

    return {
        "total": total,
        "subdepartamentos": subdepartamentos
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
