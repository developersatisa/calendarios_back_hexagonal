from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from app.infrastructure.db.database import SessionLocal
from app.infrastructure.db.repositories.proceso_repository_sql import ProcesoRepositorySQL

from app.application.use_cases.procesos.crear_proceso import crear_proceso
from app.application.use_cases.procesos.update_proceso import actualizar_proceso
from app.application.use_cases.procesos.listar_procesos_cliente_por_empleado import listar_procesos_cliente_por_empleado

router = APIRouter(prefix="/procesos", tags=["Proceso"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_repo(db: Session = Depends(get_db)):
    return ProcesoRepositorySQL(db)

@router.post("", summary="Crear un nuevo proceso",
    description="Crea un proceso especificando nombre, frecuencia, temporalidad y fechas.")
def crear(
    data: dict = Body(..., example={
        "nombre": "Contabilidad NOMINAS",
        "descripcion": "Proceso contable mensual",
        "frecuencia": 1,
        "temporalidad": "mes",
        "inicia_dia_1": True
    }),
    repo = Depends(get_repo)
):
    return crear_proceso(data, repo)

@router.get("/habilitados", summary="Listar procesos habilitados",
    description="Devuelve solo los procesos que están habilitados (habilitado=True).")
def listar_habilitados(repo = Depends(get_repo)):
    return repo.listar_habilitados()

@router.get("", summary="Listar todos los procesos",
    description="Devuelve todos los procesos registrados en el sistema.")
def listar(
    page: Optional[int] = Query(None, ge=1, description="Página actual"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Cantidad de resultados por página"),
    sort_field: Optional[str] = Query(None, description="Campo por el cual ordenar"),
    sort_direction: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Dirección de ordenación: asc o desc"),
    repo = Depends(get_repo)
):
    procesos = repo.listar()
    total = len(procesos)

    # Aplicar ordenación si se especifica
    if sort_field and hasattr(procesos[0] if procesos else None, sort_field):
        reverse = sort_direction == "desc"

        # Función de ordenación que maneja valores None
        def sort_key(proceso):
            value = getattr(proceso, sort_field, None)
            if value is None:
                return ""  # Los valores None van al final

            # Manejo especial para diferentes tipos de campos
            if sort_field in ["id", "frecuencia"]:
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return 0
            else:
                # Para campos de texto (nombre, descripcion, temporalidad),
                # convertir a minúsculas para ordenación insensible a mayúsculas
                return str(value).lower()

        procesos.sort(key=sort_key, reverse=reverse)

    # Aplicar paginación después de ordenar
    if page is not None and limit is not None:
        start = (page - 1) * limit
        end = start + limit
        procesos = procesos[start:end]

    if not procesos:
        raise HTTPException(status_code=404, detail="No se encontraron procesos")

    return {
        "total": total,
        "procesos": procesos
    }

@router.get("/{id}", summary="Obtener proceso por ID",
    description="Devuelve los datos de un proceso específico según su ID.")
def get_proceso(
    id: int = Path(..., description="ID del proceso a consultar"),
    repo = Depends(get_repo)
):
    proceso = repo.obtener_por_id(id)
    if not proceso:
        raise HTTPException(status_code=404, detail="Proceso no encontrado")
    return proceso

@router.put("/{id}", summary="Actualizar proceso",
    description="Actualiza los datos de un proceso existente por su ID.")
def update(
    id: int = Path(..., description="ID del proceso a actualizar"),
    data: dict = Body(..., example={
        "nombre": "Proceso Actualizado",
        "descripcion": "Nueva descripción del proceso",
        "frecuencia": 2,
        "temporalidad": "mes",
        "inicia_dia_1": False
    }),
    repo = Depends(get_repo)
):
    actualizado = actualizar_proceso(id, data, repo)
    if not actualizado:
        raise HTTPException(status_code=404, detail="Proceso no encontrado")
    return actualizado

@router.delete("/{id}", summary="Eliminar proceso",
    description="Elimina un proceso existente según su ID.")
def delete_proceso(
    id: int = Path(..., description="ID del proceso a eliminar"),
    repo = Depends(get_repo)
):
    resultado = repo.eliminar(id)
    if not resultado:
        raise HTTPException(status_code=404, detail="Proceso no encontrado")
    return {"mensaje": "Proceso eliminado"}

@router.get("/procesos-cliente-por-empleado", summary="Listar procesos por cliente/empleado",
    description="Devuelve todos los procesos asociados a los clientes del empleado indicado. Se puede filtrar por mes y año.")
def procesos_cliente_por_empleado(
    email: str = Query(..., description="Email del empleado que hace la consulta"),
    mes: Optional[int] = Query(None, ge=1, le=12, description="Mes de inicio (1-12)"),
    anio: Optional[int] = Query(None, ge=2000, le=2100, description="Año de inicio (ej: 2024)"),
    repo = Depends(get_repo)
):
    """
    Devuelve en UNA sola llamada todos los procesos (con sus hitos) de los clientes
    que gestiona el empleado identificado por su correo.
    """
    return listar_procesos_cliente_por_empleado(
        email=email,
        repo=repo,
        mes=mes,
        anio=anio
    )
