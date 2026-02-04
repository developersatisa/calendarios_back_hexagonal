from pydantic import BaseModel, EmailStr

class ActualizarRolRequest(BaseModel):
    admin: bool
