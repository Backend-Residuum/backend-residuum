"""
Schemas de Pontuação

Define os modelos Pydantic para criação e manipulação de pontuações.
Usados na validação de dados de pontuação nas APIs.
"""

from pydantic import BaseModel

class PontuacaoCreate(BaseModel):
    """
    Modelo para criação de uma nova pontuação.

    Contém os pontos a serem atribuídos a um usuário.
    """
    pontos: int