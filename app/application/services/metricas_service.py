from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text, func, case, and_, or_, Date
from app.infrastructure.db.models.cliente_proceso_hito_model import ClienteProcesoHitoModel
from app.infrastructure.db.models.cliente_proceso_model import ClienteProcesoModel
from app.infrastructure.db.models.proceso_model import ProcesoModel
from app.infrastructure.db.models.cliente_model import ClienteModel
from app.infrastructure.db.models.cliente_proceso_hito_cumplimiento_model import ClienteProcesoHitoCumplimientoModel

class MetricasService:
    def __init__(self, db: Session):
        self.db = db

    def _calcular_tendencia(self, valor_actual: float, valor_anterior: float) -> str:
        """Calcula la tendencia porcentual entre dos valores"""
        if valor_anterior == 0:
            if valor_actual > 0:
                return "+100.0%"
            else:
                return "0.0%"

        cambio = ((valor_actual - valor_anterior) / valor_anterior) * 100
        signo = "+" if cambio >= 0 else ""
        return f"{signo}{cambio:.1f}%"

    def get_cumplimiento_hitos(self, cliente_id: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene porcentaje de cumplimiento de hitos basado en los últimos cumplimientos"""
        fecha_actual = date.today()
        fecha_30_dias = fecha_actual - timedelta(days=30)
        fecha_60_dias = fecha_actual - timedelta(days=60)

        # Subconsulta para obtener el último cumplimiento por hito
        subquery_ultimo_cumplimiento = (
            self.db.query(
                ClienteProcesoHitoCumplimientoModel.cliente_proceso_hito_id,
                func.max(ClienteProcesoHitoCumplimientoModel.id).label('ultimo_cumplimiento_id')
            )
            .group_by(ClienteProcesoHitoCumplimientoModel.cliente_proceso_hito_id)
            .subquery()
        )

        # Consulta general: hitos totales vs hitos con último cumplimiento
        query_general = (
            self.db.query(
                func.count(ClienteProcesoHitoModel.id).label('hitos_totales'),
                func.count(subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id).label('hitos_completados')
            )
            .join(ClienteProcesoModel, ClienteProcesoHitoModel.cliente_proceso_id == ClienteProcesoModel.id)
            .outerjoin(
                subquery_ultimo_cumplimiento,
                ClienteProcesoHitoModel.id == subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id
            )
            .filter(ClienteProcesoHitoModel.habilitado == True)
        )

        if cliente_id:
            query_general = query_general.filter(ClienteProcesoModel.cliente_id == cliente_id)

        result_general = query_general.first()
        porcentaje_general = 0.0
        if result_general and result_general.hitos_totales and result_general.hitos_totales > 0:
            porcentaje_general = round((result_general.hitos_completados or 0) * 100.0 / result_general.hitos_totales, 2)

        # Consulta para últimos 30 días
        query_actual = (
            self.db.query(
                func.count(ClienteProcesoHitoModel.id).label('hitos_totales'),
                func.count(subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id).label('hitos_completados')
            )
            .join(ClienteProcesoModel, ClienteProcesoHitoModel.cliente_proceso_id == ClienteProcesoModel.id)
            .outerjoin(
                subquery_ultimo_cumplimiento,
                ClienteProcesoHitoModel.id == subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id
            )
            .filter(
                ClienteProcesoHitoModel.habilitado == True,
                ClienteProcesoHitoModel.fecha_limite >= fecha_30_dias
            )
        )

        if cliente_id:
            query_actual = query_actual.filter(ClienteProcesoModel.cliente_id == cliente_id)

        result_actual = query_actual.first()
        porcentaje_actual = 0.0
        if result_actual and result_actual.hitos_totales and result_actual.hitos_totales > 0:
            porcentaje_actual = (result_actual.hitos_completados or 0) * 100.0 / result_actual.hitos_totales

        # Consulta para 30 días anteriores (días 31-60)
        query_anterior = (
            self.db.query(
                func.count(ClienteProcesoHitoModel.id).label('hitos_totales'),
                func.count(subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id).label('hitos_completados')
            )
            .join(ClienteProcesoModel, ClienteProcesoHitoModel.cliente_proceso_id == ClienteProcesoModel.id)
            .outerjoin(
                subquery_ultimo_cumplimiento,
                ClienteProcesoHitoModel.id == subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id
            )
            .filter(
                ClienteProcesoHitoModel.habilitado == True,
                ClienteProcesoHitoModel.fecha_limite >= fecha_60_dias,
                ClienteProcesoHitoModel.fecha_limite < fecha_30_dias
            )
        )

        if cliente_id:
            query_anterior = query_anterior.filter(ClienteProcesoModel.cliente_id == cliente_id)

        result_anterior = query_anterior.first()
        porcentaje_anterior = 0.0
        if result_anterior and result_anterior.hitos_totales and result_anterior.hitos_totales > 0:
            porcentaje_anterior = (result_anterior.hitos_completados or 0) * 100.0 / result_anterior.hitos_totales

        tendencia = self._calcular_tendencia(porcentaje_actual, porcentaje_anterior)

        # Consulta por cliente para cumplimiento
        query_clientes = (
            self.db.query(
                ClienteModel.idcliente.label('cliente_id'),
                ClienteModel.razsoc.label('cliente_nombre'),
                func.count(ClienteProcesoHitoModel.id).label('hitos_totales'),
                func.count(subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id).label('hitos_completados')
            )
            .join(ClienteProcesoModel, ClienteModel.idcliente == ClienteProcesoModel.cliente_id)
            .join(ClienteProcesoHitoModel, ClienteProcesoModel.id == ClienteProcesoHitoModel.cliente_proceso_id)
            .outerjoin(
                subquery_ultimo_cumplimiento,
                ClienteProcesoHitoModel.id == subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id
            )
            .filter(ClienteProcesoHitoModel.habilitado == True)
            .group_by(ClienteModel.idcliente, ClienteModel.razsoc)
            .having(func.count(ClienteProcesoHitoModel.id) > 0)
            .order_by(ClienteModel.razsoc)
        )

        if cliente_id:
            query_clientes = query_clientes.filter(ClienteModel.idcliente == cliente_id)

        result_clientes = query_clientes.all()
        clientes_data = []
        for row in result_clientes:
            porcentaje_cliente = 0.0
            if row.hitos_totales and row.hitos_totales > 0:
                porcentaje_cliente = round((row.hitos_completados or 0) * 100.0 / row.hitos_totales, 2)

            clientes_data.append({
                "clienteId": str(row.cliente_id or ""),
                "clienteNombre": str(row.cliente_nombre or "").strip(),
                "porcentaje": porcentaje_cliente,
                "hitosTotales": int(row.hitos_totales or 0),
                "hitosCompletados": int(row.hitos_completados or 0)
            })

        return {
            "porcentajeGeneral": porcentaje_general,
            "tendencia": tendencia,
            "clientesData": clientes_data
        }

    def get_hitos_por_proceso(self, cliente_id: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene total de hitos abiertos/pendientes por tipo de proceso basado en últimos cumplimientos"""
        fecha_actual = date.today()
        fecha_30_dias = fecha_actual - timedelta(days=30)
        fecha_60_dias = fecha_actual - timedelta(days=60)

        # Subconsulta para obtener el último cumplimiento por hito
        subquery_ultimo_cumplimiento = (
            self.db.query(
                ClienteProcesoHitoCumplimientoModel.cliente_proceso_hito_id,
                func.max(ClienteProcesoHitoCumplimientoModel.id).label('ultimo_cumplimiento_id')
            )
            .group_by(ClienteProcesoHitoCumplimientoModel.cliente_proceso_hito_id)
            .subquery()
        )

        # Consulta principal por proceso
        query = (
            self.db.query(
                ProcesoModel.id.label('proceso_id'),
                ProcesoModel.nombre.label('proceso_nombre'),
                func.count(
                    case(
                        (subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id.is_(None), ClienteProcesoHitoModel.id),
                        else_=None
                    )
                ).label('hitos_pendientes'),
                func.count(subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id).label('hitos_completados')
            )
            .join(ClienteProcesoModel, ProcesoModel.id == ClienteProcesoModel.proceso_id)
            .join(ClienteProcesoHitoModel, ClienteProcesoModel.id == ClienteProcesoHitoModel.cliente_proceso_id)
            .outerjoin(
                subquery_ultimo_cumplimiento,
                ClienteProcesoHitoModel.id == subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id
            )
            .filter(ClienteProcesoHitoModel.habilitado == True)
            .group_by(ProcesoModel.id, ProcesoModel.nombre)
            .order_by(ProcesoModel.nombre)
        )

        if cliente_id:
            query = query.filter(ClienteProcesoModel.cliente_id == cliente_id)

        result = query.all()
        total_pendientes = sum(row.hitos_pendientes or 0 for row in result)

        proceso_data = []
        for row in result:
            proceso_data.append({
                "nombreProceso": str(row.proceso_nombre or "").strip(),
                "hitosPendientes": int(row.hitos_pendientes or 0),
                "hitosCompletados": int(row.hitos_completados or 0)
            })

        # Calcular tendencia para hitos pendientes
        query_actual_pend = (
            self.db.query(
                func.count(
                    case(
                        (subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id.is_(None), ClienteProcesoHitoModel.id),
                        else_=None
                    )
                ).label('pendientes_actual')
            )
            .join(ClienteProcesoModel, ClienteProcesoHitoModel.cliente_proceso_id == ClienteProcesoModel.id)
            .outerjoin(
                subquery_ultimo_cumplimiento,
                ClienteProcesoHitoModel.id == subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id
            )
            .filter(
                ClienteProcesoHitoModel.habilitado == True,
                ClienteProcesoHitoModel.fecha_limite >= fecha_30_dias
            )
        )

        if cliente_id:
            query_actual_pend = query_actual_pend.filter(ClienteProcesoModel.cliente_id == cliente_id)

        query_anterior_pend = (
            self.db.query(
                func.count(
                    case(
                        (subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id.is_(None), ClienteProcesoHitoModel.id),
                        else_=None
                    )
                ).label('pendientes_anterior')
            )
            .join(ClienteProcesoModel, ClienteProcesoHitoModel.cliente_proceso_id == ClienteProcesoModel.id)
            .outerjoin(
                subquery_ultimo_cumplimiento,
                ClienteProcesoHitoModel.id == subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id
            )
            .filter(
                ClienteProcesoHitoModel.habilitado == True,
                ClienteProcesoHitoModel.fecha_limite >= fecha_60_dias,
                ClienteProcesoHitoModel.fecha_limite < fecha_30_dias
            )
        )

        if cliente_id:
            query_anterior_pend = query_anterior_pend.filter(ClienteProcesoModel.cliente_id == cliente_id)

        result_actual_pend = query_actual_pend.first()
        result_anterior_pend = query_anterior_pend.first()

        pendientes_actual = result_actual_pend.pendientes_actual or 0 if result_actual_pend else 0
        pendientes_anterior = result_anterior_pend.pendientes_anterior or 0 if result_anterior_pend else 0

        tendencia = self._calcular_tendencia(float(pendientes_actual), float(pendientes_anterior))

        # Consulta por cliente para hitos por proceso
        query_clientes_proceso = (
            self.db.query(
                ClienteModel.idcliente.label('cliente_id'),
                ClienteModel.razsoc.label('cliente_nombre'),
                ProcesoModel.id.label('proceso_id'),
                ProcesoModel.nombre.label('proceso_nombre'),
                func.count(
                    case(
                        (subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id.is_(None), ClienteProcesoHitoModel.id),
                        else_=None
                    )
                ).label('hitos_pendientes'),
                func.count(subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id).label('hitos_completados')
            )
            .join(ClienteProcesoModel, ClienteModel.idcliente == ClienteProcesoModel.cliente_id)
            .join(ProcesoModel, ClienteProcesoModel.proceso_id == ProcesoModel.id)
            .join(ClienteProcesoHitoModel, ClienteProcesoModel.id == ClienteProcesoHitoModel.cliente_proceso_id)
            .outerjoin(
                subquery_ultimo_cumplimiento,
                ClienteProcesoHitoModel.id == subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id
            )
            .filter(ClienteProcesoHitoModel.habilitado == True)
            .group_by(ClienteModel.idcliente, ClienteModel.razsoc, ProcesoModel.id, ProcesoModel.nombre)
            .order_by(ClienteModel.razsoc, ProcesoModel.nombre)
        )

        if cliente_id:
            query_clientes_proceso = query_clientes_proceso.filter(ClienteModel.idcliente == cliente_id)

        result_clientes_proceso = query_clientes_proceso.all()
        clientes_data = []
        cliente_actual = None
        procesos_cliente = []

        for row in result_clientes_proceso:
            if cliente_actual != row.cliente_id:
                if cliente_actual is not None:
                    clientes_data.append({
                        "clienteId": str(cliente_actual),
                        "clienteNombre": nombre_cliente_actual,
                        "procesosData": procesos_cliente
                    })
                cliente_actual = row.cliente_id
                nombre_cliente_actual = str(row.cliente_nombre or "").strip()
                procesos_cliente = []

            procesos_cliente.append({
                "nombreProceso": str(row.proceso_nombre or "").strip(),
                "hitosPendientes": int(row.hitos_pendientes or 0),
                "hitosCompletados": int(row.hitos_completados or 0)
            })

        # Agregar el último cliente
        if cliente_actual is not None:
            clientes_data.append({
                "clienteId": str(cliente_actual),
                "clienteNombre": nombre_cliente_actual,
                "procesosData": procesos_cliente
            })

        return {
            "totalPendientes": total_pendientes,
            "tendencia": tendencia,
            "procesoData": proceso_data,
            "clientesData": clientes_data
        }

    def get_tiempo_resolucion(self, cliente_id: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene tiempo medio de resolución de hitos basado en últimos cumplimientos"""
        fecha_actual = date.today()
        fecha_30_dias = fecha_actual - timedelta(days=30)
        fecha_60_dias = fecha_actual - timedelta(days=60)
        fecha_6_meses = fecha_actual - timedelta(days=180)

        # Obtener último cumplimiento por hito con su fecha
        sql = """
        WITH ultimo_cumplimiento AS (
            SELECT
                cliente_proceso_hito_id,
                MAX(id) AS ultimo_id
            FROM cliente_proceso_hito_cumplimiento
            GROUP BY cliente_proceso_hito_id
        )
        SELECT
            FORMAT(cph.fecha_limite, 'yyyy-MM') AS periodo,
            AVG(DATEDIFF(day, cph.fecha_limite, CAST(cpc.fecha AS DATE))) AS tiempo_medio
        FROM cliente_proceso_hito cph
        JOIN cliente_proceso cp ON cp.id = cph.cliente_proceso_id
        JOIN ultimo_cumplimiento uc ON uc.cliente_proceso_hito_id = cph.id
        JOIN cliente_proceso_hito_cumplimiento cpc ON cpc.id = uc.ultimo_id
        WHERE cph.habilitado = 1
          AND cph.fecha_limite >= :fecha_6_meses
        """

        params = {"fecha_6_meses": fecha_6_meses}
        if cliente_id:
            sql += " AND cp.cliente_id = :cliente_id"
            params["cliente_id"] = cliente_id

        sql += """
        GROUP BY FORMAT(cph.fecha_limite, 'yyyy-MM')
        ORDER BY FORMAT(cph.fecha_limite, 'yyyy-MM')
        """

        result = self.db.execute(text(sql), params).fetchall()
        tiempo_medio_general = 0.0
        resolucion_data = []

        if result:
            total_tiempo = sum(float(row.tiempo_medio or 0) for row in result)
            tiempo_medio_general = round(total_tiempo / len(result), 2) if len(result) > 0 else 0.0

            meses = {
                "01": "Ene", "02": "Feb", "03": "Mar", "04": "Abr",
                "05": "May", "06": "Jun", "07": "Jul", "08": "Ago",
                "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dic"
            }

            for row in result:
                if row.tiempo_medio and row.periodo:
                    mes_num = row.periodo.split('-')[1] if '-' in row.periodo else "01"
                    mes_nombre = meses.get(mes_num, row.periodo)
                    resolucion_data.append({
                        "periodo": mes_nombre,
                        "tiempoMedio": round(float(row.tiempo_medio), 2)
                    })

        # Calcular tendencia usando SQL crudo
        sql_actual_tiempo = """
        WITH ultimo_cumplimiento AS (
            SELECT
                cliente_proceso_hito_id,
                MAX(id) AS ultimo_id
            FROM cliente_proceso_hito_cumplimiento
            GROUP BY cliente_proceso_hito_id
        )
        SELECT AVG(DATEDIFF(day, cph.fecha_limite, CAST(cpc.fecha AS DATE))) AS tiempo_actual
        FROM cliente_proceso_hito cph
        JOIN cliente_proceso cp ON cp.id = cph.cliente_proceso_id
        JOIN ultimo_cumplimiento uc ON uc.cliente_proceso_hito_id = cph.id
        JOIN cliente_proceso_hito_cumplimiento cpc ON cpc.id = uc.ultimo_id
        WHERE cph.habilitado = 1
          AND CAST(cpc.fecha AS DATE) >= :fecha_30_dias
        """

        params_actual = {"fecha_30_dias": fecha_30_dias}
        if cliente_id:
            sql_actual_tiempo += " AND cp.cliente_id = :cliente_id"
            params_actual["cliente_id"] = cliente_id

        sql_anterior_tiempo = """
        WITH ultimo_cumplimiento AS (
            SELECT
                cliente_proceso_hito_id,
                MAX(id) AS ultimo_id
            FROM cliente_proceso_hito_cumplimiento
            GROUP BY cliente_proceso_hito_id
        )
        SELECT AVG(DATEDIFF(day, cph.fecha_limite, CAST(cpc.fecha AS DATE))) AS tiempo_anterior
        FROM cliente_proceso_hito cph
        JOIN cliente_proceso cp ON cp.id = cph.cliente_proceso_id
        JOIN ultimo_cumplimiento uc ON uc.cliente_proceso_hito_id = cph.id
        JOIN cliente_proceso_hito_cumplimiento cpc ON cpc.id = uc.ultimo_id
        WHERE cph.habilitado = 1
          AND CAST(cpc.fecha AS DATE) >= :fecha_60_dias
          AND CAST(cpc.fecha AS DATE) < :fecha_30_dias
        """

        params_anterior = {"fecha_30_dias": fecha_30_dias, "fecha_60_dias": fecha_60_dias}
        if cliente_id:
            sql_anterior_tiempo += " AND cp.cliente_id = :cliente_id"
            params_anterior["cliente_id"] = cliente_id

        result_actual_tiempo = self.db.execute(text(sql_actual_tiempo), params_actual).fetchone()
        result_anterior_tiempo = self.db.execute(text(sql_anterior_tiempo), params_anterior).fetchone()

        tiempo_actual = float(result_actual_tiempo.tiempo_actual or 0) if result_actual_tiempo else 0.0
        tiempo_anterior = float(result_anterior_tiempo.tiempo_anterior or 0) if result_anterior_tiempo else 0.0

        tendencia_tiempo = self._calcular_tendencia(tiempo_actual, tiempo_anterior)

        # Consulta por cliente para tiempo de resolución
        sql_clientes = """
        WITH ultimo_cumplimiento AS (
            SELECT
                cliente_proceso_hito_id,
                MAX(id) AS ultimo_id
            FROM cliente_proceso_hito_cumplimiento
            GROUP BY cliente_proceso_hito_id
        )
        SELECT
            c.idcliente AS cliente_id,
            c.razsoc AS cliente_nombre,
            FORMAT(cph.fecha_limite, 'yyyy-MM') AS periodo,
            AVG(DATEDIFF(day, cph.fecha_limite, CAST(cpc.fecha AS DATE))) AS tiempo_medio
        FROM cliente_proceso_hito cph
        JOIN ultimo_cumplimiento uc ON uc.cliente_proceso_hito_id = cph.id
        JOIN cliente_proceso_hito_cumplimiento cpc ON cpc.id = uc.ultimo_id
        JOIN cliente_proceso cp ON cp.id = cph.cliente_proceso_id
        JOIN clientes c ON c.idcliente = cp.cliente_id
        WHERE cph.habilitado = 1
          AND cph.fecha_limite >= :fecha_6_meses
        """

        params_clientes = {"fecha_6_meses": fecha_6_meses}
        if cliente_id:
            sql_clientes += " AND cp.cliente_id = :cliente_id"
            params_clientes["cliente_id"] = cliente_id

        sql_clientes += """
        GROUP BY c.idcliente, c.razsoc, FORMAT(cph.fecha_limite, 'yyyy-MM')
        ORDER BY c.razsoc, FORMAT(cph.fecha_limite, 'yyyy-MM')
        """

        result_clientes = self.db.execute(text(sql_clientes), params_clientes).fetchall()
        clientes_data = []
        cliente_actual = None
        resolucion_cliente = []
        meses = {
            "01": "Ene", "02": "Feb", "03": "Mar", "04": "Abr",
            "05": "May", "06": "Jun", "07": "Jul", "08": "Ago",
            "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dic"
        }

        tiempo_total_cliente = 0.0
        count_periodos_cliente = 0

        for row in result_clientes:
            if cliente_actual != row.cliente_id:
                if cliente_actual is not None:
                    tiempo_medio_cliente = round(tiempo_total_cliente / count_periodos_cliente, 2) if count_periodos_cliente > 0 else 0.0
                    clientes_data.append({
                        "clienteId": str(cliente_actual),
                        "clienteNombre": nombre_cliente_actual,
                        "tiempoMedioDias": tiempo_medio_cliente,
                        "resolucionData": resolucion_cliente
                    })
                cliente_actual = row.cliente_id
                nombre_cliente_actual = str(row.cliente_nombre or "").strip()
                resolucion_cliente = []
                tiempo_total_cliente = 0.0
                count_periodos_cliente = 0

            if row.tiempo_medio and row.periodo:
                mes_num = row.periodo.split('-')[1] if '-' in row.periodo else "01"
                mes_nombre = meses.get(mes_num, row.periodo)
                tiempo_medio_valor = float(row.tiempo_medio)
                resolucion_cliente.append({
                    "periodo": mes_nombre,
                    "tiempoMedio": round(tiempo_medio_valor, 2)
                })
                tiempo_total_cliente += tiempo_medio_valor
                count_periodos_cliente += 1

        # Agregar el último cliente
        if cliente_actual is not None:
            tiempo_medio_cliente = round(tiempo_total_cliente / count_periodos_cliente, 2) if count_periodos_cliente > 0 else 0.0
            clientes_data.append({
                "clienteId": str(cliente_actual),
                "clienteNombre": nombre_cliente_actual,
                "tiempoMedioDias": tiempo_medio_cliente,
                "resolucionData": resolucion_cliente
            })

        return {
            "tiempoMedioDias": tiempo_medio_general,
            "tendencia": tendencia_tiempo,
            "resolucionData": resolucion_data,
            "clientesData": clientes_data
        }

    def get_hitos_vencidos(self) -> Dict[str, Any]:
        """Obtiene alertas de hitos vencidos sin último cumplimiento"""
        fecha_actual = date.today()
        fecha_30_dias = fecha_actual - timedelta(days=30)
        fecha_60_dias = fecha_actual - timedelta(days=60)

        # Subconsulta para obtener el último cumplimiento por hito
        subquery_ultimo_cumplimiento = (
            self.db.query(
                ClienteProcesoHitoCumplimientoModel.cliente_proceso_hito_id,
                func.max(ClienteProcesoHitoCumplimientoModel.id).label('ultimo_cumplimiento_id')
            )
            .group_by(ClienteProcesoHitoCumplimientoModel.cliente_proceso_hito_id)
            .subquery()
        )

        # Consulta principal: hitos vencidos sin último cumplimiento
        query = (
            self.db.query(
                ClienteProcesoHitoModel.id.label('hito_id'),
                ClienteModel.razsoc.label('cliente_nombre'),
                ProcesoModel.nombre.label('proceso_nombre'),
                ClienteProcesoHitoModel.fecha_limite.label('fecha_vencimiento')
            )
            .join(ClienteProcesoModel, ClienteProcesoHitoModel.cliente_proceso_id == ClienteProcesoModel.id)
            .join(ClienteModel, ClienteProcesoModel.cliente_id == ClienteModel.idcliente)
            .join(ProcesoModel, ClienteProcesoModel.proceso_id == ProcesoModel.id)
            .outerjoin(
                subquery_ultimo_cumplimiento,
                ClienteProcesoHitoModel.id == subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id
            )
            .filter(
                ClienteProcesoHitoModel.habilitado == True,
                ClienteProcesoHitoModel.fecha_limite < fecha_actual,
                subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id.is_(None)  # Sin cumplimiento
            )
            .order_by(ClienteProcesoHitoModel.fecha_limite.desc())
        )

        result = query.all()

        # Calcular tendencia
        query_actual_venc = (
            self.db.query(func.count(ClienteProcesoHitoModel.id).label('vencidos_actual'))
            .outerjoin(
                subquery_ultimo_cumplimiento,
                ClienteProcesoHitoModel.id == subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id
            )
            .filter(
                ClienteProcesoHitoModel.habilitado == True,
                ClienteProcesoHitoModel.fecha_limite < fecha_actual,
                ClienteProcesoHitoModel.fecha_limite >= fecha_30_dias,
                subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id.is_(None)
            )
        )

        query_anterior_venc = (
            self.db.query(func.count(ClienteProcesoHitoModel.id).label('vencidos_anterior'))
            .outerjoin(
                subquery_ultimo_cumplimiento,
                ClienteProcesoHitoModel.id == subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id
            )
            .filter(
                ClienteProcesoHitoModel.habilitado == True,
                ClienteProcesoHitoModel.fecha_limite < fecha_30_dias,
                ClienteProcesoHitoModel.fecha_limite >= fecha_60_dias,
                subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id.is_(None)
            )
        )

        result_actual_venc = query_actual_venc.first()
        result_anterior_venc = query_anterior_venc.first()

        vencidos_actual = result_actual_venc.vencidos_actual or 0 if result_actual_venc else 0
        vencidos_anterior = result_anterior_venc.vencidos_anterior or 0 if result_anterior_venc else 0

        tendencia_vencidos = self._calcular_tendencia(float(vencidos_actual), float(vencidos_anterior))

        # Agrupar hitos vencidos por cliente
        query_clientes_vencidos = (
            self.db.query(
                ClienteModel.idcliente.label('cliente_id'),
                ClienteModel.razsoc.label('cliente_nombre'),
                func.count(ClienteProcesoHitoModel.id).label('total_vencidos')
            )
            .join(ClienteProcesoModel, ClienteProcesoHitoModel.cliente_proceso_id == ClienteProcesoModel.id)
            .join(ClienteModel, ClienteProcesoModel.cliente_id == ClienteModel.idcliente)
            .outerjoin(
                subquery_ultimo_cumplimiento,
                ClienteProcesoHitoModel.id == subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id
            )
            .filter(
                ClienteProcesoHitoModel.habilitado == True,
                ClienteProcesoHitoModel.fecha_limite < fecha_actual,
                subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id.is_(None)
            )
            .group_by(ClienteModel.idcliente, ClienteModel.razsoc)
            .order_by(func.count(ClienteProcesoHitoModel.id).desc())
        )

        result_clientes_vencidos = query_clientes_vencidos.all()
        clientes_data = []
        for row in result_clientes_vencidos:
            clientes_data.append({
                "clienteId": str(row.cliente_id or ""),
                "clienteNombre": str(row.cliente_nombre or "").strip(),
                "totalVencidos": int(row.total_vencidos or 0)
            })

        return {
            "totalVencidos": len(result),
            "tendencia": tendencia_vencidos,
            "clientesData": clientes_data
        }

    def get_clientes_inactivos(self) -> Dict[str, Any]:
        """Obtiene clientes sin hitos activos recientes"""
        fecha_actual = date.today()
        fecha_30_dias = fecha_actual - timedelta(days=30)

        # Subconsulta para obtener el último cumplimiento por hito
        subquery_ultimo_cumplimiento = (
            self.db.query(
                ClienteProcesoHitoCumplimientoModel.cliente_proceso_hito_id,
                func.max(ClienteProcesoHitoCumplimientoModel.fecha).label('ultima_fecha_cumplimiento')
            )
            .group_by(ClienteProcesoHitoCumplimientoModel.cliente_proceso_hito_id)
            .subquery()
        )

        # Consulta principal: clientes sin hitos activos recientes
        query = (
            self.db.query(
                ClienteModel.idcliente.label('cliente_id'),
                ClienteModel.razsoc.label('cliente_nombre'),
                func.max(subquery_ultimo_cumplimiento.c.ultima_fecha_cumplimiento).label('ultima_actividad')
            )
            .outerjoin(ClienteProcesoModel, ClienteModel.idcliente == ClienteProcesoModel.cliente_id)
            .outerjoin(ClienteProcesoHitoModel, ClienteProcesoModel.id == ClienteProcesoHitoModel.cliente_proceso_id)
            .outerjoin(
                subquery_ultimo_cumplimiento,
                ClienteProcesoHitoModel.id == subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id
            )
            .group_by(ClienteModel.idcliente, ClienteModel.razsoc)
            .having(
                or_(
                    func.max(subquery_ultimo_cumplimiento.c.ultima_fecha_cumplimiento).is_(None),
                    func.max(subquery_ultimo_cumplimiento.c.ultima_fecha_cumplimiento) < fecha_30_dias
                )
            )
            .order_by(
                case(
                    (func.max(subquery_ultimo_cumplimiento.c.ultima_fecha_cumplimiento).is_(None), 1),
                    else_=0
                ),
                func.max(subquery_ultimo_cumplimiento.c.ultima_fecha_cumplimiento).desc()
            )
        )

        result = query.all()

        # Calcular tendencia
        fecha_60_dias = fecha_actual - timedelta(days=60)
        query_actual_inact = (
            self.db.query(func.count(func.distinct(ClienteModel.idcliente)).label('inactivos_actual'))
            .outerjoin(ClienteProcesoModel, ClienteModel.idcliente == ClienteProcesoModel.cliente_id)
            .outerjoin(ClienteProcesoHitoModel, ClienteProcesoModel.id == ClienteProcesoHitoModel.cliente_proceso_id)
            .outerjoin(
                subquery_ultimo_cumplimiento,
                ClienteProcesoHitoModel.id == subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id
            )
            .group_by(ClienteModel.idcliente)
            .having(
                or_(
                    func.max(subquery_ultimo_cumplimiento.c.ultima_fecha_cumplimiento).is_(None),
                    func.max(subquery_ultimo_cumplimiento.c.ultima_fecha_cumplimiento) < fecha_30_dias
                )
            )
        )

        query_anterior_inact = (
            self.db.query(func.count(func.distinct(ClienteModel.idcliente)).label('inactivos_anterior'))
            .outerjoin(ClienteProcesoModel, ClienteModel.idcliente == ClienteProcesoModel.cliente_id)
            .outerjoin(ClienteProcesoHitoModel, ClienteProcesoModel.id == ClienteProcesoHitoModel.cliente_proceso_id)
            .outerjoin(
                subquery_ultimo_cumplimiento,
                ClienteProcesoHitoModel.id == subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id
            )
            .group_by(ClienteModel.idcliente)
            .having(
                or_(
                    func.max(subquery_ultimo_cumplimiento.c.ultima_fecha_cumplimiento).is_(None),
                    func.max(subquery_ultimo_cumplimiento.c.ultima_fecha_cumplimiento) < fecha_60_dias
                )
            )
        )

        result_actual_inact = query_actual_inact.first()
        result_anterior_inact = query_anterior_inact.first()

        inactivos_actual = result_actual_inact.inactivos_actual or 0 if result_actual_inact else 0
        inactivos_anterior = result_anterior_inact.inactivos_anterior or 0 if result_anterior_inact else 0

        tendencia_inactivos = self._calcular_tendencia(float(inactivos_actual), float(inactivos_anterior))

        return {
            "totalInactivos": len(result),
            "tendencia": tendencia_inactivos
        }

    def get_volumen_mensual(self, cliente_id: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene volumen mensual de hitos basado en últimos cumplimientos"""
        fecha_actual = date.today()
        fecha_30_dias = fecha_actual - timedelta(days=30)
        fecha_60_dias = fecha_actual - timedelta(days=60)
        fecha_6_meses = fecha_actual - timedelta(days=180)

        # Consulta principal por mes usando SQL crudo para FORMAT
        sql = """
        WITH ultimo_cumplimiento AS (
            SELECT
                cliente_proceso_hito_id,
                MAX(id) AS ultimo_id
            FROM cliente_proceso_hito_cumplimiento
            GROUP BY cliente_proceso_hito_id
        )
        SELECT
            FORMAT(cph.fecha_limite, 'yyyy-MM') AS mes,
            COUNT(cph.id) AS hitos_creados,
            COUNT(uc.cliente_proceso_hito_id) AS hitos_completados
        FROM cliente_proceso_hito cph
        JOIN cliente_proceso cp ON cp.id = cph.cliente_proceso_id
        LEFT JOIN ultimo_cumplimiento uc ON uc.cliente_proceso_hito_id = cph.id
        WHERE cph.habilitado = 1
          AND cph.fecha_limite >= :fecha_6_meses
        """

        params = {"fecha_6_meses": fecha_6_meses}
        if cliente_id:
            sql += " AND cp.cliente_id = :cliente_id"
            params["cliente_id"] = cliente_id

        sql += """
        GROUP BY FORMAT(cph.fecha_limite, 'yyyy-MM')
        ORDER BY FORMAT(cph.fecha_limite, 'yyyy-MM')
        """
        result = self.db.execute(text(sql), params).fetchall()
        total_mes_actual = 0
        volumen_data = []

        if result:
            total_mes_actual = result[-1].hitos_completados or 0 if result else 0

            meses = {
                "01": "Ene", "02": "Feb", "03": "Mar", "04": "Abr",
                "05": "May", "06": "Jun", "07": "Jul", "08": "Ago",
                "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dic"
            }

            for row in result:
                if row.mes:
                    mes_num = row.mes.split('-')[1] if '-' in row.mes else "01"
                    mes_nombre = meses.get(mes_num, row.mes)
                    volumen_data.append({
                        "mes": mes_nombre,
                        "hitosCreados": int(row.hitos_creados or 0),
                        "hitosCompletados": int(row.hitos_completados or 0)
                    })

        # Calcular tendencia
        sql_actual_vol = """
        WITH ultimo_cumplimiento AS (
            SELECT
                cliente_proceso_hito_id,
                MAX(id) AS ultimo_id
            FROM cliente_proceso_hito_cumplimiento
            GROUP BY cliente_proceso_hito_id
        )
        SELECT COUNT(uc.cliente_proceso_hito_id) AS volumen_actual
        FROM cliente_proceso_hito cph
        JOIN cliente_proceso cp ON cp.id = cph.cliente_proceso_id
        LEFT JOIN ultimo_cumplimiento uc ON uc.cliente_proceso_hito_id = cph.id
        WHERE cph.habilitado = 1
          AND cph.fecha_limite >= :fecha_30_dias
        """

        params_actual_vol = {"fecha_30_dias": fecha_30_dias}
        if cliente_id:
            sql_actual_vol += " AND cp.cliente_id = :cliente_id"
            params_actual_vol["cliente_id"] = cliente_id

        sql_anterior_vol = """
        WITH ultimo_cumplimiento AS (
            SELECT
                cliente_proceso_hito_id,
                MAX(id) AS ultimo_id
            FROM cliente_proceso_hito_cumplimiento
            GROUP BY cliente_proceso_hito_id
        )
        SELECT COUNT(uc.cliente_proceso_hito_id) AS volumen_anterior
        FROM cliente_proceso_hito cph
        JOIN cliente_proceso cp ON cp.id = cph.cliente_proceso_id
        LEFT JOIN ultimo_cumplimiento uc ON uc.cliente_proceso_hito_id = cph.id
        WHERE cph.habilitado = 1
          AND cph.fecha_limite >= :fecha_60_dias
          AND cph.fecha_limite < :fecha_30_dias
        """

        params_anterior_vol = {"fecha_30_dias": fecha_30_dias, "fecha_60_dias": fecha_60_dias}
        if cliente_id:
            sql_anterior_vol += " AND cp.cliente_id = :cliente_id"
            params_anterior_vol["cliente_id"] = cliente_id

        result_actual_vol = self.db.execute(text(sql_actual_vol), params_actual_vol).fetchone()
        result_anterior_vol = self.db.execute(text(sql_anterior_vol), params_anterior_vol).fetchone()

        volumen_actual = result_actual_vol.volumen_actual or 0 if result_actual_vol else 0
        volumen_anterior = result_anterior_vol.volumen_anterior or 0 if result_anterior_vol else 0

        tendencia_volumen = self._calcular_tendencia(float(volumen_actual), float(volumen_anterior))

        # Consulta por cliente para volumen mensual
        sql_clientes_volumen = """
        WITH ultimo_cumplimiento AS (
            SELECT
                cliente_proceso_hito_id,
                MAX(id) AS ultimo_id
            FROM cliente_proceso_hito_cumplimiento
            GROUP BY cliente_proceso_hito_id
        )
        SELECT
            c.idcliente AS cliente_id,
            c.razsoc AS cliente_nombre,
            FORMAT(cph.fecha_limite, 'yyyy-MM') AS mes,
            COUNT(cph.id) AS hitos_creados,
            COUNT(uc.cliente_proceso_hito_id) AS hitos_completados
        FROM cliente_proceso_hito cph
        JOIN cliente_proceso cp ON cp.id = cph.cliente_proceso_id
        JOIN clientes c ON c.idcliente = cp.cliente_id
        LEFT JOIN ultimo_cumplimiento uc ON uc.cliente_proceso_hito_id = cph.id
        WHERE cph.habilitado = 1
          AND cph.fecha_limite >= :fecha_6_meses
        """

        params_clientes_volumen = {"fecha_6_meses": fecha_6_meses}
        if cliente_id:
            sql_clientes_volumen += " AND cp.cliente_id = :cliente_id"
            params_clientes_volumen["cliente_id"] = cliente_id

        sql_clientes_volumen += """
        GROUP BY c.idcliente, c.razsoc, FORMAT(cph.fecha_limite, 'yyyy-MM')
        ORDER BY c.razsoc, FORMAT(cph.fecha_limite, 'yyyy-MM')
        """

        result_clientes_volumen = self.db.execute(text(sql_clientes_volumen), params_clientes_volumen).fetchall()
        clientes_data = []
        cliente_actual = None
        volumen_cliente = []
        meses_volumen = {
            "01": "Ene", "02": "Feb", "03": "Mar", "04": "Abr",
            "05": "May", "06": "Jun", "07": "Jul", "08": "Ago",
            "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dic"
        }
        total_mes_cliente = 0

        for row in result_clientes_volumen:
            if cliente_actual != row.cliente_id:
                if cliente_actual is not None:
                    clientes_data.append({
                        "clienteId": str(cliente_actual),
                        "clienteNombre": nombre_cliente_actual,
                        "totalMesActual": total_mes_cliente,
                        "volumenData": volumen_cliente
                    })
                cliente_actual = row.cliente_id
                nombre_cliente_actual = str(row.cliente_nombre or "").strip()
                volumen_cliente = []
                total_mes_cliente = 0

            if row.mes:
                mes_num = row.mes.split('-')[1] if '-' in row.mes else "01"
                mes_nombre = meses_volumen.get(mes_num, row.mes)
                hitos_completados = int(row.hitos_completados or 0)
                volumen_cliente.append({
                    "mes": mes_nombre,
                    "hitosCreados": int(row.hitos_creados or 0),
                    "hitosCompletados": hitos_completados
                })
                # El último mes es el más reciente
                total_mes_cliente = hitos_completados

        # Agregar el último cliente
        if cliente_actual is not None:
            clientes_data.append({
                "clienteId": str(cliente_actual),
                "clienteNombre": nombre_cliente_actual,
                "totalMesActual": total_mes_cliente,
                "volumenData": volumen_cliente
            })

        return {
            "totalMesActual": total_mes_actual,
            "tendencia": tendencia_volumen,
            "volumenData": volumen_data,
            "clientesData": clientes_data
        }

    def get_resumen_metricas(self) -> Dict[str, Any]:
        """Obtiene resumen de todas las métricas"""
        # Subconsulta para obtener el último cumplimiento por hito
        subquery_ultimo_cumplimiento = (
            self.db.query(
                ClienteProcesoHitoCumplimientoModel.cliente_proceso_hito_id,
                func.max(ClienteProcesoHitoCumplimientoModel.id).label('ultimo_cumplimiento_id')
            )
            .group_by(ClienteProcesoHitoCumplimientoModel.cliente_proceso_hito_id)
            .subquery()
        )

        # Obtener cantidad total de hitos completados (con último cumplimiento)
        query_completados = (
            self.db.query(func.count(subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id).label('hitos_completados'))
            .outerjoin(
                ClienteProcesoHitoModel,
                ClienteProcesoHitoModel.id == subquery_ultimo_cumplimiento.c.cliente_proceso_hito_id
            )
            .filter(ClienteProcesoHitoModel.habilitado == True)
        )

        result_completados = query_completados.first()
        total_completados = result_completados.hitos_completados or 0 if result_completados else 0

        # Calcular tendencia para hitos completados
        fecha_actual = date.today()
        fecha_30_dias = fecha_actual - timedelta(days=30)
        fecha_60_dias = fecha_actual - timedelta(days=60)

        # Obtener cumplimientos recientes para calcular tendencia
        query_actual_comp = (
            self.db.query(func.count(ClienteProcesoHitoCumplimientoModel.id).label('completados_actual'))
            .join(
                subquery_ultimo_cumplimiento,
                ClienteProcesoHitoCumplimientoModel.id == subquery_ultimo_cumplimiento.c.ultimo_cumplimiento_id
            )
            .filter(ClienteProcesoHitoCumplimientoModel.fecha >= fecha_30_dias)
        )

        query_anterior_comp = (
            self.db.query(func.count(ClienteProcesoHitoCumplimientoModel.id).label('completados_anterior'))
            .join(
                subquery_ultimo_cumplimiento,
                ClienteProcesoHitoCumplimientoModel.id == subquery_ultimo_cumplimiento.c.ultimo_cumplimiento_id
            )
            .filter(
                ClienteProcesoHitoCumplimientoModel.fecha >= fecha_60_dias,
                ClienteProcesoHitoCumplimientoModel.fecha < fecha_30_dias
            )
        )

        result_actual_comp = query_actual_comp.first()
        result_anterior_comp = query_anterior_comp.first()

        completados_actual = result_actual_comp.completados_actual or 0 if result_actual_comp else 0
        completados_anterior = result_anterior_comp.completados_anterior or 0 if result_anterior_comp else 0

        tendencia_completados = self._calcular_tendencia(float(completados_actual), float(completados_anterior))

        # Obtener otras métricas
        hitos_proceso = self.get_hitos_por_proceso()
        vencidos = self.get_hitos_vencidos()
        inactivos = self.get_clientes_inactivos()

        return {
            "hitosCompletados": {
                "valor": total_completados,
                "tendencia": tendencia_completados
            },
            "hitosPendientes": {
                "valor": hitos_proceso['totalPendientes'],
                "tendencia": hitos_proceso['tendencia']
            },
            "hitosVencidos": {
                "valor": vencidos['totalVencidos'],
                "tendencia": vencidos['tendencia']
            },
            "clientesInactivos": {
                "valor": inactivos['totalInactivos'],
                "tendencia": inactivos['tendencia']
            }
        }
