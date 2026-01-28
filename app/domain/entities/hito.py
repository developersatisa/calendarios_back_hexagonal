from datetime import date, time

class Hito:
    def __init__(self,id = None, nombre: str = None, fecha_limite: date = None, hora_limite: time = None, descripcion: str = None, obligatorio: bool = False, tipo: str = None, habilitado: bool = True):
        self.id = id
        self.nombre = nombre
        self.descripcion = descripcion
        self.fecha_limite = fecha_limite
        self.hora_limite = hora_limite
        self.obligatorio = obligatorio
        self.tipo = tipo
        self.habilitado = habilitado
