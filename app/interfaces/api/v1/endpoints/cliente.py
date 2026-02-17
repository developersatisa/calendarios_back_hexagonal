from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from typing import Optional
from app.infrastructure.db.database import SessionLocal
from app.infrastructure.db.repositories.cliente_repository_sql import ClienteRepositorySQL
from app.application.use_cases.clientes.listar_clientes_por_hito import listar_clientes_por_hito

router = APIRouter(prefix="/clientes", tags=["Cliente"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_repo(db: Session = Depends(get_db)):
    return ClienteRepositorySQL(db)

@router.get("/hito/{hito_id}", summary="Listar clientes por hito",
    description="Devuelve la lista de clientes que tienen un hito específico en su calendario, sin repetir clientes.")

def get_clientes_por_hito(
    hito_id: int = Path(..., description="ID del hito a buscar"),
    page: Optional[int] = Query(None, ge=1, description="Página actual"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Cantidad de resultados por página (máximo 10000)"),
    sort_field: Optional[str] = Query(None, description="Campo por el cual ordenar"),
    sort_direction: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Dirección de ordenación: asc o desc"),
    repo = Depends(get_repo)
):
    clientes = listar_clientes_por_hito(repo, hito_id)
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

    # Aplicar paginación
    if page is not None and limit is not None:
        start = (page - 1) * limit
        end = start + limit
        clientes = clientes[start:end]

    if not clientes:
        raise HTTPException(status_code=404, detail=f"No se encontraron clientes con el hito {hito_id}")

    return {
        "total": total,
        "clientes": clientes
    }

@router.get("", summary="Listar clientes",
    description="Devuelve la lista completa de clientes registrados en el sistema.")
def obtener_todos(
    page: Optional[int] = Query(None, ge=1, description="Página actual"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Cantidad de resultados por página (máximo 10000)"),
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

@router.get("/con-calendario", summary="Listar clientes con calendario activo",
    description="Devuelve la lista de clientes que tienen al menos un hito habilitado en su calendario.")
def listar_con_calendario(repo: ClienteRepositorySQL = Depends(get_repo)):
    clientes = repo.listar_con_hitos()
    # Ordenar por razón social
    clientes.sort(key=lambda c: c.razsoc.lower() if c.razsoc else "")
    return {
        "total": len(clientes),
        "page": 1,
        "limit": len(clientes),
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

@router.get("/departamentos", summary="Listar clientes con departamentos",
    description="Devuelve un listado paginado de clientes que tienen departamentos asociados.")
def obtener_con_departamentos(
    page: Optional[int] = Query(1, ge=1, description="Página actual"),
    limit: Optional[int] = Query(10, ge=1, le=10000, description="Cantidad de resultados por página"),
    search: Optional[str] = Query(None, description="Buscar por CIF o Razón Social"),
    sort_field: Optional[str] = Query(None, description="Campo por el cual ordenar"),
    sort_direction: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Dirección de ordenación: asc o desc"),
    repo: ClienteRepositorySQL = Depends(get_repo)
):
    offset = (page - 1) * limit
    clientes, total = repo.listar_con_departamentos(limit, offset, search, sort_field, sort_direction)

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "clientes": clientes
    }

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

@router.get("/empresas_usuario/{email}", summary="Obtener empresas de un usuario",
    description="Devuelve la lista de empresas a las que pertenece un usuario.")
def get_empresas_usuario(
    email: str = Path(..., description="Email del usuario a consultar"),
    page: Optional[int] = Query(None, ge=1, description="Página actual"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Cantidad de resultados por página (máximo 10000)"),
    sort_field: Optional[str] = Query(None, description="Campo por el cual ordenar"),
    sort_direction: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Dirección de ordenación: asc o desc"),
    repo = Depends(get_repo)
):
    empresas = repo.listar_empresas_usuario(email)
    total = len(empresas)

    # Aplicar ordenación si se especifica
    if sort_field and hasattr(empresas[0] if empresas else None, sort_field):
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

        empresas.sort(key=sort_key, reverse=reverse)

    # Aplicar paginación después de ordenar
    if page is not None and limit is not None:
        start = (page - 1) * limit
        end = start + limit
        empresas = empresas[start:end]

    return {
        "total": total,
        "clientes": empresas
    }
