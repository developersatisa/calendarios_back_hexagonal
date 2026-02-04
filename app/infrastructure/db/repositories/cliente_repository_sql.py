from typing import List, Optional
from sqlalchemy.orm import Session
from app.domain.repositories.cliente_repository import ClienteRepository
from app.domain.entities.cliente import Cliente
from app.infrastructure.db.models.cliente_model import ClienteModel
from app.infrastructure.db.models.cliente_proceso_model import ClienteProcesoModel
from app.infrastructure.db.models.cliente_proceso_hito_model import ClienteProcesoHitoModel

class ClienteRepositorySQL(ClienteRepository):
    def __init__(self, session: Session):
        self.session = session

    def listar(self) -> List[Cliente]:
        registros = self.session.query(ClienteModel).all()
        return [self._mapear_modelo_a_entidad(r) for r in registros]

    def buscar_por_nombre(self, nombre: str) -> List[Cliente]:
        registros = self.session.query(ClienteModel).filter(
            ClienteModel.razsoc.ilike(f"%{nombre}%")
        ).all()
        return [self._mapear_modelo_a_entidad(r) for r in registros]

    def buscar_por_cif(self, cif: str) -> Optional[Cliente]:
        registro = self.session.query(ClienteModel).filter_by(cif=cif).first()
        return self._mapear_modelo_a_entidad(registro) if registro else None

    def listar_con_hitos(self) -> List[Cliente]:
        """
        Lista los clientes que tienen al menos un hito en la tabla cliente_proceso_hito.
        Usa DISTINCT para no repetir clientes.
        """
        registros = (
            self.session.query(ClienteModel)
            .join(ClienteProcesoModel, ClienteModel.idcliente == ClienteProcesoModel.cliente_id)
            .join(ClienteProcesoHitoModel, ClienteProcesoModel.id == ClienteProcesoHitoModel.cliente_proceso_id)
            .distinct()
            .all()
        )
        return [self._mapear_modelo_a_entidad(r) for r in registros]

# si alguno de los que lean este codigo se pregunta porque demonios hemos hecho esta funcion...le doy 2 tiros...no es coña,
# la razon es porque esta entidad no depende de este backend, sino que es una entidad externa, que puede ser que cambie, es deicr que se le pongan campos por ejemplo o camvias nombres....
# con esto evitamos que si esto sucede pues no reviente nuestro back.
    def _mapear_modelo_a_entidad(self, modelo: ClienteModel) -> Cliente:
        return Cliente(
            idcliente=modelo.idcliente,
            cif=modelo.cif,
            cif_empresa=modelo.cif_empresa,
            razsoc=modelo.razsoc,
            direccion=modelo.direccion,
            localidad=modelo.localidad,
            provincia=modelo.provincia,
            cpostal=modelo.cpostal,
            codigop=modelo.codigop,
            pais=modelo.pais,
            cif_factura=modelo.cif_factura,
        )

    def obtener_por_id(self, id: str) -> Optional[Cliente]:
        registro = self.session.query(ClienteModel).filter_by(idcliente=id).first()
        return self._mapear_modelo_a_entidad(registro) if registro else None

    def listar_por_hito_id(self, hito_id: int) -> List[Cliente]:
        """
        Lista los clientes que tienen un hito específico en su calendario.
        Usa DISTINCT para no repetir clientes.
        """
        registros = (
            self.session.query(ClienteModel)
            .join(ClienteProcesoModel, ClienteModel.idcliente == ClienteProcesoModel.cliente_id)
            .join(ClienteProcesoHitoModel, ClienteProcesoModel.id == ClienteProcesoHitoModel.cliente_proceso_id)
            .filter(ClienteProcesoHitoModel.hito_id == hito_id)
            .distinct()
            .all()
        )
        return [self._mapear_modelo_a_entidad(r) for r in registros]

    def listar_empresas_usuario(self, email: str) -> List[Cliente]:
        from sqlalchemy import text
        query = text("""
            SELECT c.* FROM [ATISA_Input].dbo.clientes c
            JOIN [ATISA_Input].dbo.clienteSubDepar csd ON c.CIF = csd.cif
            JOIN [ATISA_Input].dbo.SubDepar sd ON sd.codSubDepar = csd.codSubDepar
            JOIN [BI DW RRHH DEV].dbo.HDW_Cecos cc ON SUBSTRING(CAST(cc.CODIDEPAR AS VARCHAR), 24, 6) = RIGHT('000000' + CAST(sd.codSubDepar AS VARCHAR), 6) AND cc.fechafin IS NULL
            JOIN [BI DW RRHH DEV].dbo.Persona per ON per.Numeross = cc.Numeross
            WHERE per.email = :email
        """)

        # Ejecutar la consulta mapeando a ClienteModel
        registros = self.session.query(ClienteModel).from_statement(query).params(email=email).all()
        return [self._mapear_modelo_a_entidad(r) for r in registros]
