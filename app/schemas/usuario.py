"""
Schemas de Usuário

Define os modelos Pydantic para criação e manipulação de usuários.
"""

from pydantic import BaseModel, EmailStr, Field

class UsuarioCreate(BaseModel):
    """Modelo para criação de um novo usuário.
        Field para criar tamanho mínimo
        Falta criar um sistema que peça para o usuário digitar o mínimo na hora do erro
    """

    nome: str = Field(min_length=1)
    email: EmailStr
    telefone: str = Field(min_length=1)
    senha: str = Field(min_length=6)
