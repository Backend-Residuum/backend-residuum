"""
Modelo de Usuário

Define a estrutura da tabela 'usuario' no banco de dados.
Representa um usuário do sistema com informações pessoais e autenticação.
"""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Usuario(Base):
    """
    Modelo SQLAlchemy para a tabela de usuários.

    Contém dados pessoais, credenciais e relacionamento com endereço.
    """
    __tablename__ = "usuario"

    # Chave primária
    id = Column(Integer, primary_key=True, index=True)

    # Dados pessoais
    nome = Column(String)
    email = Column(String, unique=True)  # Email único para login
    telefone = Column(String)

    # Credenciais de segurança
    senha_hash = Column(String)  # Senha hasheada com bcrypt

    # Pontuação acumulada do usuário
    pontuacao_total = Column(Integer, default=0)

    role = Column(String, nullable=False, default="usuario", server_default="usuario")

    # Relacionamento com endereço
    endereco_id = Column(Integer, ForeignKey("endereco.id_end"))
    endereco = relationship("Endereco")