from pydantic import BaseModel, EmailStr
from typing import Optional

class CrearAdminRequest(BaseModel):
    email: EmailStr
    admin: bool = True

class ApiRolResponse(BaseModel):
    id: int
    email: str
    admin: bool

    class Config:
        from_attributes = True
