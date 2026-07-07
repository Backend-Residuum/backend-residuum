"""Schemas de vouchers."""

from datetime import datetime

from pydantic import BaseModel


class VoucherResponse(BaseModel):
    id: int
    titulo: str
    descricao: str | None = None
    parceiro: str
    custo_pontos: int
    quantidade_disponivel: int
    status: str
    data_inicio: datetime | None = None
    data_fim: datetime | None = None
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True
