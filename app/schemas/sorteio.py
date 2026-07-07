"""Schemas de sorteios."""

from datetime import datetime

from pydantic import BaseModel


class SorteioResponse(BaseModel):
    id: int
    titulo: str
    descricao: str | None = None
    premio: str
    custo_pontos: int
    status: str
    data_inicio: datetime | None = None
    data_fim: datetime | None = None
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True
