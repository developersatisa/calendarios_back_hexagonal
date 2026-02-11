from sqlalchemy import text
from sqlalchemy.orm import Session

class EmpleadoSubDeparProvider:

    def __init__(self, db: Session):
        self.db = db

    def obtener_subdepar_por_email(self, email: str) -> list[str]:
        sql = text("""
        SELECT s.codSubDepar
        FROM [ATISA_Input].[dbo].[subDepar] s
        JOIN [BI DW RRHH DEV].[dbo].[HDW_Cecos] c
            ON s.codidepar = c.CODIDEPAR
        JOIN [BI DW RRHH DEV].[dbo].[Persona] p
            ON p.Numeross = c.NUMEROSS
        WHERE p.email = :email
          AND c.FECHAINI <= CAST(GETDATE() AS DATE)
          AND (c.FECHAFIN IS NULL OR c.FECHAFIN >= CAST(GETDATE() AS DATE))
        """)

        result = self.db.execute(sql, {"email": email})
        return [row.codSubDepar for row in result.fetchall()]
