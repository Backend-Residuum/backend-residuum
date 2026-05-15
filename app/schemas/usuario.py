"""
Schemas de Usuário

Define os modelos Pydantic para criação e manipulação de usuários.
"""

from pydantic import BaseModel


class UsuarioCreate(BaseModel):
    """Modelo para criação de um novo usuário."""

    nome: str
    email: str
    telefone: str
    senha: str
