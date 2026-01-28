from app.domain.repositories.proceso_repository import ProcesoRepository
from app.domain.entities.proceso import Proceso
from sqlalchemy import text
from collections import OrderedDict
from app.infrastructure.db.models import ProcesoModel
from app.infrastructure.db.compartido.mis_clientes_cte import MIS_CLIENTES_CTE
from app.infrastructure.db.compartido.mis_clientes_cte import construir_sql_procesos_cliente_por_empleado


class ProcesoRepositorySQL(ProcesoRepository):
    def __init__(self, session):
        self.session = session

    def guardar(self, proceso: Proceso):
        modelo = ProcesoModel(**vars(proceso))
        self.session.add(modelo)
        self.session.commit()
        self.session.refresh(modelo)
        return modelo

    def actualizar(self, id: int, data: dict):
        proceso = self.session.query(ProcesoModel).filter_by(id=id).first()
        if not proceso:
            return None

        for key, value in data.items():
            setattr(proceso, key, value)

        self.session.commit()
        self.session.refresh(proceso)
        return proceso

    def listar(self):
        return self.session.query(ProcesoModel).all()

    def listar_habilitados(self):
        """Lista solo los procesos habilitados (habilitado=True)"""
        return self.session.query(ProcesoModel).filter_by(habilitado=True).all()

    def obtener_por_id(self, id: int):
        return self.session.query(ProcesoModel).filter_by(id=id).first()

    def eliminar(self, id: int):
        proceso = self.session.query(ProcesoModel).filter_by(id=id).first()
        if not proceso:
            return None
        self.session.delete(proceso)
        self.session.commit()
        return True

    def listar_procesos_cliente_por_empleado(self, email: str, mes=None, anio=None):
        sql = construir_sql_procesos_cliente_por_empleado(
            filtrar_fecha=False,
            filtrar_mes=bool(mes),
            filtrar_anio=bool(anio)
        )

        params = {
            "email": email,
            "mes": mes,
            "anio": anio
        }

        result = self.session.execute(text(sql), params)
        rows = result.mappings().all()

        clientes = OrderedDict()
        for r in rows:
            cid = r["cliente_id"]
            if cid not in clientes:
                clientes[cid] = {
                    "cliente": {
                        "id": cid,
                        "nombre": r["cliente_nombre"]
                    },
                    "procesos": OrderedDict()
                }
            pid = r["proceso_id"]
            proc_map = clientes[cid]["procesos"]
            if pid not in proc_map:
                proc_map[pid] = {
                    "id": pid,
                    "nombre": r["proceso_nombre"]
                }

        resultado = []
        for entry in clientes.values():
            entry["procesos"] = list(entry["procesos"].values())
            resultado.append(entry)

        return resultado
