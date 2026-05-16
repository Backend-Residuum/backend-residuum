"""
Schemas de Autenticação

Define os modelos Pydantic para requisições e respostas de autenticação.
Usados para validação e serialização de dados nas rotas de auth.
"""

from pydantic import BaseModel

class LoginRequest(BaseModel):
    """
    Modelo para requisição de login.

    Contém as credenciais necessárias para autenticação.
    """
    email: str
    senha: str

class TokenResponse(BaseModel):
    """
    Modelo para resposta de login bem-sucedido.

    Retorna o token de acesso, seu tipo e informações do usuário.
    """
    access_token: str
    token_type: str
    usuario_id: int = None