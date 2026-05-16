"""
Modelo de Ponto de Coleta

Define a estrutura da tabela 'ponto_coleta' no banco de dados.
Armazena informações dos pontos de coleta de resíduos com localização e inventário.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base


class PontoColeta(Base):
    """
    Modelo SQLAlchemy para a tabela de pontos de coleta.

    Contém localização (latitude/longitude), informações do ponto e inventário.
    """
    __tablename__ = "ponto_coleta"

    # Chave primária
    id = Column(Integer, primary_key=True, index=True)

    # Informações do ponto de coleta
    nome = Column(String(255), nullable=False)
    endereco = Column(String(500))

    # Coordenadas (GPS)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    # Raio de operação em metros (padrão: 1000m = 1km)
    raio_operacao = Column(Float, default=1000.0)

    # Inventário de resíduos (tipo_residuo -> quantidade)
    inventario = Column(JSON, default={})

    # Controle de criação e atualização
    data_criacao = Column(DateTime(timezone=True), server_default=func.now())
    data_atualizacao = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Status do ponto de coleta
    ativo = Column(Integer, default=1)  # 1 = ativo, 0 = inativo
