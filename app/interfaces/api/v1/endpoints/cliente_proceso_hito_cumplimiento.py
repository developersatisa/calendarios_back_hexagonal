from fastapi import APIRouter, Depends, HTTPException, Body, Path, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, date
from app.infrastructure.db.database import SessionLocal
from app.infrastructure.db.repositories.cliente_proceso_hito_cumplimiento_repository_sql import ClienteProcesoHitoCumplimientoRepositorySQL
from app.infrastructure.db.repositories.cliente_proceso_hito_repository_sql import ClienteProcesoHitoRepositorySQL

from app.domain.entities.cliente_proceso_hito_cumplimiento import ClienteProcesoHitoCumplimiento

router = APIRouter(prefix="/cliente-proceso-hito-cumplimientos", tags=["ClienteProcesoHitoCumplimiento"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_repo(db: Session = Depends(get_db)):
    return ClienteProcesoHitoCumplimientoRepositorySQL(db)

def get_repo_cliente_proceso_hito(db: Session = Depends(get_db)):
    return ClienteProcesoHitoRepositorySQL(db)

@router.post("", summary="Crear cumplimiento de hito",
    description="Registra el cumplimiento de un hito específico de un proceso de cliente.")
def crear(
    data: dict = Body(..., example={
        "cliente_proceso_hito_id": 1,
        "fecha": "2023-01-01",
        "hora": "14:30:00",
        "observacion": "Hito cumplido satisfactoriamente",
        "usuario": "usuario@atisa.es"
    }),
    repo = Depends(get_repo),
    repo_cliente_proceso_hito = Depends(get_repo_cliente_proceso_hito)
):
    try:
        # Verificar que el cliente_proceso_hito_id existe
        cliente_proceso_hito = repo_cliente_proceso_hito.obtener_por_id(data["cliente_proceso_hito_id"])
        if not cliente_proceso_hito:
            raise HTTPException(status_code=404, detail="El cliente_proceso_hito_id especificado no existe")

        # Validar y formatear la hora si es necesario
        hora = data["hora"]
        if len(hora.split(":")) == 2:  # Si solo tiene HH:MM, agregar :00
            hora = hora + ":00"

        cumplimiento = ClienteProcesoHitoCumplimiento(
            cliente_proceso_hito_id=data["cliente_proceso_hito_id"],
            fecha=data["fecha"],
            hora=hora,
            observacion=data.get("observacion", ""),
            usuario=data["usuario"]
        )
        return repo.guardar(cumplimiento)
    except HTTPException:
        # Re-lanzar las excepciones HTTP ya manejadas
        raise
    except Exception as e:
        # Manejar errores inesperados
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.get("", summary="Listar todos los cumplimientos",
    description="Devuelve todos los registros de cumplimiento de hitos con soporte para paginación y ordenación.")
def listar(
    page: Optional[int] = Query(None, ge=1, description="Página actual"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Cantidad de resultados por página (máximo 10000)"),
    sort_field: Optional[str] = Query(None, description="Campo por el cual ordenar (id, cliente_proceso_hito_id, fecha, hora, observacion, usuario)"),
    sort_direction: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Dirección de ordenación: asc o desc"),
    repo = Depends(get_repo)
):
    cumplimientos = repo.listar()
    total = len(cumplimientos)

    # Aplicar ordenación si se especifica
    if sort_field and hasattr(cumplimientos[0] if cumplimientos else None, sort_field):
        reverse = sort_direction == "desc"

        # Función de ordenación que maneja valores None
        def sort_key(cumplimiento):
            value = getattr(cumplimiento, sort_field, None)
            if value is None:
                return ""  # Los valores None van al final
            # Si es numérico (como id, cliente_proceso_hito_id), convertir a número para ordenación correcta
            if sort_field in ["id", "cliente_proceso_hito_id"]:
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return 0
            # Para campos de texto/fecha/hora, convertir a string para ordenación
            return str(value).lower() if isinstance(value, str) else str(value)

        cumplimientos.sort(key=sort_key, reverse=reverse)

    # Aplicar paginación después de ordenar
    if page is not None and limit is not None:
        start = (page - 1) * limit
        end = start + limit
        cumplimientos = cumplimientos[start:end]

    if not cumplimientos:
        raise HTTPException(status_code=404, detail="No se encontraron cumplimientos")

    # Convertir modelos a diccionarios para incluir atributos dinámicos como num_documentos
    cumplimientos_dict = []
    for cumplimiento in cumplimientos:
        cumplimiento_dict = {
            "id": cumplimiento.id,
            "cliente_proceso_hito_id": cumplimiento.cliente_proceso_hito_id,
            "fecha": cumplimiento.fecha.isoformat() if cumplimiento.fecha else None,
            "hora": str(cumplimiento.hora) if cumplimiento.hora else None,
            "observacion": cumplimiento.observacion,
            "usuario": cumplimiento.usuario,
            "fecha_creacion": cumplimiento.fecha_creacion.isoformat() if cumplimiento.fecha_creacion else None,
            "num_documentos": getattr(cumplimiento, 'num_documentos', 0)
        }
        cumplimientos_dict.append(cumplimiento_dict)

    return {
        "total": total,
        "cumplimientos": cumplimientos_dict
    }

@router.get("/{id}", summary="Obtener cumplimiento por ID",
    description="Devuelve un registro de cumplimiento de hito específico según su ID.")
def obtener(
    id: int = Path(..., description="ID del cumplimiento a consultar"),
    repo = Depends(get_repo)
):
    cumplimiento = repo.obtener_por_id(id)
    if not cumplimiento:
        raise HTTPException(status_code=404, detail="Cumplimiento no encontrado")

    # Convertir modelo a diccionario para incluir num_documentos
    return {
        "id": cumplimiento.id,
        "cliente_proceso_hito_id": cumplimiento.cliente_proceso_hito_id,
        "fecha": cumplimiento.fecha.isoformat() if cumplimiento.fecha else None,
        "hora": str(cumplimiento.hora) if cumplimiento.hora else None,
        "observacion": cumplimiento.observacion,
        "usuario": cumplimiento.usuario,
        "fecha_creacion": cumplimiento.fecha_creacion.isoformat() if cumplimiento.fecha_creacion else None,
        "num_documentos": getattr(cumplimiento, 'num_documentos', 0)
    }

@router.get("/cliente-proceso-hito/{id}",
    summary="Obtener cumplimiento por ID de cliente_proceso_hito",
    description="Devuelve registros de cumplimiento de hito específicos según su ID de cliente_proceso_hito con soporte para paginación y ordenación.")
def obtener_por_cliente_proceso_hito(
    id: int = Path(..., description="ID de cliente_proceso_hito a consultar"),
    page: Optional[int] = Query(None, ge=1, description="Página actual"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Cantidad de resultados por página (máximo 10000)"),
    sort_field: Optional[str] = Query(None, description="Campo por el cual ordenar (id, cliente_proceso_hito_id, fecha, hora, observacion, usuario)"),
    sort_direction: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Dirección de ordenación: asc o desc"),
    repo = Depends(get_repo)
):
    try:
        cumplimientos = repo.obtener_por_cliente_proceso_hito_id(id)

        # Asegurar que cumplimientos es una lista
        if cumplimientos is None:
            cumplimientos = []
        elif not isinstance(cumplimientos, list):
            cumplimientos = [cumplimientos] if cumplimientos else []

        total = len(cumplimientos)

        # Aplicar ordenación si se especifica y hay datos para ordenar
        if sort_field and cumplimientos:
            # Verificar que el campo existe en el primer elemento
            if hasattr(cumplimientos[0], sort_field):
                reverse = sort_direction == "desc"

                def sort_key(cumplimiento):
                    value = getattr(cumplimiento, sort_field, None)

                    # Manejo especial para campos numéricos
                    if sort_field in ["id", "cliente_proceso_hito_id"]:
                        try:
                            return int(value) if value is not None else (-1 if not reverse else float('inf'))
                        except (ValueError, TypeError):
                            return -1 if not reverse else float('inf')

                    # Manejo especial para fechas
                    elif sort_field == "fecha":
                        if value is None:
                            return datetime.min if not reverse else datetime.max
                        try:
                            if isinstance(value, str):
                                return datetime.fromisoformat(value.replace('Z', '+00:00'))
                            elif isinstance(value, date):
                                return datetime.combine(value, datetime.min.time())
                            elif hasattr(value, 'timestamp'):
                                return value
                            else:
                                return datetime.min if not reverse else datetime.max
                        except (ValueError, TypeError):
                            return datetime.min if not reverse else datetime.max

                    # Manejo especial para horas
                    elif sort_field == "hora":
                        if value is None:
                            return -1 if not reverse else float('inf')
                        try:
                            if isinstance(value, str):
                                parts = value.split(':')
                                hours = int(parts[0]) if len(parts) > 0 else 0
                                minutes = int(parts[1]) if len(parts) > 1 else 0
                                seconds = int(parts[2]) if len(parts) > 2 else 0
                                return hours * 3600 + minutes * 60 + seconds
                            else:
                                return -1 if not reverse else float('inf')
                        except (ValueError, TypeError, IndexError):
                            return -1 if not reverse else float('inf')

                    # Para campos de texto
                    else:
                        return str(value).lower() if value is not None else ""

                cumplimientos.sort(key=sort_key, reverse=reverse)

        # Aplicar paginación después de ordenar
        if page is not None and limit is not None:
            start = (page - 1) * limit
            end = start + limit
            cumplimientos = cumplimientos[start:end]

        # Convertir modelos a diccionarios para incluir atributos dinámicos como num_documentos
        cumplimientos_dict = []
        for cumplimiento in cumplimientos:
            cumplimiento_dict = {
                "id": cumplimiento.id,
                "cliente_proceso_hito_id": cumplimiento.cliente_proceso_hito_id,
                "fecha": cumplimiento.fecha.isoformat() if cumplimiento.fecha else None,
                "hora": str(cumplimiento.hora) if cumplimiento.hora else None,
                "observacion": cumplimiento.observacion,
                "usuario": cumplimiento.usuario,
                "fecha_creacion": cumplimiento.fecha_creacion.isoformat() if cumplimiento.fecha_creacion else None,
                "num_documentos": getattr(cumplimiento, 'num_documentos', 0)
            }
            cumplimientos_dict.append(cumplimiento_dict)

        # Devolver respuesta exitosa incluso si no hay cumplimientos
        return {
            "total": total,
            "cumplimientos": cumplimientos_dict
        }

    except Exception as e:
        # Manejar errores inesperados
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.put("/{id}", summary="Actualizar cumplimiento",
    description="Actualiza un registro de cumplimiento de hito existente por su ID.")
def actualizar(
    id: int = Path(..., description="ID del cumplimiento a actualizar"),
    data: dict = Body(..., example={
        "fecha": "2023-01-02",
        "hora": "15:30:00",
        "observacion": "Observación actualizada",
        "usuario": "usuario@atisa.es"
    }),
    repo = Depends(get_repo)
):
    cumplimiento_actualizado = repo.actualizar(id, data)
    if not cumplimiento_actualizado:
        raise HTTPException(status_code=404, detail="Cumplimiento no encontrado")
    return cumplimiento_actualizado

@router.delete("/{id}", summary="Eliminar cumplimiento",
    description="Elimina un registro de cumplimiento de hito existente por su ID.")
def eliminar(
    id: int = Path(..., description="ID del cumplimiento a eliminar"),
    repo = Depends(get_repo)
):
    eliminado = repo.eliminar(id)
    if not eliminado:
        raise HTTPException(status_code=404, detail="Cumplimiento no encontrado")
    return {"mensaje": "Cumplimiento eliminado exitosamente"}

@router.get("/cliente/{cliente_id}", summary="Obtener historial de cumplimientos por cliente",
    description="Devuelve el historial completo de cumplimientos de hitos para un cliente específico con información de proceso e hito.")
def obtener_historial_por_cliente(
    cliente_id: str = Path(..., description="ID del cliente para consultar su historial"),
    page: Optional[int] = Query(None, ge=1, description="Página actual"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Cantidad de resultados por página (máximo 10000)"),
    repo = Depends(get_repo)
):
    try:
        # Obtener el historial completo del cliente
        historial_raw = repo.obtener_historial_por_cliente_id(cliente_id)

        # Convertir los resultados a diccionarios para facilitar el manejo
        historial = []
        for row in historial_raw:
            historial.append({
                "id": row.id,
                "fecha": row.fecha.isoformat() if row.fecha else None,
                "hora": str(row.hora) if row.hora else None,
                "usuario": row.usuario,
                "observacion": row.observacion,
                "fecha_creacion": row.fecha_creacion.isoformat() if row.fecha_creacion else None,
                "proceso_id": row.proceso_id,
                "proceso": row.proceso,
                "hito_id": row.hito_id,
                "hito": row.hito,
                "fecha_limite": row.fecha_limite.isoformat() if row.fecha_limite else None,
                "hora_limite": str(row.hora_limite) if row.hora_limite else None,
                "num_documentos": getattr(row, 'num_documentos', 0) or 0
            })

        total = len(historial)

        # Aplicar paginación si se especifica
        if page is not None and limit is not None:
            start = (page - 1) * limit
            end = start + limit
            historial = historial[start:end]

        if not historial:
            raise HTTPException(status_code=404, detail=f"No se encontraron cumplimientos para el cliente {cliente_id}")

        return {
            "total": total,
            "cliente_id": cliente_id,
            "cumplimientos": historial
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")
