# app/infrastructure/db/repositories/cliente_proceso_hito_cumplimiento_repository_sql.py

from sqlalchemy import func
from app.domain.entities.cliente_proceso_hito_cumplimiento import ClienteProcesoHitoCumplimiento
from app.domain.repositories.cliente_proceso_hito_cumplimiento_repository import ClienteProcesoHitoCumplimientoRepository
from app.infrastructure.db.models.cliente_proceso_hito_cumplimiento_model import ClienteProcesoHitoCumplimientoModel
from app.infrastructure.db.models.documentos_cumplimiento_model import DocumentoCumplimientoModel

class ClienteProcesoHitoCumplimientoRepositorySQL(ClienteProcesoHitoCumplimientoRepository):
    def __init__(self, session):
        self.session = session

    def guardar(self, cliente_proceso_hito_cumplimiento: ClienteProcesoHitoCumplimiento):
        from datetime import datetime

        # Obtener todos los atributos de la entidad
        datos = vars(cliente_proceso_hito_cumplimiento)

        # Filtrar el campo 'id' si es None para evitar problemas con SQLAlchemy
        if datos.get('id') is None:
            datos.pop('id', None)

        # Auto-rellenar fecha_creacion si no está definida
        if datos.get('fecha_creacion') is None:
            datos['fecha_creacion'] = datetime.utcnow()

        modelo = ClienteProcesoHitoCumplimientoModel(**datos)
        self.session.add(modelo)
        self.session.commit()
        self.session.refresh(modelo)
        return modelo

    def listar(self):
        # Query con LEFT JOIN para contar documentos asociados a cada cumplimiento
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
                func.count(DocumentoCumplimientoModel.id).label('num_documentos')
            )
            .outerjoin(DocumentoCumplimientoModel, ClienteProcesoHitoCumplimientoModel.id == DocumentoCumplimientoModel.cumplimiento_id)
            .group_by(
                ClienteProcesoHitoCumplimientoModel.id,
                ClienteProcesoHitoCumplimientoModel.cliente_proceso_hito_id,
                ClienteProcesoHitoCumplimientoModel.fecha,
                ClienteProcesoHitoCumplimientoModel.hora,
                ClienteProcesoHitoCumplimientoModel.observacion,
                ClienteProcesoHitoCumplimientoModel.usuario,
                ClienteProcesoHitoCumplimientoModel.fecha_creacion
            )
            .all()
        )

        # Reconstruir los modelos con el conteo de documentos
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
                fecha_creacion=row.fecha_creacion
            )
            # Agregar el atributo dinámico num_documentos
            cumplimiento.num_documentos = row.num_documentos or 0
            modelos.append(cumplimiento)

        return modelos

    def obtener_por_id(self, id: int):
        # Query con LEFT JOIN para contar documentos asociados
        resultado = (
            self.session.query(
                ClienteProcesoHitoCumplimientoModel.id,
                ClienteProcesoHitoCumplimientoModel.cliente_proceso_hito_id,
                ClienteProcesoHitoCumplimientoModel.fecha,
                ClienteProcesoHitoCumplimientoModel.hora,
                ClienteProcesoHitoCumplimientoModel.observacion,
                ClienteProcesoHitoCumplimientoModel.usuario,
                ClienteProcesoHitoCumplimientoModel.fecha_creacion,
                func.count(DocumentoCumplimientoModel.id).label('num_documentos')
            )
            .outerjoin(DocumentoCumplimientoModel, ClienteProcesoHitoCumplimientoModel.id == DocumentoCumplimientoModel.cumplimiento_id)
            .filter(ClienteProcesoHitoCumplimientoModel.id == id)
            .group_by(
                ClienteProcesoHitoCumplimientoModel.id,
                ClienteProcesoHitoCumplimientoModel.cliente_proceso_hito_id,
                ClienteProcesoHitoCumplimientoModel.fecha,
                ClienteProcesoHitoCumplimientoModel.hora,
                ClienteProcesoHitoCumplimientoModel.observacion,
                ClienteProcesoHitoCumplimientoModel.usuario,
                ClienteProcesoHitoCumplimientoModel.fecha_creacion
            )
            .first()
        )

        if not resultado:
            return None

        # Reconstruir el modelo con el conteo de documentos
        modelo = ClienteProcesoHitoCumplimientoModel(
            id=resultado.id,
            cliente_proceso_hito_id=resultado.cliente_proceso_hito_id,
            fecha=resultado.fecha,
            hora=resultado.hora,
            observacion=resultado.observacion,
            usuario=resultado.usuario,
            fecha_creacion=resultado.fecha_creacion
        )
        modelo.num_documentos = resultado.num_documentos or 0
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
        # Query con LEFT JOIN para contar documentos asociados a cada cumplimiento
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
                func.count(DocumentoCumplimientoModel.id).label('num_documentos')
            )
            .outerjoin(DocumentoCumplimientoModel, ClienteProcesoHitoCumplimientoModel.id == DocumentoCumplimientoModel.cumplimiento_id)
            .filter(ClienteProcesoHitoCumplimientoModel.cliente_proceso_hito_id == cliente_proceso_hito_id)
            .group_by(
                ClienteProcesoHitoCumplimientoModel.id,
                ClienteProcesoHitoCumplimientoModel.cliente_proceso_hito_id,
                ClienteProcesoHitoCumplimientoModel.fecha,
                ClienteProcesoHitoCumplimientoModel.hora,
                ClienteProcesoHitoCumplimientoModel.observacion,
                ClienteProcesoHitoCumplimientoModel.usuario,
                ClienteProcesoHitoCumplimientoModel.fecha_creacion
            )
            .all()
        )

        # Reconstruir los modelos con el conteo de documentos
        modelos = []
        for row in resultados:
            cumplimiento = ClienteProcesoHitoCumplimientoModel(
                id=row.id,
                cliente_proceso_hito_id=row.cliente_proceso_hito_id,
                fecha=row.fecha,
                hora=row.hora,
                observacion=row.observacion,
                usuario=row.usuario,
                fecha_creacion=row.fecha_creacion
            )
            cumplimiento.num_documentos = row.num_documentos or 0
            modelos.append(cumplimiento)

        return modelos

    def obtener_historial_por_cliente_id(self, cliente_id: str):
        """Obtiene el historial de cumplimientos de un cliente con información completa de proceso e hito"""
        from sqlalchemy import text

        query = text("""
            SELECT cpc.id, cpc.fecha, cpc.hora, cpc.usuario, cpc.observacion, cpc.fecha_creacion,
                   p.id as proceso_id, p.nombre AS proceso, h.id as hito_id, h.nombre AS hito,
                   cph.fecha_limite, cph.hora_limite,
                   COUNT(dc.id) as num_documentos
            FROM cliente_proceso_hito_cumplimiento cpc
            JOIN cliente_proceso_hito cph ON cph.id = cpc.cliente_proceso_hito_id
            JOIN cliente_proceso cp ON cp.id = cph.cliente_proceso_id
            JOIN proceso p ON p.id = cp.proceso_id
            JOIN hito h ON h.id = cph.hito_id
            LEFT JOIN documentos_cumplimiento dc ON dc.cumplimiento_id = cpc.id
            WHERE cp.cliente_id = :cliente_id
            GROUP BY cpc.id, cpc.fecha, cpc.hora, cpc.usuario, cpc.observacion, cpc.fecha_creacion,
                     p.id, p.nombre, h.id, h.nombre, cph.fecha_limite, cph.hora_limite
            ORDER BY cpc.id DESC
        """)

        result = self.session.execute(query, {"cliente_id": cliente_id})
        return result.fetchall()

    def cumplir_masivo(self, cliente_proceso_hito_ids: list[int], fecha: str, hora: str = None,
                      observacion: str = None, usuario: str = None):
        """Implementación de cumplimiento masivo por lista de IDs"""
        from app.infrastructure.db.models.cliente_proceso_hito_model import ClienteProcesoHitoModel
        from datetime import datetime

        # 1. Buscar los hitos candidatos (solo habilitados)
        hitos_candidatos = self.session.query(ClienteProcesoHitoModel).filter(
            ClienteProcesoHitoModel.id.in_(cliente_proceso_hito_ids),
            ClienteProcesoHitoModel.habilitado == True
        ).all()

        cumplimientos_creados = 0

        for hito in hitos_candidatos:
            # Crear cumplimiento
            nuevo_cumplimiento = ClienteProcesoHitoCumplimientoModel(
                cliente_proceso_hito_id=hito.id,
                fecha=fecha,
                hora=hora,
                observacion=observacion,
                usuario=usuario,
                fecha_creacion=datetime.utcnow()
            )
            self.session.add(nuevo_cumplimiento)

            # Actualizar estado del hito
            hito.estado = "Finalizado"
            hito.fecha_estado = datetime.utcnow()

            cumplimientos_creados += 1

        self.session.commit()
        return cumplimientos_creados
