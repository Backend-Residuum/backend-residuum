"""
Rotas de Ponto de Coleta e QR Code Token

Gerencia os pontos de coleta e tokens para validação presencial via QR Code.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timedelta

from app.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.usuario import Usuario
from app.models.ponto_coleta import PontoColeta
from app.models.qrcode_token import QRCodeToken
from app.schemas.ponto_coleta import PontoColetaCreate, PontoColetaResponse, PontoColetaUpdate
from app.schemas.qrcode_token import QRCodeTokenCreate, QRCodeTokenResponse, QRCodeTokenValidate

router = APIRouter()


# ========================
# PONTO DE COLETA
# ========================

@router.post("/pontos-coleta", response_model=PontoColetaResponse, tags=["Ponto de Coleta"])
async def criar_ponto_coleta(
    obj_in: PontoColetaCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_role("admin"))
):
    """Cria um novo ponto de coleta (apenas admin)."""
    novo_ponto = PontoColeta(
        nome=obj_in.nome,
        endereco=obj_in.endereco,
        latitude=obj_in.latitude,
        longitude=obj_in.longitude,
        raio_operacao=obj_in.raio_operacao or 1000.0,
        inventario={}
    )
    db.add(novo_ponto)
    db.commit()
    db.refresh(novo_ponto)
    return novo_ponto


@router.get("/pontos-coleta/{ponto_id}", response_model=PontoColetaResponse, tags=["Ponto de Coleta"])
async def obter_ponto_coleta(
    ponto_id: int,
    db: Session = Depends(get_db),
):
    """Obtém os detalhes de um ponto de coleta."""
    ponto = db.query(PontoColeta).filter(PontoColeta.id == ponto_id).first()
    if not ponto:
        raise HTTPException(status_code=404, detail="Ponto de coleta não encontrado.")
    return ponto


@router.get("/pontos-coleta", tags=["Ponto de Coleta"])
async def listar_pontos_coleta(
    db: Session = Depends(get_db),
):
    """Lista todos os pontos de coleta ativos."""
    return db.query(PontoColeta).filter(PontoColeta.ativo == 1).all()


@router.put("/pontos-coleta/{ponto_id}", response_model=PontoColetaResponse, tags=["Ponto de Coleta"])
async def atualizar_ponto_coleta(
    ponto_id: int,
    obj_in: PontoColetaUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_role("admin"))
):
    """Atualiza um ponto de coleta (apenas admin)."""
    ponto = db.query(PontoColeta).filter(PontoColeta.id == ponto_id).first()
    if not ponto:
        raise HTTPException(status_code=404, detail="Ponto de coleta não encontrado.")
    
    if obj_in.nome:
        ponto.nome = obj_in.nome
    if obj_in.endereco:
        ponto.endereco = obj_in.endereco
    if obj_in.latitude:
        ponto.latitude = obj_in.latitude
    if obj_in.longitude:
        ponto.longitude = obj_in.longitude
    if obj_in.raio_operacao:
        ponto.raio_operacao = obj_in.raio_operacao
    if obj_in.ativo is not None:
        ponto.ativo = obj_in.ativo
    
    db.commit()
    db.refresh(ponto)
    return ponto


# ========================
# QR CODE TOKEN (RF013)
# ========================

@router.post("/qrcode-tokens", response_model=QRCodeTokenResponse, tags=["QR Code"])
async def gerar_qrcode_token(
    obj_in: QRCodeTokenCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_role("admin"))
):
    """
    Gera um novo token QR Code para um ponto de coleta.
    
    RF013: Validação Alternativa via QR Code
    O ponto de coleta gera um código/token único (UUID).
    """
    # Verifica se o ponto existe
    ponto = db.query(PontoColeta).filter(PontoColeta.id == obj_in.ponto_coleta_id).first()
    if not ponto:
        raise HTTPException(status_code=404, detail="Ponto de coleta não encontrado.")
    
    # Gera um UUID único
    token_uuid = str(uuid.uuid4())
    
    # Token válido por 1 hora
    data_expiracao = datetime.utcnow() + timedelta(hours=1)
    
    novo_token = QRCodeToken(
        token=token_uuid,
        ponto_coleta_id=obj_in.ponto_coleta_id,
        data_expiracao=data_expiracao,
        ativo=1
    )
    db.add(novo_token)
    db.commit()
    db.refresh(novo_token)
    
    return novo_token


@router.get("/qrcode-tokens/{ponto_id}", tags=["QR Code"])
async def listar_tokens_ativos(
    ponto_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_role("admin"))
):
    """Lista todos os tokens ativos de um ponto de coleta."""
    tokens = db.query(QRCodeToken).filter(
        QRCodeToken.ponto_coleta_id == ponto_id,
        QRCodeToken.ativo == 1,
        QRCodeToken.data_expiracao > datetime.utcnow()
    ).all()
    return tokens


@router.post("/qrcode-tokens/validar", tags=["QR Code"])
async def validar_qrcode_token(
    obj_in: QRCodeTokenValidate,
    db: Session = Depends(get_db)
):
    """
    Valida um token QR Code.
    
    Usado antes de fazer o descarte para confirmar que o usuário está presencialmente
    no ponto de coleta.
    """
    token = db.query(QRCodeToken).filter(
        QRCodeToken.token == obj_in.token,
        QRCodeToken.ativo == 1,
        QRCodeToken.data_expiracao > datetime.utcnow()
    ).first()
    
    if not token:
        raise HTTPException(status_code=403, detail="Token inválido ou expirado.")
    
    # Retorna os dados do ponto de coleta
    ponto = db.query(PontoColeta).filter(PontoColeta.id == token.ponto_coleta_id).first()
    
    return {
        "valido": True,
        "ponto_coleta_id": token.ponto_coleta_id,
        "ponto_nome": ponto.nome if ponto else "Desconhecido",
        "token": token.token
    }
