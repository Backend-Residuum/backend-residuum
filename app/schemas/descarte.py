from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DescarteCreate(BaseModel):
    quantidade: float
    tipo_residuo: str
    observacao: Optional[str] = "Descarte via APP"
    usuario_lat: float
    usuario_long: float
    ponto_lat: float
    ponto_long: float

class DescarteConfirmar(BaseModel):
    quantidade_confirmada: float

class DescarteResponse(BaseModel):
    id_descarte: int
    status: str
    quantidade: float
    data_desc: datetime

    class Config:
        from_attributes = True