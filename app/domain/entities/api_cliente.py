class ApiCliente:
    def __init__(self, id=None, nombre_cliente=None, hashed_key=None, activo=True, email=None):
        self.id = id
        self.nombre_cliente = nombre_cliente
        self.hashed_key = hashed_key
        self.activo = activo
        self.email = email
