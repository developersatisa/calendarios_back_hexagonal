# app/interfaces/api/v1/endpoints/status_todos_clientes.py

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, case
import io
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill
except ImportError:
    pass
from typing import Optional, List, Dict, Any
from datetime import date, time

from app.infrastructure.db.database import SessionLocal
from app.infrastructure.db.models.cliente_proceso_hito_model import ClienteProcesoHitoModel
from app.infrastructure.db.models.cliente_proceso_model import ClienteProcesoModel
from app.infrastructure.db.models.cliente_model import ClienteModel
from app.infrastructure.db.models.proceso_model import ProcesoModel
from app.infrastructure.db.models.hito_model import HitoModel
from app.infrastructure.db.models.cliente_proceso_hito_cumplimiento_model import ClienteProcesoHitoCumplimientoModel
from app.infrastructure.db.models.documentos_cumplimiento_model import DocumentoCumplimientoModel

router = APIRouter(prefix="/status-todos-clientes", tags=["Status Todos los Clientes"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/hitos", summary="Obtener todos los hitos habilitados de todos los clientes",
            description="Devuelve todos los hitos habilitados de todos los clientes con información relacionada (cliente, proceso, hito maestro) y el último cumplimiento si existe.")
def get_status_todos_clientes(
    fecha_limite_desde: Optional[str] = Query(None, description="Filtrar por fecha límite desde (YYYY-MM-DD)"),
    fecha_limite_hasta: Optional[str] = Query(None, description="Filtrar por fecha límite hasta (YYYY-MM-DD)"),
    cliente_id: Optional[str] = Query(None, description="Filtrar por ID de cliente"),
    proceso_id: Optional[int] = Query(None, description="Filtrar por ID de proceso"),
    hito_id: Optional[int] = Query(None, description="Filtrar por ID de hito"),
    ordenar_por: Optional[str] = Query("fecha_limite", description="Campo para ordenar (fecha_limite, cliente_nombre, proceso_nombre)"),
    orden: Optional[str] = Query("asc", description="Orden (asc o desc)"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Límite de resultados"),
    offset: Optional[int] = Query(None, ge=0, description="Offset para paginación"),
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los hitos habilitados de todos los clientes con información relacionada.
    Incluye el último cumplimiento de cada hito con el número de documentos asociados.
    """
    try:
        # Subconsulta para obtener el último cumplimiento por hito con número de documentos
        subquery_ultimo_cumplimiento = (
            db.query(
                ClienteProcesoHitoCumplimientoModel.cliente_proceso_hito_id,
                func.max(ClienteProcesoHitoCumplimientoModel.id).label('ultimo_cumplimiento_id')
            )
            .group_by(ClienteProcesoHitoCumplimientoModel.cliente_proceso_hito_id)
            .subquery()
        )

        # Consulta principal con todos los JOINs necesarios
        query = (
            db.query(
                # Campos de ClienteProcesoHito
                ClienteProcesoHitoModel.id,
                ClienteProcesoHitoModel.cliente_proceso_id,
                ClienteProcesoHitoModel.hito_id,
                ClienteProcesoHitoModel.estado,
                ClienteProcesoHitoModel.fecha_estado,
                ClienteProcesoHitoModel.fecha_limite,
                ClienteProcesoHitoModel.hora_limite,
                ClienteProcesoHitoModel.tipo,
                ClienteProcesoHitoModel.habilitado,

                # Información del cliente
                ClienteModel.idcliente.label('cliente_id'),
                ClienteModel.razsoc.label('cliente_nombre'),

                # Información del proceso
                ClienteProcesoModel.proceso_id,
                ProcesoModel.nombre.label('proceso_nombre'),

                # Información del hito maestro
                HitoModel.nombre.label('hito_nombre'),

                # Último cumplimiento (si existe)
                ClienteProcesoHitoCumplimientoModel.id.label('cumplimiento_id'),
                ClienteProcesoHitoCumplimientoModel.fecha.label('cumplimiento_fecha'),
                ClienteProcesoHitoCumplimientoModel.hora.label('cumplimiento_hora'),
                ClienteProcesoHitoCumplimientoModel.observacion.label('cumplimiento_observacion'),
                ClienteProcesoHitoCumplimientoModel.usuario.label('cumplimiento_usuario'),
                ClienteProcesoHitoCumplimientoModel.fecha_creacion.label('cumplimiento_fecha_creacion'),

                # Número de documentos del último cumplimiento
                func.count(DocumentoCumplimientoModel.id).label('num_documentos')
            )
            .join(ClienteProcesoModel, ClienteProcesoHitoModel.cliente_proceso_id == ClienteProcesoModel.id)
            .join(ClienteModel, ClienteProcesoModel.cliente_id == ClienteModel.idcliente)
            .join(ProcesoModel, ClienteProcesoModel.proceso_id == ProcesoModel.id)
            .join(HitoModel, ClienteProcesoHitoModel.hito_id == HitoModel.id)
            .outerjoin(
                subquery_ultimo_cumplimiento,
                ClienteProcesoHitoModel.id == subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id
            )
            .outerjoin(
                ClienteProcesoHitoCumplimientoModel,
                ClienteProcesoHitoCumplimientoModel.id == subquery_ultimo_cumplimiento.c.ultimo_cumplimiento_id
            )
            .outerjoin(
                DocumentoCumplimientoModel,
                ClienteProcesoHitoCumplimientoModel.id == DocumentoCumplimientoModel.cumplimiento_id
            )
            .filter(ClienteProcesoHitoModel.habilitado == True)
            .group_by(
                ClienteProcesoHitoModel.id,
                ClienteProcesoHitoModel.cliente_proceso_id,
                ClienteProcesoHitoModel.hito_id,
                ClienteProcesoHitoModel.estado,
                ClienteProcesoHitoModel.fecha_estado,
                ClienteProcesoHitoModel.fecha_limite,
                ClienteProcesoHitoModel.hora_limite,
                ClienteProcesoHitoModel.tipo,
                ClienteProcesoHitoModel.habilitado,
                ClienteModel.idcliente,
                ClienteModel.razsoc,
                ClienteProcesoModel.proceso_id,
                ProcesoModel.nombre,
                HitoModel.nombre,
                ClienteProcesoHitoCumplimientoModel.id,
                ClienteProcesoHitoCumplimientoModel.fecha,
                ClienteProcesoHitoCumplimientoModel.hora,
                ClienteProcesoHitoCumplimientoModel.observacion,
                ClienteProcesoHitoCumplimientoModel.usuario,
                ClienteProcesoHitoCumplimientoModel.fecha_creacion
            )
        )

        # Aplicar filtros opcionales
        if fecha_limite_desde:
            try:
                fecha_desde = date.fromisoformat(fecha_limite_desde)
                query = query.filter(ClienteProcesoHitoModel.fecha_limite >= fecha_desde)
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de fecha_limite_desde inválido. Use YYYY-MM-DD")

        if fecha_limite_hasta:
            try:
                fecha_hasta = date.fromisoformat(fecha_limite_hasta)
                query = query.filter(ClienteProcesoHitoModel.fecha_limite <= fecha_hasta)
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de fecha_limite_hasta inválido. Use YYYY-MM-DD")

        if cliente_id:
            query = query.filter(ClienteModel.idcliente == cliente_id)

        if proceso_id:
            query = query.filter(ClienteProcesoModel.proceso_id == proceso_id)

        if hito_id:
            query = query.filter(ClienteProcesoHitoModel.hito_id == hito_id)

        # Aplicar ordenamiento
        if ordenar_por == "fecha_limite":
            order_field = ClienteProcesoHitoModel.fecha_limite
        elif ordenar_por == "cliente_nombre":
            order_field = ClienteModel.razsoc
        elif ordenar_por == "proceso_nombre":
            order_field = ProcesoModel.nombre
        else:
            order_field = ClienteProcesoHitoModel.fecha_limite

        if orden.lower() == "desc":
            query = query.order_by(order_field.desc())
        else:
            query = query.order_by(order_field.asc())

        # Obtener total antes de aplicar paginación
        total = query.count()

        # Aplicar paginación si se especifica
        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        # Ejecutar consulta
        resultados = query.all()

        # Construir respuesta
        hitos_response = []
        for row in resultados:
            # Construir objeto de último cumplimiento si existe
            ultimo_cumplimiento = None
            if row.cumplimiento_id:
                ultimo_cumplimiento = {
                    "id": row.cumplimiento_id,
                    "fecha": row.cumplimiento_fecha.isoformat() if row.cumplimiento_fecha else None,
                    "hora": str(row.cumplimiento_hora) if row.cumplimiento_hora else None,
                    "observacion": row.cumplimiento_observacion,
                    "usuario": row.cumplimiento_usuario,
                    "fecha_creacion": row.cumplimiento_fecha_creacion.isoformat() if row.cumplimiento_fecha_creacion else None,
                    "num_documentos": int(row.num_documentos or 0)
                }

            hito_dict = {
                # Campos de ClienteProcesoHito
                "id": row.id,
                "cliente_proceso_id": row.cliente_proceso_id,
                "hito_id": row.hito_id,
                "estado": row.estado,
                "fecha_estado": row.fecha_estado.isoformat() if row.fecha_estado else None,
                "fecha_limite": row.fecha_limite.isoformat() if row.fecha_limite else None,
                "hora_limite": str(row.hora_limite) if row.hora_limite else None,
                "tipo": row.tipo,
                "habilitado": bool(row.habilitado),

                # Información del cliente
                "cliente_id": str(row.cliente_id or ""),
                "cliente_nombre": str(row.cliente_nombre or "").strip(),

                # Información del proceso
                "proceso_id": row.proceso_id,
                "proceso_nombre": str(row.proceso_nombre or "").strip(),

                # Información del hito maestro
                "hito_nombre": str(row.hito_nombre or "").strip(),

                # Último cumplimiento
                "ultimo_cumplimiento": ultimo_cumplimiento
            }
            hitos_response.append(hito_dict)

        return {
            "hitos": hitos_response,
            "total": total
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener hitos: {str(e)}")


@router.get("/exportar-excel", summary="Exportar status de todos los clientes a Excel")
def exportar_status_todos_excel(
    fecha_desde: Optional[str] = Query(None, description="Filtrar por fecha límite desde (YYYY-MM-DD)"),
    fecha_hasta: Optional[str] = Query(None, description="Filtrar por fecha límite hasta (YYYY-MM-DD)"),
    cliente_id: Optional[str] = Query(None, description="Filtrar por ID de cliente"),
    proceso_id: Optional[int] = Query(None, description="Filtrar por ID de proceso"),
    hito_id: Optional[int] = Query(None, description="Filtrar por ID de hito"),
    db: Session = Depends(get_db)
):
    """
    Exporta a Excel la misma información que el listado de hitos de todos los clientes.
    """
    try:
        # Reutilizamos la lógica de consulta (sin paginación)
        query = (
            db.query(
                ClienteModel.razsoc.label('cliente_nombre'),
                ProcesoModel.nombre.label('proceso_nombre'),
                HitoModel.nombre.label('hito_nombre'),
                ClienteProcesoHitoModel.estado,
                ClienteProcesoHitoModel.fecha_limite,
                ClienteProcesoHitoModel.hora_limite,
                ClienteProcesoHitoModel.fecha_estado,
                ClienteProcesoHitoModel.tipo,
                ClienteProcesoHitoCumplimientoModel.fecha.label('cumplimiento_fecha')
            )
            .join(ClienteProcesoModel, ClienteProcesoHitoModel.cliente_proceso_id == ClienteProcesoModel.id)
            .join(ClienteModel, ClienteProcesoModel.cliente_id == ClienteModel.idcliente)
            .join(ProcesoModel, ClienteProcesoModel.proceso_id == ProcesoModel.id)
            .join(HitoModel, ClienteProcesoHitoModel.hito_id == HitoModel.id)
            .outerjoin(ClienteProcesoHitoCumplimientoModel, ClienteProcesoHitoCumplimientoModel.cliente_proceso_hito_id == ClienteProcesoHitoModel.id)
            .filter(ClienteProcesoHitoModel.habilitado == True)
        )

        def calculate_status(estado_base, fecha_limite, hora_limite, fecha_cumplimiento):
            from datetime import date as dt_date, datetime as dt_datetime

            if estado_base == 'Finalizado':
                if not fecha_cumplimiento:
                    # Fallback logic if completion date is missing but status is Finalized
                    # You might want to default to "Cumplido en plazo" or just return "Finalizado"
                    # depending on business rules. For now, let's assume it was on time if no date.
                    return "Finalizado"

                # Check if fulfilled on time
                # Build deadline datetime
                if not fecha_limite:
                    return "Finalizado"

                deadline = dt_datetime.combine(fecha_limite, hora_limite) if hora_limite else dt_datetime.combine(fecha_limite, time(23, 59, 59))

                # Assuming fulfillment is a date, we compare with the date part or combine with min time
                # If fulfillment is a datetime, use it directly.
                # Based on models, often fulfillment date is just a date.
                if isinstance(fecha_cumplimiento, dt_date) and not isinstance(fecha_cumplimiento, dt_datetime):
                     fulfillment_dt = dt_datetime.combine(fecha_cumplimiento, time(0, 0, 0))
                else:
                     fulfillment_dt = fecha_cumplimiento

                if fulfillment_dt > deadline:
                    return "Cumplido fuera de plazo"
                else:
                    return "Cumplido en plazo"

            else:
                # Not finalized (Pending, New, etc.)
                if not fecha_limite:
                    return estado_base

                today = dt_date.today()

                if fecha_limite == today:
                    return "Vence hoy"
                elif fecha_limite < today:
                    return "Pendiente fuera de plazo"
                else:
                    return "Pendiente en plazo"

        # Filtros
        if fecha_desde:
            query = query.filter(ClienteProcesoHitoModel.fecha_limite >= date.fromisoformat(fecha_desde))
        if fecha_hasta:
            query = query.filter(ClienteProcesoHitoModel.fecha_limite <= date.fromisoformat(fecha_hasta))
        if cliente_id:
            query = query.filter(ClienteModel.idcliente == cliente_id)
        if proceso_id:
            query = query.filter(ClienteProcesoModel.proceso_id == proceso_id)
        if hito_id:
            query = query.filter(ClienteProcesoHitoModel.hito_id == hito_id)

        # Aplicar ordenamiento predeterminado de /hitos (fecha_limite asc)
        query = query.order_by(ClienteProcesoHitoModel.fecha_limite.asc())

        resultados = query.all()

        # Crear Excel
        wb = Workbook()
        ws = wb.active
        ws.title = "Status Todos los Clientes"

        headers = ["Cliente", "Proceso", "Hito", "Estado", "Fecha Límite", "Hora Límite", "Fecha Estado", "Tipo"]
        ws.append(headers)

        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center")

        # Definir colores de fondo por estado
        colores_estado = {
            "Cumplido en plazo": PatternFill(start_color="16a34a", end_color="16a34a", fill_type="solid"),  # Verde
            "Cumplido fuera de plazo": PatternFill(start_color="b45309", end_color="b45309", fill_type="solid"),  # Naranja
            "Vence hoy": PatternFill(start_color="dc2626", end_color="dc2626", fill_type="solid"),  # Rojo
            "Pendiente fuera de plazo": PatternFill(start_color="ef4444", end_color="ef4444", fill_type="solid"),  # Rojo claro
            "Pendiente en plazo": PatternFill(start_color="00a1de", end_color="00a1de", fill_type="solid"),  # Azul Atisa
        }
        font_blanco = Font(color="FFFFFF", bold=False)

        for r in resultados:
            estado_calculado = calculate_status(r.estado, r.fecha_limite, r.hora_limite, r.cumplimiento_fecha)
            ws.append([
                str(r.cliente_nombre or "").strip(),
                str(r.proceso_nombre or "").strip(),
                str(r.hito_nombre or "").strip(),
                estado_calculado,
                r.fecha_limite.strftime("%d/%m/%Y") if r.fecha_limite else "",
                r.hora_limite.strftime("%H:%M") if r.hora_limite else "",
                r.fecha_estado.strftime("%d/%m/%Y") if r.fecha_estado else "",
                r.tipo
            ])

            # Aplicar estilos a la fila recién agregada
            fila_numero = ws.max_row
            fill_color = colores_estado.get(estado_calculado)

            if fill_color:
                for cell in ws[fila_numero]:
                    cell.fill = fill_color
                    cell.font = font_blanco

        # Auto-ajustar columnas
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except: pass
            ws.column_dimensions[column].width = min(max_length + 2, 50)

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        filename = f"status_todos_clientes_{date.today().strftime('%Y-%m-%d')}.xlsx"
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename={filename}',
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al exportar Excel: {str(e)}")
