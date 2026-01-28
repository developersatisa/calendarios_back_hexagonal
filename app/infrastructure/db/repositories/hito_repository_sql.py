from app.domain.repositories.hito_repository import HitoRepository
from app.domain.entities.hito import Hito
from app.infrastructure.db.models import HitoModel
from sqlalchemy import text
from collections import OrderedDict
from app.infrastructure.db.compartido.mis_clientes_cte import MIS_CLIENTES_CTE
from app.infrastructure.db.compartido.mis_clientes_cte import construir_sql_hitos_cliente_por_empleado

class HitoRepositorySQL(HitoRepository):
    def __init__(self, session):
        self.session = session

    def guardar(self, hito: Hito):
        modelo = HitoModel(**vars(hito))
        self.session.add(modelo)
        self.session.commit()
        self.session.refresh(modelo)
        return modelo

    def listar(self):
        return self.session.query(HitoModel).all()

    def listar_habilitados(self):
        """Lista solo los hitos habilitados (habilitado=True)"""
        return self.session.query(HitoModel).filter_by(habilitado=True).all()

    def obtener_por_id(self, id: int):
        return self.session.query(HitoModel).filter_by(id=id).first()

    def actualizar(self, id: int, data: dict):
        hito = self.obtener_por_id(id)
        if not hito:
            return None
        for key, value in data.items():
            setattr(hito, key, value)
        self.session.commit()
        self.session.refresh(hito)
        return hito

    def eliminar(self, id: int):
        hito = self.obtener_por_id(id)
        if not hito:
            return None
        self.session.delete(hito)
        self.session.commit()
        return True

    def listar_hitos_cliente_por_empleado(self, email, fecha_inicio=None, fecha_fin=None, mes=None, anio=None):
        sql = construir_sql_hitos_cliente_por_empleado(
            filtrar_fecha=bool(fecha_inicio and fecha_fin),
            filtrar_mes=bool(mes),
            filtrar_anio=bool(anio)
        )

        params = {
            "email": email,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
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
                    "nombre": r["proceso_nombre"],
                    "fecha_inicio": r["fecha_inicio"],
                    "fecha_fin": r["fecha_fin"],
                    "hitos": []
                }

            proc_map[pid]["hitos"].append({
                "id": r["hito_id"],
                "nombre": r["hito_nombre"],
                "fecha_limite": r["fecha_limite_hito"]
            })

        resultado = []
        for entry in clientes.values():
            entry["procesos"] = list(entry["procesos"].values())
            resultado.append(entry)

        return resultado
