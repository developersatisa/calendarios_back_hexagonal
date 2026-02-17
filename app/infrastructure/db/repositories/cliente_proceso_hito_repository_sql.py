# app/infrastructure/db/repositories/cliente_proceso_hito_repository_sql.py

from datetime import date, datetime, time, timedelta
import calendar

from sqlalchemy import extract, text, func, case, or_, Table, Column, String, MetaData

from app.domain.entities.cliente_proceso_hito import ClienteProcesoHito
from app.domain.repositories.cliente_proceso_hito_repository import ClienteProcesoHitoRepository

from app.infrastructure.db.models.cliente_proceso_hito_model import ClienteProcesoHitoModel
from app.infrastructure.db.models.cliente_proceso_model import ClienteProcesoModel
from app.infrastructure.db.models.cliente_model import ClienteModel
from app.infrastructure.db.models.hito_model import HitoModel
from app.infrastructure.db.models.proceso_model import ProcesoModel
from app.infrastructure.db.models.cliente_proceso_hito_cumplimiento_model import ClienteProcesoHitoCumplimientoModel
from app.infrastructure.db.models.documentos_cumplimiento_model import DocumentoCumplimientoModel
from app.infrastructure.db.models.subdepar_model import SubdeparModel
from app.infrastructure.db.models import ProcesoHitoMaestroModel

