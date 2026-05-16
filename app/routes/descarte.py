from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.descarte import Descarte
from app.models.usuario import Usuario
from app.models.ponto_coleta import PontoColeta
from app.models.qrcode_token import QRCodeToken
from app.schemas.descarte import DescarteCreate, DescarteResponse, DescarteConfirmar
from app.services.validacao_service import validar_quantidade, validar_residuo
from app.services.localizacao_service import validar_localizacao
from app.services.pontuacao_service import calcular_pontos_proporcionais
from app.services.transferencia_service import transferir_residuo_para_ponto_coleta
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=DescarteResponse)
async def registrar_descarte(
    obj_in: DescarteCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """
    Registra um novo descarte de resíduo.
    
    RF014: Pontuação Proporcional - O usuário NOT ganha pontos imediatamente.
    O descarte entra com status='pendente'. Quando a cooperativa confirmar,
    o sistema calcula 10 pontos por cada 1kg real confirmado.
    
    RF010 + RN005: Validação de GPS (Geofencing)
    - Valida se o usuário está dentro de 1km do ponto de coleta
    
    RF013: Validação via QR Code (alternativa ao GPS)
    - Se qrcode_token for fornecido, valida presencialmente
    """
    # Validações básicas
    if not validar_quantidade(obj_in.quantidade):
        raise HTTPException(status_code=400, detail="Quantidade inválida. O valor deve estar entre 1 e 1000.")
    if not validar_residuo(obj_in.tipo_residuo):
        raise HTTPException(status_code=400, detail="Tipo de resíduo não aceito.")

    # Busca o usuário
    usuario_bd = db.query(Usuario).filter(Usuario.id == usuario.id).first()
    if not usuario_bd:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    # Busca o ponto de coleta
    ponto = db.query(PontoColeta).filter(PontoColeta.id == obj_in.ponto_coleta_id).first()
    if not ponto:
        raise HTTPException(status_code=404, detail="Ponto de coleta não encontrado.")

    # Validação de geofencing (RF010 + RN005)
    # Se não tiver QR Code, valida GPS
    validacao_qrcode = False
    if obj_in.qrcode_token:
        # Valida QR Code (RF013)
        qr_token = db.query(QRCodeToken).filter(
            QRCodeToken.token == obj_in.qrcode_token,
            QRCodeToken.ponto_coleta_id == obj_in.ponto_coleta_id,
            QRCodeToken.ativo == 1,
            QRCodeToken.data_expiracao > datetime.utcnow()
        ).first()
        if not qr_token:
            raise HTTPException(status_code=403, detail="Token QR Code inválido ou expirado.")
        validacao_qrcode = True
    else:
        # Valida GPS com Haversine
        if not validar_localizacao(
            obj_in.usuario_lat,
            obj_in.usuario_long,
            ponto.latitude,
            ponto.longitude,
            ponto.raio_operacao
        ):
            raise HTTPException(status_code=403, detail="Muito longe do ponto de coleta. Distância máxima: 1km.")

    # RF012: Transferência de inventário (ainda em status 'pendente')
    transferir_residuo_para_ponto_coleta(
        obj_in.tipo_residuo,
        obj_in.quantidade,
        obj_in.ponto_coleta_id,
        db
    )

    # RF014: Criar descarte com status 'pendente' (sem gerar pontos ainda)
    novo_descarte = Descarte(
        quantidade=obj_in.quantidade,
        tipo_residuo=obj_in.tipo_residuo,
        observacao=obj_in.observacao,
        status='pendente',  # Status inicial
        usuario_id=usuario_bd.id,
        usuario_lat=obj_in.usuario_lat,
        usuario_long=obj_in.usuario_long,
        ponto_lat=ponto.latitude,
        ponto_long=ponto.longitude,
        ponto_coleta_id=ponto.id,
        qrcode_token_id=qr_token.id if validacao_qrcode else None
    )
    db.add(novo_descarte)
    db.commit()
    db.refresh(novo_descarte)

    if validacao_qrcode:
        qr_token.descarte_id = novo_descarte.id
        qr_token.ativo = 0
        db.commit()
        db.refresh(qr_token)
    
    return novo_descarte

@router.get("/historico")
async def ver_historico(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return db.query(Descarte).filter(Descarte.usuario_id == usuario.id).all()

@router.get("/historico/geral")
async def ver_historico_geral(
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_role("admin")),
):
    return db.query(Descarte).order_by(Descarte.data_desc.desc()).all()

@router.get("/pendentes")
async def listar_descartes_pendentes(
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_role("admin")),
):
    """Lista todos os descartes com status 'pendente' para confirmação pela cooperativa."""
    return db.query(Descarte).filter(Descarte.status == 'pendente').all()

@router.put("/{id_descarte}/confirmar")
async def confirmar_descarte(
    id_descarte: int,
    obj_in: DescarteConfirmar,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_role("admin"))
):
    """
    Confirma o descarte e calcula pontos (RF014).
    
    Apenas administradores (cooperativa) podem confirmar.
    O sistema calcula 10 pontos por cada 1kg confirmado.
    """
    descarte = db.query(Descarte).filter(Descarte.id_descarte == id_descarte).first()
    if not descarte:
        raise HTTPException(status_code=404, detail="Descarte não encontrado.")
    if descarte.status == 'confirmado':
        raise HTTPException(status_code=400, detail="Descarte já foi confirmado.")

    # RF014: Calcula pontos proporcionais apenas após confirmação
    pontos = calcular_pontos_proporcionais(descarte.quantidade, obj_in.quantidade_confirmada)

    descarte.quantidade_confirmada = obj_in.quantidade_confirmada
    descarte.status = 'confirmado'

    usuario = db.query(Usuario).filter(Usuario.id == descarte.usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário do descarte não encontrado.")

    # Atualiza a pontuação do usuário
    usuario.pontuacao_total = (usuario.pontuacao_total or 0) + pontos

    db.commit()
    db.refresh(descarte)

    return {
        "mensagem": "Descarte confirmado com sucesso!",
        "id_descarte": descarte.id_descarte,
        "status": descarte.status,
        "quantidade_confirmada": descarte.quantidade_confirmada,
        "pontos_gerados": pontos,
        "pontuacao_total_usuario": usuario.pontuacao_total
    }
