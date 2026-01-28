from datetime import datetime
from typing import Optional

class DocumentalDocumentos:
    def __init__(self, id=None, cliente_id=None, categoria_id=None, nombre_documento=None, original_file_name=None, stored_file_name=None, fecha_creacion=None):
        self.id = id
        self.cliente_id = cliente_id
        self.categoria_id = categoria_id
        self.nombre_documento = nombre_documento
        self.original_file_name = original_file_name
        self.stored_file_name = stored_file_name
        self.fecha_creacion = fecha_creacion
