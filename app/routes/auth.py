"""
Rotas de Autenticação

Este módulo define as rotas para autenticação: cadastro de usuários, login e perfil do usuário logado.
Usa hashing de senha com bcrypt e JWT para tokens.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from app.schemas.base import BaseResponse
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.database import get_db
from app.models.usuario import Usuario
from app.models.endereco import Endereco
from app.schemas.usuario import UsuarioCreate
from app.schemas.auth import LoginRequest

from app.core.security import criar_token
from app.core.decorators import public
from app.dependencies.auth import get_current_user

# Roteador para agrupar as rotas de autenticação
router = APIRouter()

# Contexto para hashing de senhas usando bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_senha(senha: str):
    """
    Gera um hash seguro para a senha usando bcrypt.
    Limita a senha a 72 caracteres para compatibilidade.
    """
    return pwd_context.hash(senha[:72])

def verificar_senha(senha: str, hash: str):
    """
    Verifica se a senha corresponde ao hash armazenado.
    """
    return pwd_context.verify(senha[:72], hash)

# ========================
# CADASTRO DE USUÁRIO
# ========================
@router.post("/usuarios", response_model=BaseResponse)
@public
def criar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    """
    Cria um novo usuário no sistema apenas com credenciais e dados pessoais.

    O endereço é cadastrado posteriormente via PUT /me/endereco.
    """

    # Busca usuário pelo email
    usuario_existente = db.query(Usuario).filter(
        Usuario.email == usuario.email
    ).first()

    # Verifica se já existe usuário com o email informado
    if usuario_existente:
      raise HTTPException(
        status_code=400,
        detail={
            "success": False,
            "message": "Email já cadastrado",
            "data": None
        }
    )

    # Cria novo usuário
    novo_usuario = Usuario(
        nome=usuario.nome,
        email=usuario.email,
        telefone=usuario.telefone,
        senha_hash=hash_senha(usuario.senha),
        pontuacao_total=0,
    )

    # Salva no banco
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    # Retorna resposta padronizada
    return BaseResponse(
        success=True,
        message="Usuário criado com sucesso",
        data={
            "id": novo_usuario.id,
            "nome": novo_usuario.nome,
            "email": novo_usuario.email,
            "telefone": novo_usuario.telefone
        }
    )

@router.post("/login", response_model=BaseResponse)
@public
def login(dados: LoginRequest = Body(...), db: Session = Depends(get_db)):
    """
    Realiza o login do usuário.

    Verifica email e senha, e retorna um token JWT se válido.
    """

    # Busca o usuário pelo email
    usuario = db.query(Usuario).filter(
        Usuario.email == dados.email
    ).first()

    # Verifica se o usuário existe
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "message": "Email ou senha inválidos",
                "data": None
            }
        )

    # Verifica se a senha está correta
    if not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "message": "Email ou senha inválidos",
                "data": None
            }
        )

    # Gera o token JWT
    token = criar_token({
        "sub": str(usuario.id),
        "email": usuario.email
    })

    # Retorna token padronizado
    return BaseResponse(
        success=True,
        message="Login realizado com sucesso",
        data={
            "access_token": token,
            "token_type": "bearer"
        }
    )

# ========================
# PERFIL DO USUÁRIO LOGADO
# ========================
@router.get("/me", response_model=BaseResponse)
def get_me(usuario: Usuario = Depends(get_current_user)):
    """
    Retorna os dados básicos do usuário autenticado.

    Requer token válido no cabeçalho Authorization.
    """
    endereco = None
    if usuario.endereco is not None:
        endereco = {
            "id_end": usuario.endereco.id_end,
            "rua": usuario.endereco.rua,
            "bairro": usuario.endereco.bairro,
            "numero": usuario.endereco.numero,
            "cep": usuario.endereco.cep,
            "cidade": usuario.endereco.cidade,
        }

    # Retorna os dados do usuário autenticado
    # Retorna os dados do usuário autenticado
    return BaseResponse(
        success=True,
        message="Dados do usuário retornados com sucesso",
        data={
            "id": usuario.id,
            "nome": usuario.nome,
            "email": usuario.email,
            "telefone": usuario.telefone,
            "pontuacao_total": usuario.pontuacao_total,
            "role": usuario.role,
            "endereco": endereco,
        }
    )