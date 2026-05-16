"""
Schemas para Ponto de Coleta

Define os modelos Pydantic para criação e validação de pontos de coleta.
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any


class PontoColetaCreate(BaseModel):
    """Modelo para criação de um novo ponto de coleta."""
    nome: str
    endereco: Optional[str] = None
    latitude: float
    longitude: float
    raio_operacao: Optional[float] = 1000.0


class PontoColetaUpdate(BaseModel):
    """Modelo para atualização de um ponto de coleta."""
    nome: Optional[str] = None
    endereco: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    raio_operacao: Optional[float] = None
    ativo: Optional[int] = None


class PontoColetaResponse(BaseModel):
    """Modelo de resposta para um ponto de coleta."""
    id: int
    nome: str
    endereco: Optional[str]
    latitude: float
    longitude: float
    raio_operacao: float
    inventario: Dict[str, Any]
    ativo: int
    data_criacao: datetime
    data_atualizacao: datetime

    class Config:
        from_attributes = True
