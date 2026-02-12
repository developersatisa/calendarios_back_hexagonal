class DocumentalCarpetaProceso:
    def __init__(self, id=None, proceso_id=None, nombre=None, descripcion=None, fecha_creacion=None, fecha_actualizacion=None, eliminado=False):
        self.id = id
        self.proceso_id = proceso_id
        self.nombre = nombre
        self.descripcion = descripcion
        self.fecha_creacion = fecha_creacion
        self.fecha_actualizacion = fecha_actualizacion
        self.eliminado = eliminado
