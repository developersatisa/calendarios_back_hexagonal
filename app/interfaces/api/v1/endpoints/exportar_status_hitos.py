# app/interfaces/api/v1/endpoints/exportar_status_hitos.py

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime, date, time
from typing import Optional, List
import io

from app.infrastructure.db.database import SessionLocal
from app.infrastructure.db.repositories.cliente_proceso_repository_sql import ClienteProcesoRepositorySQL
from app.infrastructure.db.repositories.cliente_proceso_hito_repository_sql import ClienteProcesoHitoRepositorySQL
from app.infrastructure.db.repositories.cliente_proceso_hito_cumplimiento_repository_sql import ClienteProcesoHitoCumplimientoRepositorySQL
from app.infrastructure.db.models.cliente_proceso_hito_model import ClienteProcesoHitoModel
from app.infrastructure.db.models.cliente_proceso_model import ClienteProcesoModel
from app.infrastructure.db.models.proceso_model import ProcesoModel
from app.infrastructure.db.models.hito_model import HitoModel
from app.infrastructure.db.models.cliente_proceso_hito_cumplimiento_model import ClienteProcesoHitoCumplimientoModel

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
except ImportError:
    raise ImportError("openpyxl no está instalado. Instálalo con: pip install openpyxl")

router = APIRouter(prefix="/status-cliente", tags=["Exportar Status Hitos"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_repo_cp(db: Session = Depends(get_db)):
    return ClienteProcesoRepositorySQL(db)

def get_repo_cph(db: Session = Depends(get_db)):
    return ClienteProcesoHitoRepositorySQL(db)

def get_repo_cumplimiento(db: Session = Depends(get_db)):
    return ClienteProcesoHitoCumplimientoRepositorySQL(db)

def get_estado_vencimiento(fecha_limite: Optional[date], estado: str, fecha_actual: date) -> str:
    """
    Determina el estado de vencimiento de un hito.
    Devuelve: 'hoy', 'vencido', o 'futuro'
    """
    if fecha_limite is None:
        return 'futuro'

    if fecha_limite == fecha_actual:
        return 'hoy'
    elif fecha_limite < fecha_actual:
        return 'vencido'
    else:
        return 'futuro'

def is_finalizado_fuera_de_plazo(
    cumplimientos: List,
    fecha_limite: Optional[date],
    hora_limite: Optional[time]
) -> bool:
    """
    Determina si un hito finalizado fue cumplido fuera de plazo.
    Compara la fecha/hora del último cumplimiento con la fecha/hora límite.
    """
    if not cumplimientos:
        # Si no hay cumplimientos, considerar fuera de plazo por seguridad
        return True

    if fecha_limite is None:
        # Si no hay fecha límite, considerar en plazo
        return False

    # Obtener el último cumplimiento
    ultimo_cumplimiento = max(cumplimientos, key=lambda c: (c.fecha, c.hora or time.min))

    # Comparar fecha y hora del cumplimiento con fecha y hora límite
    fecha_cumplimiento = ultimo_cumplimiento.fecha
    hora_cumplimiento = ultimo_cumplimiento.hora or time.min

    # Crear datetime para comparación
    if hora_limite:
        limite_datetime = datetime.combine(fecha_limite, hora_limite)
        cumplimiento_datetime = datetime.combine(fecha_cumplimiento, hora_cumplimiento)
    else:
        # Si no hay hora límite, solo comparar fechas (hasta el final del día)
        limite_datetime = datetime.combine(fecha_limite, time.max)
        cumplimiento_datetime = datetime.combine(fecha_cumplimiento, time.max)

    # Si el cumplimiento fue después de la fecha límite, está fuera de plazo
    return cumplimiento_datetime > limite_datetime

def calcular_estado_hito(
    estado: str,
    fecha_limite: Optional[date],
    hora_limite: Optional[time],
    cumplimientos: List,
    fecha_actual: date = None
) -> str:
    """
    Calcula el estado del hito según la lógica exacta del frontend:
    1. Si estado = 'Finalizado':
       - Si isFinalizadoFueraDePlazo: "Cumplido fuera de plazo"
       - Si no: "Cumplido en plazo"
    2. Si estado = 'Nuevo' y estadoVenc = 'hoy': "Vence hoy"
    3. Si estadoVenc = 'vencido': "Pendiente fuera de plazo"
    4. Si no: "Pendiente en plazo"
    """
    if fecha_actual is None:
        fecha_actual = date.today()

    is_finalized = estado == 'Finalizado'
    is_nuevo = estado == 'Nuevo'
    estado_venc = get_estado_vencimiento(fecha_limite, estado, fecha_actual)
    finalizado_fuera = is_finalizado_fuera_de_plazo(cumplimientos, fecha_limite, hora_limite) if is_finalized else False
    vence_hoy = is_nuevo and estado_venc == 'hoy'

    # Aplicar la lógica exacta del frontend
    if is_finalized:
        if finalizado_fuera:
            return "Cumplido fuera de plazo"
        else:
            return "Cumplido en plazo"
    elif vence_hoy:
        return "Vence hoy"
    elif estado_venc == 'vencido':
        return "Pendiente fuera de plazo"
    else:
        return "Pendiente en plazo"

def formatear_fecha(fecha: Optional[date]) -> str:
    """Formatea una fecha a DD/MM/YYYY"""
    if fecha is None:
        return ""
    return fecha.strftime("%d/%m/%Y")

def formatear_hora(hora: Optional[time]) -> str:
    """Formatea una hora a HH:MM"""
    if hora is None:
        return ""
    return hora.strftime("%H:%M")

@router.get("/{cliente_id}/exportar-excel")
def exportar_status_hitos_excel(
    cliente_id: str = Path(..., description="ID del cliente"),
    hito_id: Optional[int] = Query(None, description="Filtrar por ID de hito específico"),
    proceso_nombre: Optional[str] = Query(None, description="Filtrar por nombre de proceso"),
    fecha_desde: Optional[str] = Query(None, description="Fecha límite desde (YYYY-MM-DD)"),
    fecha_hasta: Optional[str] = Query(None, description="Fecha límite hasta (YYYY-MM-DD)"),
    estados: Optional[str] = Query(None, description="Estados separados por comas"),
    tipos: Optional[str] = Query(None, description="Tipos de hito separados por comas"),
    search_term: Optional[str] = Query(None, description="Búsqueda por texto"),
    db: Session = Depends(get_db)
):
    """
    Exporta a Excel los hitos de un cliente con los filtros aplicados.

    IMPORTANTE: Este endpoint exporta TODOS los hitos que cumplan con los filtros,
    sin límites de paginación. Todos los resultados se incluyen en el archivo Excel.
    """
    try:
        # Parsear fechas
        fecha_desde_parsed = None
        fecha_hasta_parsed = None
        if fecha_desde:
            fecha_desde_parsed = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
        if fecha_hasta:
            fecha_hasta_parsed = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()

        # Parsear estados y tipos
        # Mapeo de estados con guiones bajos a estados con espacios (como se calculan)
        estado_mapping = {
            "cumplido_en_plazo": "Cumplido en plazo",
            "cumplido_fuera_plazo": "Cumplido fuera de plazo",
            "vence_hoy": "Vence hoy",
            "pendiente_fuera_plazo": "Pendiente fuera de plazo",
            "pendiente_en_plazo": "Pendiente en plazo"
        }

        estados_raw = [e.strip() for e in estados.split(",")] if estados else []
        # Convertir estados con guiones bajos a estados con espacios
        estados_list = [estado_mapping.get(estado.lower(), estado) for estado in estados_raw]
        tipos_list = [t.strip() for t in tipos.split(",")] if tipos else []

        # Obtener procesos habilitados del cliente
        repo_cp = ClienteProcesoRepositorySQL(db)
        procesos_cliente = repo_cp.listar_habilitados_por_cliente(cliente_id)

        if not procesos_cliente:
            raise HTTPException(status_code=404, detail=f"No se encontraron procesos habilitados para el cliente {cliente_id}")

        # Obtener todos los hitos habilitados de los procesos del cliente usando una query optimizada
        from app.infrastructure.db.models.proceso_hito_maestro_model import ProcesoHitoMaestroModel

        # Construir lista de IDs de procesos del cliente
        proceso_ids = [cp.id for cp in procesos_cliente]
        if not proceso_ids:
            raise HTTPException(status_code=404, detail=f"No se encontraron procesos habilitados para el cliente {cliente_id}")

        # Query optimizada para obtener todos los hitos con sus relaciones
        query = db.query(
            ClienteProcesoHitoModel,
            ProcesoModel,
            HitoModel
        ).join(
            ClienteProcesoModel, ClienteProcesoHitoModel.cliente_proceso_id == ClienteProcesoModel.id
        ).join(
            ProcesoModel, ClienteProcesoModel.proceso_id == ProcesoModel.id
        ).join(
            ProcesoHitoMaestroModel, ClienteProcesoHitoModel.hito_id == ProcesoHitoMaestroModel.hito_id
        ).join(
            HitoModel, ProcesoHitoMaestroModel.hito_id == HitoModel.id
        ).filter(
            ClienteProcesoHitoModel.cliente_proceso_id.in_(proceso_ids),
            ClienteProcesoHitoModel.habilitado == True
        )

        # Aplicar filtros adicionales
        if hito_id:
            query = query.filter(ClienteProcesoHitoModel.hito_id == hito_id)

        if proceso_nombre:
            query = query.filter(ProcesoModel.nombre.ilike(f"%{proceso_nombre}%"))

        if fecha_desde_parsed:
            query = query.filter(ClienteProcesoHitoModel.fecha_limite >= fecha_desde_parsed)

        if fecha_hasta_parsed:
            query = query.filter(ClienteProcesoHitoModel.fecha_limite <= fecha_hasta_parsed)

        if tipos_list:
            query = query.filter(ClienteProcesoHitoModel.tipo.in_(tipos_list))

        # Ordenar por fecha límite y hora límite ascendente
        # SQL Server no soporta NULLS LAST, usamos CASE para poner NULLs al final
        from sqlalchemy import case
        query = query.order_by(
            case(
                (ClienteProcesoHitoModel.fecha_limite.is_(None), 1),
                else_=0
            ),
            ClienteProcesoHitoModel.fecha_limite.asc(),
            case(
                (ClienteProcesoHitoModel.hora_limite.is_(None), 1),
                else_=0
            ),
            ClienteProcesoHitoModel.hora_limite.asc()
        )

        # Obtener TODOS los resultados sin límite de paginación
        # Usar yield_per para procesar en lotes si hay muchos registros, pero obtener todos
        resultados = query.all()

        # Obtener cumplimientos para todos los hitos de una vez
        hito_ids = [r[0].id for r in resultados]
        cumplimientos_dict = {}
        if hito_ids:
            cumplimientos = db.query(ClienteProcesoHitoCumplimientoModel).filter(
                ClienteProcesoHitoCumplimientoModel.cliente_proceso_hito_id.in_(hito_ids)
            ).all()

            for cumplimiento in cumplimientos:
                if cumplimiento.cliente_proceso_hito_id not in cumplimientos_dict:
                    cumplimientos_dict[cumplimiento.cliente_proceso_hito_id] = []
                cumplimientos_dict[cumplimiento.cliente_proceso_hito_id].append(cumplimiento)

        # Procesar resultados y aplicar filtros de estado y búsqueda
        hitos_data = []

        for hito_model, proceso_model, hito_maestro_model in resultados:
            # Obtener cumplimientos del hito
            cumplimientos = cumplimientos_dict.get(hito_model.id, [])

            # Calcular estado
            estado_calculado = calcular_estado_hito(
                hito_model.estado,
                hito_model.fecha_limite,
                hito_model.hora_limite,
                cumplimientos
            )

            # Filtrar por estados calculados
            if estados_list and estado_calculado not in estados_list:
                continue

            # Filtrar por search_term
            if search_term:
                search_lower = search_term.lower()
                if not (
                    search_lower in proceso_model.nombre.lower() or
                    search_lower in hito_maestro_model.nombre.lower() or
                    search_lower in estado_calculado.lower() or
                    search_lower in hito_model.tipo.lower()
                ):
                    continue

            # Agregar a la lista
            hitos_data.append({
                'proceso_nombre': proceso_model.nombre,
                'hito_nombre': hito_maestro_model.nombre,
                'estado_calculado': estado_calculado,
                'fecha_limite': hito_model.fecha_limite,
                'hora_limite': hito_model.hora_limite,
                'fecha_estado': hito_model.fecha_estado.date() if hito_model.fecha_estado else None,
                'tipo': hito_model.tipo
            })

        if not hitos_data:
            raise HTTPException(status_code=404, detail="No se encontraron hitos que cumplan con los filtros especificados")

        # Crear el archivo Excel
        wb = Workbook()
        ws = wb.active
        ws.title = "Status de Hitos"

        # Encabezados
        headers = ["Proceso", "Hito", "Estado", "Fecha Límite", "Hora Límite", "Fecha Estado", "Tipo"]
        ws.append(headers)

        # Formatear encabezados en negrita
        for cell in ws[1]:
            cell.font = Font(bold=True)

        # Definir colores de fondo por estado (según los colores del frontend)
        colores_estado = {
            "Cumplido en plazo": PatternFill(start_color="16a34a", end_color="16a34a", fill_type="solid"),  # Verde
            "Cumplido fuera de plazo": PatternFill(start_color="b45309", end_color="b45309", fill_type="solid"),  # Naranja
            "Vence hoy": PatternFill(start_color="dc2626", end_color="dc2626", fill_type="solid"),  # Rojo
            "Pendiente fuera de plazo": PatternFill(start_color="ef4444", end_color="ef4444", fill_type="solid"),  # Rojo claro
            "Pendiente en plazo": PatternFill(start_color="3b82f6", end_color="3b82f6", fill_type="solid"),  # Azul
        }

        # Color de texto blanco para todos los estados
        font_blanco = Font(color="FFFFFF", bold=False)

        # Agregar datos con estilos
        for hito_data in hitos_data:
            estado = hito_data['estado_calculado']
            fila_numero = ws.max_row + 1

            # Agregar la fila
            ws.append([
                hito_data['proceso_nombre'],
                hito_data['hito_nombre'],
                estado,
                formatear_fecha(hito_data['fecha_limite']),
                formatear_hora(hito_data['hora_limite']),
                formatear_fecha(hito_data['fecha_estado']),
                hito_data['tipo']
            ])

            # Aplicar color de fondo y texto blanco a toda la fila
            fill_color = colores_estado.get(estado, PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid"))
            for cell in ws[fila_numero]:
                cell.fill = fill_color
                cell.font = font_blanco
                cell.alignment = Alignment(horizontal="left", vertical="center")

        # Ajustar ancho de columnas
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if cell.value and len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width

        # Generar archivo en memoria
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        # Nombre del archivo
        fecha_actual = datetime.now().strftime('%Y-%m-%d')
        filename = f"status_hitos_cliente_{cliente_id}_{fecha_actual}.xlsx"

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Error en el formato de fecha: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el archivo Excel: {str(e)}")
