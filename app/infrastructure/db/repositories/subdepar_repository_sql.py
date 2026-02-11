from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.domain.repositories.subdepar_repository import SubdeparRepository
from app.domain.entities.subdepar import Subdepar
from app.infrastructure.db.models.subdepar_model import SubdeparModel

class SubdeparRepositorySQL(SubdeparRepository):
    def __init__(self, session: Session):
        self.session = session

    def listar(self) -> List[Subdepar]:
        registros = self.session.query(SubdeparModel).all()
        return [self._mapear_modelo_a_entidad(r) for r in registros]

    def obtener_por_id(self, id: int) -> Optional[Subdepar]:
        registro = self.session.query(SubdeparModel).filter_by(id=id).first()
        return self._mapear_modelo_a_entidad(registro) if registro else None

    def obtener_por_cliente(self, id_cliente: str) -> List[Dict[str, Any]]:
        query = text("""
            SELECT sd.codSubDepar, sd.nombre
            FROM [ATISA_Input].dbo.clientes c
            JOIN [ATISA_Input].dbo.clienteSubDepar csd ON c.CIF = csd.cif
            JOIN [ATISA_Input].dbo.SubDepar sd ON sd.codSubDepar = csd.codSubDepar
            JOIN [BI DW RRHH DEV].dbo.HDW_Cecos cc
                ON SUBSTRING(CAST(cc.CODIDEPAR AS VARCHAR), 24, 6) = RIGHT('000000' + CAST(sd.codSubDepar AS VARCHAR), 6)
                AND cc.fechafin IS NULL
            JOIN [BI DW RRHH DEV].dbo.Persona per ON per.Numeross = cc.Numeross
            WHERE c.idcliente = :id_cliente
            GROUP BY sd.codSubDepar, sd.nombre;
        """)

        resultados = self.session.execute(query, {"id_cliente": id_cliente}).fetchall()

        return [
            {"codSubDepar": row.codSubDepar, "nombre": row.nombre}
            for row in resultados
        ]


    def _mapear_modelo_a_entidad(self, modelo: SubdeparModel) -> Subdepar:
        return Subdepar(
            id=modelo.id,
            codidepar=modelo.codidepar,
            ceco=modelo.ceco,
            codSubDepar=modelo.codSubDepar,
            nombre=modelo.nombre,
            fechaini=modelo.fechaini,
            fechafin=modelo.fechafin,
        )
