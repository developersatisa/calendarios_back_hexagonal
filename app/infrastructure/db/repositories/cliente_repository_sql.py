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

    def listar_con_departamentos(self, limit: int, offset: int, search: Optional[str] = None, sort_field: Optional[str] = None, sort_direction: str = "asc") -> tuple[List[Cliente], int]:
        from sqlalchemy import text

        # Base query structure for counting and data
        # Debe coincidir con los criterios de la consulta de departamentos
        base_query = """
            FROM [ATISA_Input].dbo.clientes c
            WHERE EXISTS (
                SELECT 1
                FROM [ATISA_Input].dbo.clienteSubDepar csd
                JOIN [ATISA_Input].dbo.SubDepar sd ON sd.codSubDepar = csd.codSubDepar
                JOIN [BI DW RRHH DEV].dbo.HDW_Cecos cc
                    ON SUBSTRING(CAST(cc.CODIDEPAR AS VARCHAR), 24, 6) = RIGHT('000000' + CAST(sd.codSubDepar AS VARCHAR), 6)
                    AND cc.fechafin IS NULL
                JOIN [BI DW RRHH DEV].dbo.Persona per ON per.Numeross = cc.Numeross
                WHERE csd.cif = c.CIF
            )
        """

        params = {}

        # Apply search filter if provided
        if search:
            base_query += " AND (c.cif LIKE :search OR c.razsoc LIKE :search)"
            params["search"] = f"%{search}%"

        # Count total records
        count_query = text(f"SELECT COUNT(*) {base_query}")
        total = self.session.execute(count_query, params).scalar()

        # Build order by clause
        # Map sort_field to column names if needed, default to idcliente
        valid_sort_fields = {"idcliente": "c.idcliente", "cif": "c.cif", "razsoc": "c.razsoc"}
        order_col = valid_sort_fields.get(sort_field, "c.idcliente")
        order_dir = "DESC" if sort_direction.lower() == "desc" else "ASC"

        # Fetch page data
        data_query = text(f"""
            SELECT c.*
            {base_query}
            ORDER BY {order_col} {order_dir}
            OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
        """)

        params["offset"] = offset
        params["limit"] = limit

        registros = self.session.query(ClienteModel).from_statement(data_query).params(**params).all()
        clientes = [self._mapear_modelo_a_entidad(r) for r in registros]

        # Si hay clientes, obtenemos sus departamentos
        if clientes:
            ids_clientes = [c.idcliente for c in clientes]

            # Construir query para departamentos con placeholders dinámicos para IN clause
            # SQL Server con pyodbc no soporta binding de tuplas directamente
            placeholders = ', '.join([f':id{i}' for i in range(len(ids_clientes))])
            dept_query_str = f"""
                SELECT c.idcliente, sd.codSubDepar, sd.nombre,
                       cac.id as config_id,
                       CAST(cac.aviso_vence_hoy AS INT) as aviso_vence_hoy,
                       cac.temporicidad_vence_hoy,
                       cac.tiempo_vence_hoy,
                       cac.hora_vence_hoy,
                       CAST(cac.aviso_proximo_vencimiento AS INT) as aviso_proximo_vencimiento,
                       cac.temporicidad_proximo_vencimiento,
                       cac.tiempo_proximo_vencimiento,
                       cac.hora_proximo_vencimiento,
                       cac.dias_proximo_vencimiento,
                       CAST(cac.aviso_vencido AS INT) as aviso_vencido,
                       cac.temporicidad_vencido,
                       cac.tiempo_vencido,
                       cac.hora_vencido,
                       CAST(cac.config_global AS INT) as config_global,
                       cac.temporicidad_global,
                       cac.tiempo_global,
                       cac.hora_global
                FROM [ATISA_Input].dbo.clientes c
                JOIN [ATISA_Input].dbo.clienteSubDepar csd ON c.CIF = csd.cif
                JOIN [ATISA_Input].dbo.SubDepar sd ON sd.codSubDepar = csd.codSubDepar
                JOIN [BI DW RRHH DEV].dbo.HDW_Cecos cc
                    ON SUBSTRING(CAST(cc.CODIDEPAR AS VARCHAR), 24, 6) = RIGHT('000000' + CAST(sd.codSubDepar AS VARCHAR), 6)
                    AND cc.fechafin IS NULL
                JOIN [BI DW RRHH DEV].dbo.Persona per ON per.Numeross = cc.Numeross
                LEFT JOIN config_avisos_calendarios cac
                    ON cac.cliente_id COLLATE DATABASE_DEFAULT = c.idcliente COLLATE DATABASE_DEFAULT
                    AND cac.codSubDepar COLLATE DATABASE_DEFAULT = sd.codSubDepar COLLATE DATABASE_DEFAULT
                WHERE c.idcliente IN ({placeholders})
                GROUP BY c.idcliente, sd.codSubDepar, sd.nombre,
                         cac.id, cac.aviso_vence_hoy, cac.temporicidad_vence_hoy, cac.tiempo_vence_hoy, cac.hora_vence_hoy,
                         cac.aviso_proximo_vencimiento, cac.temporicidad_proximo_vencimiento, cac.tiempo_proximo_vencimiento, cac.hora_proximo_vencimiento, cac.dias_proximo_vencimiento,
                         cac.aviso_vencido, cac.temporicidad_vencido, cac.tiempo_vencido, cac.hora_vencido,
                         cac.config_global, cac.temporicidad_global, cac.tiempo_global, cac.hora_global
            """

            dept_query = text(dept_query_str)

            # Crear diccionario de parámetros con id0, id1, id2, etc.
            dept_params = {f'id{i}': id_cliente for i, id_cliente in enumerate(ids_clientes)}

            dept_results = self.session.execute(dept_query, dept_params).fetchall()

            # Map departments to clients
            dept_map = {}
            for row in dept_results:
                if row.idcliente not in dept_map:
                    dept_map[row.idcliente] = []

                dept_data = {
                    "codSubDepar": row.codSubDepar,
                    "nombre": row.nombre,
                    "configuracion": None
                }

                if row.config_id is not None:
                    dept_data["configuracion"] = {
                        "id": row.config_id,
                        "aviso_vence_hoy": bool(row.aviso_vence_hoy),
                        "temporicidad_vence_hoy": row.temporicidad_vence_hoy,
                        "tiempo_vence_hoy": row.tiempo_vence_hoy,
                        "hora_vence_hoy": str(row.hora_vence_hoy) if row.hora_vence_hoy else None,
                        "aviso_proximo_vencimiento": bool(row.aviso_proximo_vencimiento),
                        "temporicidad_proximo_vencimiento": row.temporicidad_proximo_vencimiento,
                        "tiempo_proximo_vencimiento": row.tiempo_proximo_vencimiento,
                        "hora_proximo_vencimiento": str(row.hora_proximo_vencimiento) if row.hora_proximo_vencimiento else None,
                        "dias_proximo_vencimiento": row.dias_proximo_vencimiento,
                        "aviso_vencido": bool(row.aviso_vencido),
                        "temporicidad_vencido": row.temporicidad_vencido,
                        "tiempo_vencido": row.tiempo_vencido,
                        "hora_vencido": str(row.hora_vencido) if row.hora_vencido else None,
                        "config_global": bool(row.config_global) if row.config_global is not None else None,
                        "temporicidad_global": row.temporicidad_global,
                        "tiempo_global": row.tiempo_global,
                        "hora_global": str(row.hora_global) if row.hora_global else None
                    }

                dept_map[row.idcliente].append(dept_data)

            # Attach to client dicts
            results = []
            for client in clientes:
                client_dict = vars(client)
                # Remove internal sqlalchemy state if present
                if "_sa_instance_state" in client_dict:
                    del client_dict["_sa_instance_state"]

                client_dict["departamentos"] = dept_map.get(client.idcliente, [])
                results.append(client_dict)

            return results, total

        return [], total
