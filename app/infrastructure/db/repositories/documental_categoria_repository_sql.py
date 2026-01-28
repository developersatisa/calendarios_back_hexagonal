from typing import List
from sqlalchemy.orm import Session
from app.domain.repositories.documental_categoria_repository import DocumentalCategoriaRepository
from app.domain.entities.documental_categoria import DocumentalCategoria
from app.infrastructure.db.models.documental_categoria_model import DocumentalCategoriaModel

class SqlDocumentalCategoriaRepository(DocumentalCategoriaRepository):
    def __init__(self, session: Session):
        self.session = session

    def guardar(self, documento_categoria: DocumentalCategoria):
        modelo = DocumentalCategoriaModel(**documento_categoria.__dict__)
        self.session.add(modelo)
        self.session.commit()
        self.session.refresh(modelo)
        return modelo

    def actualizar(self, id: int, data: dict):
        documental_categoria = self.session.query(DocumentalCategoriaModel).filter_by(id=id).first()
        if not documental_categoria:
            return None

        for key, value in data.items():
            setattr(documental_categoria, key, value)

        self.session.commit()
        self.session.refresh(documental_categoria)
        return documental_categoria

    def listar(self):
        return self.session.query(DocumentalCategoriaModel).all()

    def obtener_por_id(self, id: int):
        return self.session.query(DocumentalCategoriaModel).filter_by(id=id).first()

    def obtener_por_cliente(self, cliente_id: str):
        return self.session.query(DocumentalCategoriaModel).filter_by(cliente_id=cliente_id).all()

    def eliminar(self, id: int):
        documento_categoria = self.session.query(DocumentalCategoriaModel).filter_by(id=id).first()
        if not documento_categoria:
            return None
        self.session.delete(documento_categoria)
        self.session.commit()
        return True
