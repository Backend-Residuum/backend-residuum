"""
Schemas de Usuário

Define os modelos Pydantic para criação e manipulação de usuários.
Inclui dados pessoais e endereço para cadastro completo.
"""

from pydantic import BaseModel

class EnderecoCreate(BaseModel):
    """
    Modelo para criação de endereço (duplicado para evitar import circular).

    Contém os campos necessários para registrar um endereço junto ao usuário.
    """
    rua: str
    bairro: str
    numero: int
    cep: str
    cidade: str

class UsuarioCreate(BaseModel):
    """
    Modelo para criação de um novo usuário.

    Inclui dados pessoais, credenciais e endereço completo.
    """
    nome: str
    email: str
    telefone: str
    senha: str
    endereco: EnderecoCreate