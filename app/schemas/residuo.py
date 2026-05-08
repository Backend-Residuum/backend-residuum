from pydantic import BaseModel


class ResiduoCreate(BaseModel):

    nome: str

    codigo_barras: str

    quantidade: int


class ResiduoResponse(BaseModel):

    id: int

    nome: str

    codigo_barras: str

    quantidade: int

    class Config:
        from_attributes = True