"""
Rotas de Autenticação

Este módulo define as rotas para autenticação: cadastro de usuários, login e perfil do usuário logado.
Usa hashing de senha com bcrypt e JWT para tokens.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.database import get_db
from app.models.usuario import Usuario
from app.models.endereco import Endereco
from app.schemas.usuario import UsuarioCreate
from app.schemas.auth import LoginRequest, TokenResponse
from app.core.security import criar_token
from app.dependencies.auth import get_current_user

# Roteador para agrupar as rotas de autenticação
router = APIRouter(tags=["Auth"])

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
@router.post("/usuarios")
def criar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    """
    Cria um novo usuário no sistema.

    Verifica se o email já existe, cria o endereço e o usuário,
    e salva no banco de dados.
    """
    # Verifica se o email já está cadastrado
    usuario_existente = db.query(Usuario).filter(Usuario.email == usuario.email).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    # Cria o endereço associado ao usuário
    novo_endereco = Endereco(**usuario.endereco.dict())
    db.add(novo_endereco)
    db.commit()
    db.refresh(novo_endereco)

    # Cria o usuário com senha hasheada
    novo_usuario = Usuario(
        nome=usuario.nome,
        email=usuario.email,
        telefone=usuario.telefone,
        senha_hash=hash_senha(usuario.senha),
        endereco_id=novo_endereco.id_end,
        pontuacao_total=0
    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    return {"msg": "Usuário criado com sucesso"}

# ========================
# LOGIN
# ========================
@router.post("/login", response_model=TokenResponse)
def login(dados: LoginRequest = Body(...), db: Session = Depends(get_db)):
    """
    Realiza o login do usuário.

    Verifica email e senha, e retorna um token JWT se válido.
    """
    # Busca o usuário pelo email
    usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos"
        )

    # Verifica a senha
    if not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos"
        )

    # Gera o token JWT
    token = criar_token({
        "sub": str(usuario.id),
        "email": usuario.email
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }

# ========================
# PERFIL DO USUÁRIO LOGADO
# ========================
@router.get("/me")
def get_me(usuario: Usuario = Depends(get_current_user)):
    """
    Retorna os dados básicos do usuário autenticado.

    Requer token válido no cabeçalho Authorization.
    """
    return {
        "id": usuario.id,
        "nome": usuario.nome,
        "email": usuario.email,
        "pontuacao_total": usuario.pontuacao_total
    }