class ClienteProcesoHitoRepositorySQL(ClienteProcesoHitoRepository):
    def __init__(self, session):
        self.session = session

    def guardar(self, relacion: ClienteProcesoHito):
        modelo = ClienteProcesoHitoModel(**vars(relacion))
        self.session.add(modelo)
        self.session.commit()
        self.session.refresh(modelo)
        return modelo

    def listar(self):
        return self.session.query(ClienteProcesoHitoModel).all()

    def obtener_por_fecha(self, anio: int, mes: int, cliente_id: str = None, proceso_ids: list = None, hito_ids: list = None) -> list:
        query = self.session.query(
            ClienteProcesoHitoModel.id,
            ClienteProcesoHitoModel.fecha_limite,
            ClienteProcesoHitoModel.estado,
            ClienteProcesoHitoModel.hora_limite,
            ClienteModel.razsoc,
            HitoModel.nombre,
            ProcesoModel.nombre,
            ProcesoModel.id,
            HitoModel.id
        ).join(
            ClienteProcesoModel, ClienteProcesoHitoModel.cliente_proceso_id == ClienteProcesoModel.id
        ).join(
            ClienteModel, ClienteProcesoModel.cliente_id == ClienteModel.idcliente
        ).join(
            HitoModel, ClienteProcesoHitoModel.hito_id == HitoModel.id
        ).join(
            ProcesoModel, ClienteProcesoModel.proceso_id == ProcesoModel.id
        ).filter(
            extract('year', ClienteProcesoHitoModel.fecha_limite) == anio,
            extract('month', ClienteProcesoHitoModel.fecha_limite) == mes,
            ClienteProcesoHitoModel.habilitado == True
        )

        if cliente_id:
            query = query.filter(ClienteModel.idcliente == cliente_id)

        if proceso_ids:
            query = query.filter(ProcesoModel.id.in_(proceso_ids))

        if hito_ids:
            query = query.filter(HitoModel.id.in_(hito_ids))

        resultados = query.all()

        return [
            {
                "id": r[0],
                "fecha_limite": r[1],
                "estado": r[2],
                "hora_limite": r[3],
                "cliente": r[4],
                "hito": r[5],
                "proceso": r[6],
                "proceso_id": r[7],
                "hito_id": r[8]
            } for r in resultados
        ]

    def obtener_filtros(self, anio: int, mes: int, cliente_id: str = None):
        # Base filters
        filters = [
            extract('year', ClienteProcesoHitoModel.fecha_limite) == anio,
            extract('month', ClienteProcesoHitoModel.fecha_limite) == mes,
            ClienteProcesoHitoModel.habilitado == True,
            ClienteProcesoModel.habilitado == True
        ]

        # Query Procesos
        q_procesos = self.session.query(ProcesoModel.id, ProcesoModel.nombre).join(
            ClienteProcesoModel, ProcesoModel.id == ClienteProcesoModel.proceso_id
        ).join(
            ClienteProcesoHitoModel, ClienteProcesoModel.id == ClienteProcesoHitoModel.cliente_proceso_id
        ).filter(*filters)

        # Query Hitos
        q_hitos = self.session.query(HitoModel.id, HitoModel.nombre).join(
            ClienteProcesoHitoModel, HitoModel.id == ClienteProcesoHitoModel.hito_id
        ).join(
            ClienteProcesoModel, ClienteProcesoHitoModel.cliente_proceso_id == ClienteProcesoModel.id
        ).filter(*filters)

        if cliente_id:
            # Need to join ClienteModel only if filtering by client
            q_procesos = q_procesos.join(ClienteModel, ClienteProcesoModel.cliente_id == ClienteModel.idcliente).filter(ClienteModel.idcliente == cliente_id)
            q_hitos = q_hitos.join(ClienteModel, ClienteProcesoModel.cliente_id == ClienteModel.idcliente).filter(ClienteModel.idcliente == cliente_id)

        procesos = q_procesos.distinct().all()
        hitos = q_hitos.distinct().all()

        return {
            "procesos": [{"id": p[0], "nombre": p[1]} for p in procesos],
            "hitos": [{"id": h[0], "nombre": h[1]} for h in hitos]
        }

    def obtener_por_id(self, id: int):
        return self.session.query(ClienteProcesoHitoModel).filter_by(id=id).first()

    def eliminar(self, id: int):
        relacion = self.obtener_por_id(id)
        if not relacion:
            return False
        self.session.delete(relacion)
        self.session.commit()
        return True

    def obtener_por_cliente_proceso_id(self, cliente_proceso_id: int):
        return self.session.query(ClienteProcesoHitoModel).filter_by(cliente_proceso_id=cliente_proceso_id).all()

    def listar_habilitados(self):
        """Lista solo los hitos habilitados (habilitado=True)"""
        return self.session.query(ClienteProcesoHitoModel).filter_by(habilitado=True).all()

    def obtener_habilitados_por_cliente_proceso_id(self, cliente_proceso_id: int):
        """Obtiene solo los hitos habilitados de un proceso de cliente específico"""
        return self.session.query(ClienteProcesoHitoModel).filter_by(
            cliente_proceso_id=cliente_proceso_id,
            habilitado=True
        ).all()

    def deshabilitar_desde_fecha_por_hito(self, hito_id: int, fecha_desde):
        """Deshabilita todos los ClienteProcesoHito para un hito_id con fecha_limite >= fecha_desde"""

        # Normalizar fecha_desde a date
        if isinstance(fecha_desde, str):
            try:
                fecha_desde = datetime.fromisoformat(fecha_desde).date()
            except ValueError:
                fecha_desde = date.fromisoformat(fecha_desde)

        # Obtener todos los registros a deshabilitar
        query = self.session.query(ClienteProcesoHitoModel).filter(
            ClienteProcesoHitoModel.hito_id == hito_id,
            ClienteProcesoHitoModel.fecha_limite >= fecha_desde
        )

        # Obtener los cliente_proceso_id únicos que serán afectados
        cliente_proceso_ids_afectados = set()
        afectados = 0
        cliente_procesos_deshabilitados = []

        # Primero, obtener los registros que se van a deshabilitar
        registros_a_deshabilitar = query.all()

        for registro in registros_a_deshabilitar:
            registro.habilitado = False
            cliente_proceso_ids_afectados.add(registro.cliente_proceso_id)
            afectados += 1

        # Hacer flush para que los cambios se reflejen en la sesión antes de contar
        self.session.flush()

        # Ahora verificar cada cliente_proceso afectado
        for cliente_proceso_id in cliente_proceso_ids_afectados:
            # Contar TODOS los hitos habilitados para este cliente_proceso
            hitos_habilitados = self.session.query(ClienteProcesoHitoModel).filter(
                ClienteProcesoHitoModel.cliente_proceso_id == cliente_proceso_id,
                ClienteProcesoHitoModel.habilitado == True
            ).count()

            # Si no quedan hitos habilitados, deshabilitar el cliente_proceso
            if hitos_habilitados == 0:
                cliente_proceso = self.session.query(ClienteProcesoModel).filter_by(
                    id=cliente_proceso_id
                ).first()
                if cliente_proceso:
                    cliente_proceso.habilitado = False
                    cliente_procesos_deshabilitados.append({
                        'id': cliente_proceso.id,
                        'cliente_id': cliente_proceso.cliente_id,
                        'proceso_id': cliente_proceso.proceso_id
                    })

        self.session.commit()
        return {
            'hitos_afectados': afectados,
            'cliente_procesos_deshabilitados': cliente_procesos_deshabilitados
        }

    def sincronizar_estado_cliente_proceso(self, cliente_proceso_id: int):
        """Verifica y actualiza el estado de habilitado de un cliente_proceso basado en sus hitos"""

        # Contar hitos habilitados para este cliente_proceso
        hitos_habilitados = self.session.query(ClienteProcesoHitoModel).filter(
            ClienteProcesoHitoModel.cliente_proceso_id == cliente_proceso_id,
            ClienteProcesoHitoModel.habilitado == True
        ).count()

        # Obtener el cliente_proceso
        cliente_proceso = self.session.query(ClienteProcesoModel).filter_by(
            id=cliente_proceso_id
        ).first()

        if not cliente_proceso:
            return False

        # Determinar el estado correcto: habilitado si tiene al menos un hito habilitado
        nuevo_estado = hitos_habilitados > 0
        estado_anterior = cliente_proceso.habilitado

        if cliente_proceso.habilitado != nuevo_estado:
            cliente_proceso.habilitado = nuevo_estado
            self.session.commit()
            return {
                'actualizado': True,
                'estado_anterior': estado_anterior,
                'estado_nuevo': nuevo_estado,
                'hitos_habilitados': hitos_habilitados
            }

        return {
            'actualizado': False,
            'estado_actual': cliente_proceso.habilitado,
            'hitos_habilitados': hitos_habilitados
        }

    def actualizar_fecha_masivo(self, hito_id: int, cliente_ids: list[int], nueva_fecha: date, nueva_hora: time | None, fecha_desde: date, fecha_hasta: date | None = None) -> int:
        """Actualiza la fecha_limite y opcionalmente la hora_limite de un hito para múltiples clientes, aplicando solo si la fecha actual >= fecha_desde"""

        # Normalizar fecha_desde a date si es datetime o string
        if isinstance(fecha_desde, datetime):
            fecha_desde = fecha_desde.date()
        elif isinstance(fecha_desde, str):
            try:
                fecha_desde = date.fromisoformat(fecha_desde)
            except ValueError:
                pass

        print(f"DEBUG: fecha_desde={fecha_desde}, fecha_hasta={fecha_hasta}")

        # Si fecha_hasta no viene informada, usar el úlitmo día del año de fecha_desde
        if not fecha_hasta:
            fecha_hasta = date(fecha_desde.year, 12, 31)
            print(f"DEBUG: fecha_hasta calculada={fecha_hasta}")


        # Obtener los registros que se van a actualizar
        query = self.session.query(ClienteProcesoHitoModel).filter(
            ClienteProcesoHitoModel.hito_id == hito_id,
            ClienteProcesoHitoModel.fecha_limite >= fecha_desde,
            ClienteProcesoHitoModel.cliente_proceso_id.in_(
                self.session.query(ClienteProcesoModel.id).filter(
                    ClienteProcesoModel.cliente_id.in_(cliente_ids)
                )
            )
        )

        if fecha_hasta:
             query = query.filter(ClienteProcesoHitoModel.fecha_limite <= fecha_hasta)

        registros_a_actualizar = query.all()

        # Actualizar cada registro individualmente, cambiando solo el día
        updated_count = 0
        nuevo_dia = nueva_fecha.day

        for registro in registros_a_actualizar:
            # Actualizar hora si se proporciona
            if nueva_hora is not None:
                registro.hora_limite = nueva_hora

            if registro.fecha_limite:
                try:
                    # Mantener el año y mes original, cambiar solo el día
                    fecha_actualizada = registro.fecha_limite.replace(day=nuevo_dia)

                    # Ajustar fin de semana: si cae en sábado o domingo, mover al viernes
                    weekday = fecha_actualizada.weekday()  # 0=Lunes ... 5=Sábado, 6=Domingo
                    if weekday == 5:  # Sábado -> viernes (día - 1)
                        fecha_actualizada = fecha_actualizada - timedelta(days=1)
                    elif weekday == 6:  # Domingo -> viernes (día - 2)
                        fecha_actualizada = fecha_actualizada - timedelta(days=2)

                    registro.fecha_limite = fecha_actualizada
                    updated_count += 1
                except ValueError:
                    # Si el día no es válido para ese mes (ej: 31 en febrero)
                    # Usar el último día del mes
                    ultimo_dia = calendar.monthrange(registro.fecha_limite.year, registro.fecha_limite.month)[1]
                    dia_a_usar = min(nuevo_dia, ultimo_dia)
                    fecha_actualizada = registro.fecha_limite.replace(day=dia_a_usar)

                    # Ajustar fin de semana también para este caso
                    weekday = fecha_actualizada.weekday()
                    if weekday == 5:  # Sábado -> viernes
                        fecha_actualizada = fecha_actualizada - timedelta(days=1)
                    elif weekday == 6:  # Domingo -> viernes
                        fecha_actualizada = fecha_actualizada - timedelta(days=2)

                    registro.fecha_limite = fecha_actualizada
                    updated_count += 1

        self.session.commit()
        return updated_count

    def actualizar(self, id: int, data: dict):
        hito = self.obtener_por_id(id)
        if not hito:
            return None

        # Guardar el cliente_proceso_id antes de actualizar
        cliente_proceso_id = hito.cliente_proceso_id

        for key, value in data.items():
            # Manejar conversión de tipos específicos
            if key == 'fecha_estado' and isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    value = datetime.fromisoformat(value)
            elif key == 'fecha_limite' and isinstance(value, str):
                try:
                    value = date.fromisoformat(value)
                except ValueError:
                    value = value
            elif key == 'habilitado' and isinstance(value, str):
                value = value.lower() in ('true', '1', 'yes', 'on')

            setattr(hito, key, value)

        # Hacer flush para que los cambios se reflejen
        self.session.flush()

        # Si se cambió el estado de habilitado del hito, verificar si debe actualizar el cliente_proceso
        if 'habilitado' in data:
            # Contar hitos habilitados para este cliente_proceso
            hitos_habilitados = self.session.query(ClienteProcesoHitoModel).filter(
                ClienteProcesoHitoModel.cliente_proceso_id == cliente_proceso_id,
                ClienteProcesoHitoModel.habilitado == True
            ).count()

            # Obtener el cliente_proceso
            cliente_proceso = self.session.query(ClienteProcesoModel).filter_by(
                id=cliente_proceso_id
            ).first()

            if cliente_proceso:
                # Si hay hitos habilitados, el cliente_proceso debe estar habilitado
                # Si no hay hitos habilitados, el cliente_proceso debe estar deshabilitado
                nuevo_estado = hitos_habilitados > 0
                if cliente_proceso.habilitado != nuevo_estado:
                    cliente_proceso.habilitado = nuevo_estado

        self.session.commit()
        self.session.refresh(hito)
        return hito

    def verificar_registros_por_hito(self, hito_id: int):
        """Verifica si existe algún registro para un hito específico"""

        # Buscar cualquier registro en cliente_proceso_hito que referencie al hito a través de proceso_hito_maestro
        resultado = self.session.query(ClienteProcesoHitoModel).join(
            ProcesoHitoMaestroModel,
            ClienteProcesoHitoModel.hito_id == ProcesoHitoMaestroModel.hito_id
        ).filter(
            ProcesoHitoMaestroModel.hito_id == hito_id
        ).first()

        return resultado is not None

    def eliminar_por_hito_id(self, hito_id: int):
        """Elimina todos los registros de cliente_proceso_hito asociados a un hito específico"""

        # Obtener los IDs de proceso_hito_maestro que referencian al hito
        proceso_hito_ids = self.session.query(ProcesoHitoMaestroModel.id).filter(
            ProcesoHitoMaestroModel.hito_id == hito_id
        ).all()

        if proceso_hito_ids:
            # Extraer solo los IDs
            ids_list = [phm_id[0] for phm_id in proceso_hito_ids]

            # Eliminar registros de cliente_proceso_hito que referencien estos IDs
            eliminados = self.session.query(ClienteProcesoHitoModel).filter(
                ClienteProcesoHitoModel.hito_id.in_(ids_list)
            ).delete(synchronize_session=False)

            self.session.commit()
            return eliminados

        return 0


    def ejecutar_reporte_status_todos_clientes(self, filtros: dict, paginacion: dict):
        # Definir tabla externa Persona
        metadata = MetaData()
        # Se asume que el driver manejara los espacios en el nombre de la BD si se pasa como schema
        persona_table = Table(
            'Persona',
            metadata,
            Column('Numeross', String, primary_key=True),
            Column('Nombre', String),
            Column('Apellido1', String),
            Column('Apellido2', String),
            schema='BI DW RRHH DEV.dbo'
        )
        per = persona_table.alias('per')

        # Subconsulta para obtener el ID del último cumplimiento por hito
        subquery_ultimo_cumplimiento = (
            self.session.query(
                ClienteProcesoHitoCumplimientoModel.cliente_proceso_hito_id,
                func.max(ClienteProcesoHitoCumplimientoModel.id).label('ultimo_cumplimiento_id')
            )
            .group_by(ClienteProcesoHitoCumplimientoModel.cliente_proceso_hito_id)
            .subquery()
        )

        query = (
            self.session.query(
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
                ClienteProcesoModel.fecha_inicio.label('proceso_fecha_inicio'),
                ClienteProcesoModel.fecha_fin.label('proceso_fecha_fin'),
                ClienteProcesoModel.mes.label('proceso_mes'),
                ClienteProcesoModel.anio.label('proceso_anio'),
                ProcesoModel.nombre.label('proceso_nombre'),
                # Información del hito maestro
                HitoModel.nombre.label('hito_nombre'),
                HitoModel.obligatorio.label('hito_obligatorio'),
                # Último cumplimiento (si existe)
                ClienteProcesoHitoCumplimientoModel.id.label('cumplimiento_id'),
                ClienteProcesoHitoCumplimientoModel.fecha.label('cumplimiento_fecha'),
                ClienteProcesoHitoCumplimientoModel.hora.label('cumplimiento_hora'),
                ClienteProcesoHitoCumplimientoModel.observacion.label('cumplimiento_observacion'),
                 # Usuario: si existe en Persona, concatenar nombre completo, sino usar campo usuario
                case(
                    (per.c.Nombre != None,
                     func.concat(
                         func.isnull(per.c.Nombre, ''), ' ',
                         func.isnull(per.c.Apellido1, ''), ' ',
                         func.isnull(per.c.Apellido2, '')
                     )),
                    else_=ClienteProcesoHitoCumplimientoModel.usuario
                ).label('cumplimiento_usuario'),
                ClienteProcesoHitoCumplimientoModel.codSubDepar.label('cumplimiento_codSubDepar'),
                SubdeparModel.nombre.label('cumplimiento_departamento'),
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
            .outerjoin(
                SubdeparModel,
                ClienteProcesoHitoCumplimientoModel.codSubDepar == SubdeparModel.codSubDepar
            )
            .outerjoin(
                per,
                per.c.Numeross == ClienteProcesoHitoCumplimientoModel.usuario
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
                ClienteProcesoModel.fecha_inicio,
                ClienteProcesoModel.fecha_fin,
                ClienteProcesoModel.mes,
                ClienteProcesoModel.anio,
                ProcesoModel.nombre,
                HitoModel.nombre,
                HitoModel.obligatorio,
                ClienteProcesoHitoCumplimientoModel.id,
                ClienteProcesoHitoCumplimientoModel.fecha,
                ClienteProcesoHitoCumplimientoModel.hora,
                ClienteProcesoHitoCumplimientoModel.observacion,
                ClienteProcesoHitoCumplimientoModel.usuario,
                ClienteProcesoHitoCumplimientoModel.codSubDepar,
                SubdeparModel.nombre,
                per.c.Nombre,
                per.c.Apellido1,
                per.c.Apellido2,
                ClienteProcesoHitoCumplimientoModel.fecha_creacion
            )
        )

        # Aplicar filtros
        if filtros.get('fecha_limite_desde'):
            query = query.filter(ClienteProcesoHitoModel.fecha_limite >= filtros['fecha_limite_desde'])

        if filtros.get('fecha_limite_hasta'):
            query = query.filter(ClienteProcesoHitoModel.fecha_limite <= filtros['fecha_limite_hasta'])

        if filtros.get('cliente_id'):
            query = query.filter(ClienteModel.idcliente == filtros['cliente_id'])

        if filtros.get('proceso_id'):
            query = query.filter(ClienteProcesoModel.proceso_id == filtros['proceso_id'])

        if filtros.get('hito_id'):
            query = query.filter(ClienteProcesoHitoModel.hito_id == filtros['hito_id'])

        if filtros.get('proceso_nombre'):
             query = query.filter(ProcesoModel.nombre.ilike(f"%{filtros['proceso_nombre']}%"))

        if filtros.get('tipos'):
            tipos_list = [t.strip() for t in filtros['tipos'].split(",")]
            query = query.filter(ClienteProcesoHitoModel.tipo.in_(tipos_list))

        if filtros.get('search_term'):
            search_pattern = f"%{filtros['search_term']}%"
            query = query.filter(
                (ProcesoModel.nombre.ilike(search_pattern)) |
                (HitoModel.nombre.ilike(search_pattern))
            )

        # Ordenar
        ordenar_por = filtros.get('ordenar_por', 'fecha_limite')
        orden = filtros.get('orden', 'asc')

        if ordenar_por == "fecha_limite":
            order_field = ClienteProcesoHitoModel.fecha_limite
        elif ordenar_por == "cliente_nombre":
            order_field = ClienteModel.razsoc
        elif ordenar_por == "proceso_nombre":
            order_field = ProcesoModel.nombre
        else:
            order_field = ClienteProcesoHitoModel.fecha_limite

        if orden and orden.lower() == "desc":
            query = query.order_by(order_field.desc())
        else:
            query = query.order_by(order_field.asc())

        # Obtener Total
        total_registros = query.count()

        # Paginación
        if paginacion:
            if paginacion.get('offset') is not None:
                query = query.offset(paginacion['offset'])
            if paginacion.get('limit') is not None:
                query = query.limit(paginacion['limit'])

        registros = query.all()

        return registros, total_registros
