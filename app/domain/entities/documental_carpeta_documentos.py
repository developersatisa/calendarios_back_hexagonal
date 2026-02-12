class DocumentalCarpetaDocumentos:
    def __init__(self, id=None, carpeta_id=None, nombre_documento=None, original_file_name=None, stored_file_name=None, autor=None, codSubDepar=None, departamento=None, fecha_creacion=None, fecha_actualizacion=None, eliminado=False):
        self.id = id
        self.carpeta_id = carpeta_id
        self.nombre_documento = nombre_documento
        self.original_file_name = original_file_name
        self.stored_file_name = stored_file_name
        self.autor = autor
        self.codSubDepar = codSubDepar
        self.departamento = departamento
        self.fecha_creacion = fecha_creacion
        self.fecha_actualizacion = fecha_actualizacion
        self.eliminado = eliminado
