from typing import List, Optional
from sqlalchemy.orm import Session
from app.domain.repositories.config_avisos_calendarios_repository import ConfigAvisoCalendarioRepository
from app.domain.entities.config_avisos_calendarios import ConfigAvisoCalendario
from app.infrastructure.db.models.config_avisos_calendarios_model import ConfigAvisoCalendarioModel

class ConfigAvisoCalendarioRepositorySQL(ConfigAvisoCalendarioRepository):
    def __init__(self, session: Session):
        self.session = session

    def listar(self) -> List[ConfigAvisoCalendario]:
        registros = self.session.query(ConfigAvisoCalendarioModel).all()
        return [self._mapear_modelo_a_entidad(r) for r in registros]

    def obtener_por_id(self, id: int) -> Optional[ConfigAvisoCalendario]:
        registro = self.session.query(ConfigAvisoCalendarioModel).filter(ConfigAvisoCalendarioModel.id == id).first()
        return self._mapear_modelo_a_entidad(registro) if registro else None

    def obtener_por_cod_sub_depar(self, cod_sub_depar: str) -> Optional[ConfigAvisoCalendario]:
        registro = self.session.query(ConfigAvisoCalendarioModel).filter(ConfigAvisoCalendarioModel.codSubDepar == cod_sub_depar).first()
        return self._mapear_modelo_a_entidad(registro) if registro else None

    def guardar(self, config_aviso: ConfigAvisoCalendario) -> ConfigAvisoCalendario:
        datos = vars(config_aviso)
        if datos.get('id') is None:
            datos.pop('id', None)

        modelo = ConfigAvisoCalendarioModel(**datos)
        self.session.add(modelo)
        self.session.commit()
        self.session.refresh(modelo)
        return self._mapear_modelo_a_entidad(modelo)

    def actualizar(self, id: int, data: dict) -> Optional[ConfigAvisoCalendario]:
        modelo = self.session.query(ConfigAvisoCalendarioModel).filter(ConfigAvisoCalendarioModel.id == id).first()
        if not modelo:
            return None

        for key, value in data.items():
            if hasattr(modelo, key):
                setattr(modelo, key, value)

        self.session.commit()
        self.session.refresh(modelo)
        return self._mapear_modelo_a_entidad(modelo)

    def eliminar(self, id: int) -> bool:
        modelo = self.session.query(ConfigAvisoCalendarioModel).filter(ConfigAvisoCalendarioModel.id == id).first()
        if not modelo:
            return False

        self.session.delete(modelo)
        self.session.commit()
        return True

    def _mapear_modelo_a_entidad(self, modelo: ConfigAvisoCalendarioModel) -> ConfigAvisoCalendario:
        return ConfigAvisoCalendario(
            id=modelo.id,
            cliente_id=modelo.cliente_id,
            codSubDepar=modelo.codSubDepar,
            aviso_vence_hoy=modelo.aviso_vence_hoy,
            temporicidad_vence_hoy=modelo.temporicidad_vence_hoy,
            tiempo_vence_hoy=modelo.tiempo_vence_hoy,
            hora_vence_hoy=modelo.hora_vence_hoy,
            aviso_proximo_vencimiento=modelo.aviso_proximo_vencimiento,
            temporicidad_proximo_vencimiento=modelo.temporicidad_proximo_vencimiento,
            tiempo_proximo_vencimiento=modelo.tiempo_proximo_vencimiento,
            hora_proximo_vencimiento=modelo.hora_proximo_vencimiento,
            dias_proximo_vencimiento=modelo.dias_proximo_vencimiento,
            aviso_vencido=modelo.aviso_vencido,
            temporicidad_vencido=modelo.temporicidad_vencido,
            tiempo_vencido=modelo.tiempo_vencido,
            hora_vencido=modelo.hora_vencido,
            config_global=modelo.config_global,
            temporicidad_global=modelo.temporicidad_global,
            tiempo_global=modelo.tiempo_global,
            hora_global=modelo.hora_global
        )
