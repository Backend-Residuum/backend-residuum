"""
Schemas para Ponto de Coleta

Define os modelos Pydantic para criação, atualização e resposta de pontos de coleta.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List


TIPOS_RESIDUOS_EXEMPLO = [
    "plastico",
    "papel",
    "papelao",
    "metal",
    "vidro",
    "aluminio",
    "cobre",
    "pilhas",
    "baterias",
]


class PontoColetaCreate(BaseModel):
    """Modelo para criação de um novo ponto de coleta."""
    nome: str
    endereco: Optional[str] = None
    latitude: float
    longitude: float
    raio_operacao: Optional[float] = 1000.0
    capacidade_maxima: Optional[float] = Field(default=None, description="Capacidade máxima estimada em kg")
    tipos_residuos_aceitos: Optional[List[str]] = Field(default=None, description="Tipos de resíduos aceitos pelo ponto")
    horario_funcionamento: Optional[str] = None
    status: Optional[str] = Field(default="ativo", description="ativo, cheio ou inativo")


class PontoColetaUpdate(BaseModel):
    """Modelo para atualização de um ponto de coleta."""
    nome: Optional[str] = None
    endereco: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    raio_operacao: Optional[float] = None
    capacidade_maxima: Optional[float] = None
    tipos_residuos_aceitos: Optional[List[str]] = None
    horario_funcionamento: Optional[str] = None
    status: Optional[str] = None
    ativo: Optional[int] = None


class PontoColetaResponse(BaseModel):
    """Modelo de resposta para um ponto de coleta."""
    id: int
    nome: str
    endereco: Optional[str]
    latitude: float
    longitude: float
    raio_operacao: float
    capacidade_maxima: Optional[float] = None
    tipos_residuos_aceitos: List[str] = []
    horario_funcionamento: Optional[str] = None
    status: str = "ativo"
    status_calculado: Optional[str] = None
    inventario: Dict[str, Any]
    total_inventario: Optional[float] = None
    percentual_ocupacao: Optional[float] = None
    distancia_km: Optional[float] = None
    ativo: int
    data_criacao: datetime
    data_atualizacao: datetime

    class Config:
        from_attributes = True
