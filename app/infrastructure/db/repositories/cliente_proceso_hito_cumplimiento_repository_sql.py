# app/infrastructure/db/repositories/cliente_proceso_hito_cumplimiento_repository_sql.py

from sqlalchemy import func
from app.domain.entities.cliente_proceso_hito_cumplimiento import ClienteProcesoHitoCumplimiento
from app.domain.repositories.cliente_proceso_hito_cumplimiento_repository import ClienteProcesoHitoCumplimientoRepository
from app.infrastructure.db.models.cliente_proceso_hito_cumplimiento_model import ClienteProcesoHitoCumplimientoModel
from app.infrastructure.db.models.documentos_cumplimiento_model import DocumentoCumplimientoModel

from app.infrastructure.db.models.subdepar_model import SubdeparModel

class ClienteProcesoHitoCumplimientoRepositorySQL(ClienteProcesoHitoCumplimientoRepository):
    def __init__(self, session):
        self.session = session

    def guardar(self, cliente_proceso_hito_cumplimiento: ClienteProcesoHitoCumplimiento):
        from datetime import datetime, timedelta

        # Obtener todos los atributos de la entidad
        datos = vars(cliente_proceso_hito_cumplimiento)

        # Filtrar el campo 'id' si es None para evitar problemas con SQLAlchemy
        if datos.get('id') is None:
            datos.pop('id', None)

        # Auto-rellenar fecha_creacion si no está definida
        if datos.get('fecha_creacion') is None:
            # Ajuste de hora para compensar UTC vs Local (España)
            datos['fecha_creacion'] = datetime.utcnow() + timedelta(hours=1)

        modelo = ClienteProcesoHitoCumplimientoModel(**datos)
        self.session.add(modelo)
        self.session.commit()
        self.session.refresh(modelo)
        return modelo

    def listar(self):
        # Query con LEFT JOIN para contar documentos asociados a cada cumplimiento y obtener nombre departamento
        # SQL Server requiere que todas las columnas estén en GROUP BY
        resultados = (
            self.session.query(
                ClienteProcesoHitoCumplimientoModel.id,
                ClienteProcesoHitoCumplimientoModel.cliente_proceso_hito_id,
                ClienteProcesoHitoCumplimientoModel.fecha,
                ClienteProcesoHitoCumplimientoModel.hora,
                ClienteProcesoHitoCumplimientoModel.observacion,
                ClienteProcesoHitoCumplimientoModel.usuario,
                ClienteProcesoHitoCumplimientoModel.fecha_creacion,
                ClienteProcesoHitoCumplimientoModel.ceco,
                SubdeparModel.nombre.label('departamento'),
                func.count(DocumentoCumplimientoModel.id).label('num_documentos')
            )
            .outerjoin(DocumentoCumplimientoModel, ClienteProcesoHitoCumplimientoModel.id == DocumentoCumplimientoModel.cumplimiento_id)
            .outerjoin(SubdeparModel, ClienteProcesoHitoCumplimientoModel.codSubDepar == SubdeparModel.codSubDepar)
            .group_by(
                ClienteProcesoHitoCumplimientoModel.id,
                ClienteProcesoHitoCumplimientoModel.cliente_proceso_hito_id,
                ClienteProcesoHitoCumplimientoModel.fecha,
                ClienteProcesoHitoCumplimientoModel.hora,
                ClienteProcesoHitoCumplimientoModel.observacion,
                ClienteProcesoHitoCumplimientoModel.usuario,
                ClienteProcesoHitoCumplimientoModel.fecha_creacion,
                ClienteProcesoHitoCumplimientoModel.codSubDepar,
                SubdeparModel.nombre
            )
            .all()
        )

        # Reconstruir los modelos con el conteo de documentos y departamento
        modelos = []
        for row in resultados:
            # Crear una instancia del modelo con los datos
            cumplimiento = ClienteProcesoHitoCumplimientoModel(
                id=row.id,
                cliente_proceso_hito_id=row.cliente_proceso_hito_id,
                fecha=row.fecha,
                hora=row.hora,
                observacion=row.observacion,
                usuario=row.usuario,
                fecha_creacion=row.fecha_creacion,
                codSubDepar=row.codSubDepar
            )
            # Agregar atributos dinámicos
            cumplimiento.num_documentos = row.num_documentos or 0
            cumplimiento.departamento = row.departamento
            modelos.append(cumplimiento)

        return modelos

    def obtener_por_id(self, id: int):
        # Query con LEFT JOIN para contar documentos asociados y obtener departamento
        resultado = (
            self.session.query(
                ClienteProcesoHitoCumplimientoModel.id,
                ClienteProcesoHitoCumplimientoModel.cliente_proceso_hito_id,
                ClienteProcesoHitoCumplimientoModel.fecha,
                ClienteProcesoHitoCumplimientoModel.hora,
                ClienteProcesoHitoCumplimientoModel.observacion,
                ClienteProcesoHitoCumplimientoModel.usuario,
                ClienteProcesoHitoCumplimientoModel.fecha_creacion,
                ClienteProcesoHitoCumplimientoModel.codSubDepar,
                SubdeparModel.nombre.label('departamento'),
                func.count(DocumentoCumplimientoModel.id).label('num_documentos')
            )
            .outerjoin(DocumentoCumplimientoModel, ClienteProcesoHitoCumplimientoModel.id == DocumentoCumplimientoModel.cumplimiento_id)
            .outerjoin(SubdeparModel, ClienteProcesoHitoCumplimientoModel.codSubDepar == SubdeparModel.codSubDepar)
            .filter(ClienteProcesoHitoCumplimientoModel.id == id)
            .group_by(
                ClienteProcesoHitoCumplimientoModel.id,
                ClienteProcesoHitoCumplimientoModel.cliente_proceso_hito_id,
                ClienteProcesoHitoCumplimientoModel.fecha,
                ClienteProcesoHitoCumplimientoModel.hora,
                ClienteProcesoHitoCumplimientoModel.observacion,
                ClienteProcesoHitoCumplimientoModel.usuario,
                ClienteProcesoHitoCumplimientoModel.fecha_creacion,
                ClienteProcesoHitoCumplimientoModel.codSubDepar,
                SubdeparModel.nombre
            )
            .first()
        )

        if not resultado:
            return None

        # Reconstruir el modelo con el conteo de documentos y departamento
        modelo = ClienteProcesoHitoCumplimientoModel(
            id=resultado.id,
            cliente_proceso_hito_id=resultado.cliente_proceso_hito_id,
            fecha=resultado.fecha,
            hora=resultado.hora,
            observacion=resultado.observacion,
            usuario=resultado.usuario,
            fecha_creacion=resultado.fecha_creacion,
            codSubDepar=resultado.codSubDepar
        )
        modelo.num_documentos = resultado.num_documentos or 0
        modelo.departamento = resultado.departamento
        return modelo

    def actualizar(self, id: int, data: dict):
        modelo = self.session.query(ClienteProcesoHitoCumplimientoModel).filter(
            ClienteProcesoHitoCumplimientoModel.id == id
        ).first()

        if not modelo:
            return None

        # Actualizar los campos proporcionados
        for campo, valor in data.items():
            if hasattr(modelo, campo):
                setattr(modelo, campo, valor)

        self.session.commit()
        self.session.refresh(modelo)
        return modelo

    def eliminar(self, id: int):
        modelo = self.session.query(ClienteProcesoHitoCumplimientoModel).filter(
            ClienteProcesoHitoCumplimientoModel.id == id
        ).first()

        if not modelo:
            return False

        self.session.delete(modelo)
        self.session.commit()
        return True

    def obtener_por_cliente_proceso_hito_id(self, cliente_proceso_hito_id: int):
        # Query con LEFT JOIN para contar documentos asociados a cada cumplimiento y obtener departamento
        # SQL Server requiere que todas las columnas estén en GROUP BY
        resultados = (
            self.session.query(
                ClienteProcesoHitoCumplimientoModel.id,
                ClienteProcesoHitoCumplimientoModel.cliente_proceso_hito_id,
                ClienteProcesoHitoCumplimientoModel.fecha,
                ClienteProcesoHitoCumplimientoModel.hora,
                ClienteProcesoHitoCumplimientoModel.observacion,
                ClienteProcesoHitoCumplimientoModel.usuario,
                ClienteProcesoHitoCumplimientoModel.fecha_creacion,
                ClienteProcesoHitoCumplimientoModel.codSubDepar,
                SubdeparModel.nombre.label('departamento'),
                func.count(DocumentoCumplimientoModel.id).label('num_documentos')
            )
            .outerjoin(DocumentoCumplimientoModel, ClienteProcesoHitoCumplimientoModel.id == DocumentoCumplimientoModel.cumplimiento_id)
            .outerjoin(SubdeparModel, ClienteProcesoHitoCumplimientoModel.codSubDepar == SubdeparModel.codSubDepar)
            .filter(ClienteProcesoHitoCumplimientoModel.cliente_proceso_hito_id == cliente_proceso_hito_id)
            .group_by(
                ClienteProcesoHitoCumplimientoModel.id,
                ClienteProcesoHitoCumplimientoModel.cliente_proceso_hito_id,
                ClienteProcesoHitoCumplimientoModel.fecha,
                ClienteProcesoHitoCumplimientoModel.hora,
                ClienteProcesoHitoCumplimientoModel.observacion,
                ClienteProcesoHitoCumplimientoModel.usuario,
                ClienteProcesoHitoCumplimientoModel.fecha_creacion,
                ClienteProcesoHitoCumplimientoModel.codSubDepar,
                SubdeparModel.nombre
            )
            .all()
        )

        # Reconstruir los modelos con el conteo de documentos y departamento
        modelos = []
        for row in resultados:
            cumplimiento = ClienteProcesoHitoCumplimientoModel(
                id=row.id,
                cliente_proceso_hito_id=row.cliente_proceso_hito_id,
                fecha=row.fecha,
                hora=row.hora,
                observacion=row.observacion,
                usuario=row.usuario,
                fecha_creacion=row.fecha_creacion,
                codSubDepar=row.codSubDepar
            )
            cumplimiento.num_documentos = row.num_documentos or 0
            cumplimiento.departamento = row.departamento
            modelos.append(cumplimiento)

        return modelos

    def obtener_historial_por_cliente_id(self, cliente_id: str):
        """Obtiene el historial de cumplimientos de un cliente con información completa de proceso e hito"""
        from sqlalchemy import text

        query = text("""
            SELECT cpc.id, cpc.fecha, cpc.hora, cpc.usuario, cpc.observacion, cpc.fecha_creacion, cpc.codSubDepar, sd.nombre as departamento,
                   p.id as proceso_id, p.nombre AS proceso, h.id as hito_id, h.nombre AS hito,
                   cph.fecha_limite, cph.hora_limite,
                   COUNT(dc.id) as num_documentos
            FROM cliente_proceso_hito_cumplimiento cpc
            JOIN cliente_proceso_hito cph ON cph.id = cpc.cliente_proceso_hito_id
            JOIN cliente_proceso cp ON cp.id = cph.cliente_proceso_id
            JOIN proceso p ON p.id = cp.proceso_id
            JOIN hito h ON h.id = cph.hito_id
            LEFT JOIN documentos_cumplimiento dc ON dc.cumplimiento_id = cpc.id
            LEFT JOIN subdepar sd ON sd.codSubDePar = cpc.codSubDepar
            WHERE cp.cliente_id = :cliente_id
            GROUP BY cpc.id, cpc.fecha, cpc.hora, cpc.usuario, cpc.observacion, cpc.fecha_creacion, cpc.codSubDepar, sd.nombre,
                     p.id, p.nombre, h.id, h.nombre, cph.fecha_limite, cph.hora_limite
            ORDER BY cpc.id DESC
        """)

        result = self.session.execute(query, {"cliente_id": cliente_id})
        return result.fetchall()
