from typing import Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from app.infrastructure.db.database import SessionLocal
from app.infrastructure.db.repositories.hito_repository_sql import HitoRepositorySQL
from app.infrastructure.db.repositories.cliente_proceso_hito_repository_sql import ClienteProcesoHitoRepositorySQL
from app.infrastructure.db.repositories.proceso_hito_maestro_repository_sql import ProcesoHitoMaestroRepositorySQL

from app.domain.entities.hito import Hito
from app.application.use_cases.hitos.update_hito import actualizar_hito

router = APIRouter(prefix="/hitos", tags=["Hito"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_repo(db: Session = Depends(get_db)):
    return HitoRepositorySQL(db)

def get_repo_cliente_proceso_hito(db: Session = Depends(get_db)):
    return ClienteProcesoHitoRepositorySQL(db)

def get_repo_proceso_hito_maestro(db: Session = Depends(get_db)):
    return ProcesoHitoMaestroRepositorySQL(db)

@router.post("", summary="Crear un nuevo hito",
    description="Crea un nuevo hito especificando nombre, fecha límite, si es obligatorio y si está habilitado.")
def crear(
    data: dict = Body(..., example={
        "nombre": "Recibir documentos",
        "fecha_limite": "2023-01-05",
        "hora_limite": "12:00:00",
        "obligatorio": 1,
        "tipo": "Atisa",
        "habilitado": 1,
        "critico": False
    }),
    repo = Depends(get_repo)
):

    hora_limite = data["hora_limite"]
    if len(hora_limite.split(":")) == 2:  # Si solo tiene HH:MM, agregar :00
        hora_limite = hora_limite + ":00"

    hito = Hito(
        nombre=data.get("nombre"),
        fecha_limite=data.get("fecha_limite"),
        hora_limite=hora_limite,
        descripcion=data.get("descripcion"),
        obligatorio=data.get("obligatorio", False),
        tipo=data.get("tipo"),
        habilitado=data.get("habilitado", True),
        critico=data.get("critico", False)
    )
    return repo.guardar(hito)

@router.get("/hitos-cliente-por-empleado", summary="Listar hitos por cliente/empleado",
    description="Devuelve todos los hitos asociados a los procesos de clientes gestionados por un empleado. Filtrable por fecha límite, mes y año.")
def obtener_hitos_por_empleado(
    email: str = Query(..., description="Email del empleado"),
    fecha_inicio: Optional[str] = Query(None, description="Fecha mínima (YYYY-MM-DD) de fecha límite del hito"),
    fecha_fin: Optional[str] = Query(None, description="Fecha máxima (YYYY-MM-DD) de fecha límite del hito"),
    mes: Optional[int] = Query(None, ge=1, le=12, description="Mes de fecha límite del hito (1-12)"),
    anio: Optional[int] = Query(None, ge=2000, le=2100, description="Año de fecha límite del hito"),
    repo = Depends(get_repo)
):
    return repo.listar_hitos_cliente_por_empleado(
        email= email,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        mes=mes,
        anio=anio
    )

@router.get("/habilitados", summary="Listar hitos habilitados",
    description="Devuelve solo los hitos que están habilitados (habilitado=True).")
def listar_habilitados(repo = Depends(get_repo)):
    return repo.listar_habilitados()

@router.get("", summary="Listar todos los hitos",
    description="Devuelve todos los hitos definidos en el sistema.")
def listar(
    page: Optional[int] = Query(None, ge=1, description="Página actual"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Cantidad de resultados por página (máximo 10000)"),
    sort_field: Optional[str] = Query(None, description="Campo por el cual ordenar"),
    sort_direction: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Dirección de ordenación: asc o desc"),
    repo = Depends(get_repo)
):
    hitos = repo.listar()
    total = len(hitos)

    # Aplicar ordenación si se especifica y hay datos para ordenar
    if sort_field and hitos and hasattr(hitos[0], sort_field):
        reverse = sort_direction == "desc"

        # Función de ordenación que maneja valores None
        def sort_key(hito):
            value = getattr(hito, sort_field, None)

            # Manejo especial para diferentes tipos de campos
            if sort_field in ["id", "frecuencia", "obligatorio"]:
                if value is None:
                    return -1 if not reverse else float('inf')  # None al inicio en asc, al final en desc
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return -1 if not reverse else float('inf')

            elif sort_field in ["fecha_inicio", "fecha_fin"]:
                if value is None:
                    return -1 if not reverse else float('inf')  # None al inicio en asc, al final en desc
                try:
                    # Convertir fecha a timestamp para ordenación
                    if isinstance(value, str):
                        return datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()
                    elif isinstance(value, date):
                        return datetime.combine(value, datetime.min.time()).timestamp()
                    elif hasattr(value, 'timestamp'):
                        return value.timestamp()
                    else:
                        return -1 if not reverse else float('inf')
                except (ValueError, TypeError):
                    return -1 if not reverse else float('inf')
            else:
                # Para campos de texto
                if value is None:
                    return ""  # Strings vacíos van al principio alfabéticamente
                return str(value).lower()

        hitos.sort(key=sort_key, reverse=reverse)

    # Aplicar paginación después de ordenar
    if page is not None and limit is not None:
        start = (page - 1) * limit
        end = start + limit
        hitos = hitos[start:end]

    # Devolver respuesta exitosa incluso si no hay hitos después de la paginación
    return {
        "total": total,
        "hitos": hitos
    }

@router.get("/{id}", summary="Obtener hito por ID",
    description="Devuelve la información de un hito específico por su ID.")
def get_hito(
    id: int = Path(..., description="ID del hito a consultar"),
    repo = Depends(get_repo)
):
    hito = repo.obtener_por_id(id)
    if not hito:
        raise HTTPException(status_code=404, detail="Hito no encontrado")
    return hito

@router.put("/{id}", summary="Actualizar hito",
    description="Actualiza un hito existente por su ID.")
def update(
    id: int = Path(..., description="ID del hito a actualizar"),
    data: dict = Body(..., example={
        "nombre": "Recibir y validar documentos",
        "frecuencia": 1,
        "temporalidad": "mes",
        "fecha_inicio": "2023-01-01",
        "fecha_fin": "2023-01-10",
        "obligatorio": 1,
        "critico": True
    }),
    repo = Depends(get_repo)
):
    actualizado = actualizar_hito(id, data, repo)
    if not actualizado:
        raise HTTPException(status_code=404, detail="Hito no encontrado")
    return actualizado

@router.delete("/{id}", summary="Eliminar hito",
    description="Elimina un hito por su ID. Verifica que no existan registros finalizados antes de eliminar.")
def delete_hito(
    id: int = Path(..., description="ID del hito a eliminar"),
    repo = Depends(get_repo),
    repo_cliente_proceso_hito = Depends(get_repo_cliente_proceso_hito),
    repo_proceso_hito_maestro = Depends(get_repo_proceso_hito_maestro)
):
    try:
        # Verificar que el hito existe
        hito = repo.obtener_por_id(id)
        if not hito:
            raise HTTPException(status_code=404, detail="Hito no encontrado")

        # Verificar si hay registros en cliente_proceso_hito
        tiene_registros = repo_cliente_proceso_hito.verificar_registros_por_hito(id)
        if tiene_registros:
            raise HTTPException(
                status_code=409,
                detail="No se puede eliminar por estar asociado al calendario de algún cliente"
            )

        # Proceder con el borrado en cascada
        # 1. Eliminar registros de cliente_proceso_hito
        eliminados_cph = repo_cliente_proceso_hito.eliminar_por_hito_id(id)

        # 2. Eliminar registros de proceso_hito_maestro
        eliminados_phm = repo_proceso_hito_maestro.eliminar_por_hito_id(id)

        # 3. Eliminar el hito
        resultado = repo.eliminar(id)
        if not resultado:
            raise HTTPException(status_code=500, detail="Error al eliminar el hito")

        return {
            "mensaje": "Hito eliminado correctamente",
            "detalles": {
                "hito_id": id,
                "registros_cliente_proceso_hito_eliminados": eliminados_cph,
                "registros_proceso_hito_maestro_eliminados": eliminados_phm
            }
        }

    except HTTPException:
        # Re-lanzar las excepciones HTTP ya manejadas
        raise
    except Exception as e:
        # Manejar errores inesperados
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")
