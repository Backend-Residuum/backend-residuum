"""
Schemas de Endereço

Define os modelos Pydantic para criação e manipulação de endereços.
Usados na validação de dados de endereço nas APIs.
"""

from pydantic import BaseModel

class EnderecoCreate(BaseModel):
    """
    Modelo para criação de um novo endereço.

    Contém todos os campos necessários para registrar um endereço.
    """
    rua: str
    bairro: str
    numero: int
    cep: str
    cidade: str