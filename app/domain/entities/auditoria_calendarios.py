class AuditoriaCalendarios:
    def __init__(self, id=None, cliente_id="", hito_id=0, campo_modificado="",
                 valor_anterior=None, valor_nuevo=None, observaciones=None,
                 motivo: int = None, usuario="", codSubDepar=None,
                 fecha_modificacion=None, created_at=None, updated_at=None):
        self.id = id
        self.cliente_id = cliente_id
        self.hito_id = hito_id  # ID del ClienteProcesoHito
        self.campo_modificado = campo_modificado
        self.valor_anterior = valor_anterior
        self.valor_nuevo = valor_nuevo
        self.observaciones = observaciones
        self.motivo = motivo
        self.usuario = usuario
        self.codSubDepar = codSubDepar
        self.fecha_modificacion = fecha_modificacion
        self.created_at = created_at
        self.updated_at = updated_at
