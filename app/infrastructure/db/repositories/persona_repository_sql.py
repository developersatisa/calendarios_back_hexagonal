from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.domain.repositories.persona_repository import PersonaRepository
from app.domain.entities.persona import Persona

class PersonaRepositorySQL(PersonaRepository):
    def __init__(self, session: Session):
        self.session = session

    def _mapear_a_entidad(self, row) -> Persona:
        return Persona(
            NIF=row.NIF,
            Nombre=row.Nombre,
            Apellido1=row.Apellido1,
            Apellido2=row.Apellido2,
            email=row.email
        )

    def listar(self) -> List[Persona]:
        query = text("SELECT NIF, Nombre, Apellido1, Apellido2, email FROM [BI DW RRHH DEV].dbo.Persona WHERE fechabaja IS NULL")
        result = self.session.execute(query).fetchall()
        return [self._mapear_a_entidad(row) for row in result]

    def buscar_por_email(self, email: str) -> Optional[Persona]:
        query = text("SELECT NIF, Nombre, Apellido1, Apellido2, email FROM [BI DW RRHH DEV].dbo.Persona WHERE email = :email AND fechabaja IS NULL")
        result = self.session.execute(query, {"email": email}).fetchone()
        return self._mapear_a_entidad(result) if result else None

    def buscar_por_nif(self, nif: str) -> Optional[Persona]:
        query = text("SELECT NIF, Nombre, Apellido1, Apellido2, email FROM [BI DW RRHH DEV].dbo.Persona WHERE NIF = :nif AND fechabaja IS NULL")
        result = self.session.execute(query, {"nif": nif}).fetchone()
        return self._mapear_a_entidad(result) if result else None
