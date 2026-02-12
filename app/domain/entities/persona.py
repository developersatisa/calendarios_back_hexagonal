class Persona:
    def __init__(self, NIF=None, Nombre=None, Apellido1=None, Apellido2=None, email=None, admin=False, id_api_rol=None):
        self.NIF = NIF
        self.Nombre = Nombre
        self.Apellido1 = Apellido1
        self.Apellido2 = Apellido2
        self.email = email
        self.admin = admin
        self.id_api_rol = id_api_rol
