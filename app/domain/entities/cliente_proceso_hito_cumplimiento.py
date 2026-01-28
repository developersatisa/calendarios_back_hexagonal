from datetime import datetime

class ClienteProcesoHitoCumplimiento:
    def __init__(self, id=None, cliente_proceso_hito_id=None, fecha=None, hora=None, observacion=None, usuario=None, fecha_creacion=None):
        self.id = id
        self.cliente_proceso_hito_id = cliente_proceso_hito_id
        self.fecha = fecha
        self.hora = hora
        self.observacion = observacion
        self.usuario = usuario
        self.fecha_creacion = fecha_creacion
