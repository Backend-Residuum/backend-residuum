from pydantic import BaseModel
from typing import Optional

class ColetaCreate(BaseModel):
    descarte_id: int
    peso_real: float
    responsavel: str
    observacao: Optional[str] = None


class ColetaResponse(BaseModel):
    id: int
    descarte_id: int
    peso_real: float
    responsavel: str

    class Config:
        from_attributes = True