"""
Schema Base de Respostas

Define o formato padrão das respostas da API.

Todas as respostas da aplicação devem seguir este padrão
para manter consistência entre endpoints.

Campos:
- success -> indica se a operação foi bem sucedida
- message -> mensagem explicativa da operação
- data -> dados retornados pela API
"""

from pydantic import BaseModel
from typing import Any, Optional


class BaseResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None