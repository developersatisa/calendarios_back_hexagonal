class ConfigAvisoCalendario:
    def __init__(
        self,
        id=None,
        cliente_id=None,
        codSubDepar=None,
        aviso_vence_hoy=None,
        temporicidad_vence_hoy=None,
        tiempo_vence_hoy=None,
        hora_vence_hoy=None,
        aviso_proximo_vencimiento=None,
        temporicidad_proximo_vencimiento=None,
        tiempo_proximo_vencimiento=None,
        hora_proximo_vencimiento=None,
        dias_proximo_vencimiento=None,
        aviso_vencido=None,
        temporicidad_vencido=None,
        tiempo_vencido=None,
        hora_vencido=None,
        config_global=None,
        temporicidad_global=None,
        tiempo_global=None,
        hora_global=None
    ):
        self.id = id
        self.cliente_id = cliente_id
        self.codSubDepar = codSubDepar
        self.aviso_vence_hoy = aviso_vence_hoy
        self.temporicidad_vence_hoy = temporicidad_vence_hoy
        self.tiempo_vence_hoy = tiempo_vence_hoy
        self.hora_vence_hoy = hora_vence_hoy
        self.aviso_proximo_vencimiento = aviso_proximo_vencimiento
        self.temporicidad_proximo_vencimiento = temporicidad_proximo_vencimiento
        self.tiempo_proximo_vencimiento = tiempo_proximo_vencimiento
        self.hora_proximo_vencimiento = hora_proximo_vencimiento
        self.dias_proximo_vencimiento = dias_proximo_vencimiento
        self.aviso_vencido = aviso_vencido
        self.temporicidad_vencido = temporicidad_vencido
        self.tiempo_vencido = tiempo_vencido
        self.hora_vencido = hora_vencido
        self.config_global = config_global
        self.temporicidad_global = temporicidad_global
        self.tiempo_global = tiempo_global
        self.hora_global = hora_global
