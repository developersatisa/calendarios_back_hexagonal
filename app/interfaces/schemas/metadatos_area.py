from pydantic import BaseModel

class MetadatosAreaCreate(BaseModel):
    id_metadato: int
    codSubDepar: str

class MetadatosAreaRead(MetadatosAreaCreate):
    id: int

    class Config:
        orm_mode = True
