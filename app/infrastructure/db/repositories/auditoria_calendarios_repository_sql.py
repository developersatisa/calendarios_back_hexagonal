from datetime import datetime
from sqlalchemy import text
from app.domain.entities.auditoria_calendarios import AuditoriaCalendarios
from app.domain.repositories.auditoria_calendarios_repository import AuditoriaCalendariosRepository
from app.infrastructure.db.models.auditoria_calendarios_model import AuditoriaCalendariosModel
from app.infrastructure.db.models.hito_model import HitoModel
from app.infrastructure.db.models.cliente_proceso_hito_model import ClienteProcesoHitoModel
from app.infrastructure.db.models.proceso_hito_maestro_model import ProcesoHitoMaestroModel

# Catálogo de motivos de auditoría
MOTIVOS_AUDITORIA = {
    1: "Por configuración",
    2: "A petición de Atisa",
    3: "A petición de cliente",
    4: "A petición de tercero",
}


class AuditoriaCalendariosRepositorySQL(AuditoriaCalendariosRepository):
    def __init__(self, session):
        self.session = session

    def guardar(self, auditoria: AuditoriaCalendarios):
        current_time = datetime.utcnow()
        data = {}
        for k, v in auditoria.__dict__.items():
            if k == 'id' and v is None:
                continue
            elif k in ['created_at', 'updated_at']:
                data[k] = current_time
            elif k == 'fecha_modificacion' and v is None:
                data[k] = current_time
            else:
                data[k] = v

        modelo = AuditoriaCalendariosModel(**data)
        self.session.add(modelo)
        self.session.commit()
        self.session.refresh(modelo)
        return modelo

    def _execute_query(self, where_clause="", params={}):
        sql = f"""
            SELECT
                ac.id,
                ac.cliente_id,
                ac.hito_id,
                ac.campo_modificado,
                ac.valor_anterior,
                ac.valor_nuevo,
                ac.observaciones,
                ac.motivo,
                ac.usuario,
                CASE
                    WHEN per.Nombre IS NOT NULL THEN LTRIM(RTRIM(ISNULL(per.Nombre, ''))) + ' ' + LTRIM(RTRIM(ISNULL(per.Apellido1, ''))) + ' ' + LTRIM(RTRIM(ISNULL(per.Apellido2, '')))
                    ELSE ac.usuario
                END as nombre_usuario,
                ac.codSubDepar,
                ac.fecha_modificacion,
                ac.created_at,
                ac.updated_at,
                sd.nombre AS nombre_subdepar,
                p.nombre AS proceso_nombre,
                h.nombre AS hito_nombre,
                h.tipo AS tipo,
                h.critico AS hito_critico,
                h.obligatorio AS hito_obligatorio,
                cph.fecha_limite AS cph_fecha_limite
            FROM auditoria_calendarios ac
            INNER JOIN [ATISA_Input].dbo.cliente_proceso_hito cph ON ac.hito_id = cph.id
            INNER JOIN [ATISA_Input].dbo.hito h ON cph.hito_id = h.id
            LEFT JOIN [ATISA_Input].dbo.cliente_proceso cp ON cph.cliente_proceso_id = cp.id
            LEFT JOIN [ATISA_Input].dbo.proceso p ON cp.proceso_id = p.id
            LEFT JOIN [ATISA_Input].dbo.SubDePar sd ON ac.codSubDepar = sd.codSubDePar
            LEFT JOIN [BI DW RRHH DEV].dbo.Persona per ON per.Numeross = ac.usuario
            WHERE 1=1 {where_clause}
            ORDER BY ac.fecha_modificacion DESC
        """
        result = self.session.execute(text(sql), params)
        rows = result.mappings().all()

        output = []
        for r in rows:
            # Calcular momento del cambio
            momento_cambio = None
            if r['fecha_modificacion'] and r['cph_fecha_limite']:
                fm_date = r['fecha_modificacion'].date() if hasattr(r['fecha_modificacion'], 'date') else r['fecha_modificacion']
                fl_date = r['cph_fecha_limite']
                if fm_date < fl_date:
                    momento_cambio = "Antes de fecha límite"
                elif fm_date == fl_date:
                    momento_cambio = "El mismo día de la fecha límite"
                else:
                    momento_cambio = "Después de la fecha límite"

            # Determinar fecha_limite_anterior y actual
            fecha_limite_anterior = None
            fecha_limite_actual = None
            if r['campo_modificado'] == 'fecha_limite':
                fecha_limite_anterior = r['valor_anterior']
                fecha_limite_actual = r['valor_nuevo']
            elif r['cph_fecha_limite']:
                fecha_limite_actual = str(r['cph_fecha_limite'])

            output.append({
                "id": r['id'],
                "cliente_id": r['cliente_id'],
                "hito_id": r['hito_id'],
                "campo_modificado": r['campo_modificado'],
                "valor_anterior": r['valor_anterior'],
                "valor_nuevo": r['valor_nuevo'],
                "observaciones": r['observaciones'],
                "motivo": r['motivo'],
                "motivo_descripcion": MOTIVOS_AUDITORIA.get(r['motivo']) if r['motivo'] is not None else None,
                "usuario": r['usuario'],
                "nombre_usuario": r['nombre_usuario'],
                "codSubDepar": r['codSubDepar'],
                "fecha_modificacion": r['fecha_modificacion'],
                "created_at": r['created_at'],
                "updated_at": r['updated_at'],
                # Campos enriquecidos
                "nombre_subdepar": r['nombre_subdepar'],
                "proceso_nombre": r['proceso_nombre'],
                "hito_nombre": r['hito_nombre'],
                "tipo": r['tipo'],
                "critico": bool(r['hito_critico']) if r['hito_critico'] is not None else False,
                "obligatorio": bool(r['hito_obligatorio']) if r['hito_obligatorio'] is not None else False,
                "fecha_limite_anterior": fecha_limite_anterior,
                "fecha_limite_actual": fecha_limite_actual,
                "momento_cambio": momento_cambio,
            })
        return output

    def listar(self):
        return self._execute_query()

    def obtener_por_id(self, id: int):
        res = self._execute_query("AND ac.id = :id", {"id": id})
        return res[0] if res else None

    def obtener_por_hito(self, id_hito: int):
        return self._execute_query("AND ac.hito_id = :hito_id", {"hito_id": id_hito})

    def obtener_por_cliente(self, cliente_id: str):
        return self._execute_query("AND ac.cliente_id = :cliente_id", {"cliente_id": cliente_id})

    # Implementación de métodos async del repositorio base
    async def create(self, auditoria: AuditoriaCalendarios) -> AuditoriaCalendarios:
        return self.guardar(auditoria)

    async def get_by_id(self, id: int):
        return self.obtener_por_id(id)

    async def get_by_hito(self, id_hito: int):
        return self.obtener_por_hito(id_hito)

    async def get_by_cliente(self, id_cliente: str):
        return self.obtener_por_cliente(id_cliente)
