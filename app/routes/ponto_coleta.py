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

from typing import Optional, List, Dict, Any
from app.services.localizacao_service import calcular_distancia_haversine


STATUS_VALIDOS = {"ativo", "cheio", "inativo"}


def _normalizar_tipos(tipos: Optional[List[str]]) -> List[str]:
    if not tipos:
        return []
    return [str(tipo).strip().lower() for tipo in tipos if str(tipo).strip()]


def _total_inventario(inventario: Optional[Dict[str, Any]]) -> float:
    if not inventario:
        return 0.0
    total = 0.0
    for valor in inventario.values():
        try:
            total += float(valor or 0)
        except (TypeError, ValueError):
            continue
    return total


def _status_calculado(ponto: PontoColeta) -> str:
    if ponto.ativo == 0 or ponto.status == "inativo":
        return "inativo"

    total = _total_inventario(ponto.inventario)
    if ponto.capacidade_maxima and ponto.capacidade_maxima > 0 and total >= float(ponto.capacidade_maxima):
        return "cheio"

    return ponto.status or "ativo"


def _serializar_ponto(ponto: PontoColeta, distancia_km: Optional[float] = None) -> Dict[str, Any]:
    total = _total_inventario(ponto.inventario)
    percentual = None
    if ponto.capacidade_maxima and ponto.capacidade_maxima > 0:
        percentual = round((total / float(ponto.capacidade_maxima)) * 100, 2)

    return {
        "id": ponto.id,
        "nome": ponto.nome,
        "endereco": ponto.endereco,
        "latitude": ponto.latitude,
        "longitude": ponto.longitude,
        "raio_operacao": ponto.raio_operacao or 1000.0,
        "capacidade_maxima": ponto.capacidade_maxima,
        "tipos_residuos_aceitos": ponto.tipos_residuos_aceitos or [],
        "horario_funcionamento": ponto.horario_funcionamento,
        "status": ponto.status or "ativo",
        "status_calculado": _status_calculado(ponto),
        "inventario": ponto.inventario or {},
        "total_inventario": round(total, 3),
        "percentual_ocupacao": percentual,
        "distancia_km": round(distancia_km, 3) if distancia_km is not None else None,
        "ativo": ponto.ativo,
        "data_criacao": ponto.data_criacao,
        "data_atualizacao": ponto.data_atualizacao,
    }


@router.post("/pontos-coleta", response_model=PontoColetaResponse, tags=["Ponto de Coleta"])
async def criar_ponto_coleta(
    obj_in: PontoColetaCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_role("admin"))
):
    """Cria um novo ponto de coleta (apenas admin)."""
    status = (obj_in.status or "ativo").lower()
    if status not in STATUS_VALIDOS:
        raise HTTPException(status_code=400, detail="Status inválido. Use: ativo, cheio ou inativo.")

    novo_ponto = PontoColeta(
        nome=obj_in.nome,
        endereco=obj_in.endereco,
        latitude=obj_in.latitude,
        longitude=obj_in.longitude,
        raio_operacao=obj_in.raio_operacao or 1000.0,
        capacidade_maxima=obj_in.capacidade_maxima,
        tipos_residuos_aceitos=_normalizar_tipos(obj_in.tipos_residuos_aceitos),
        horario_funcionamento=obj_in.horario_funcionamento,
        status=status,
        ativo=0 if status == "inativo" else 1,
        inventario={}
    )
    db.add(novo_ponto)
    db.commit()
    db.refresh(novo_ponto)
    return _serializar_ponto(novo_ponto)


@router.get("/pontos-coleta/{ponto_id}", response_model=PontoColetaResponse, tags=["Ponto de Coleta"])
async def obter_ponto_coleta(
    ponto_id: int,
    db: Session = Depends(get_db),
):
    """Obtém os detalhes de um ponto de coleta."""
    ponto = db.query(PontoColeta).filter(PontoColeta.id == ponto_id).first()
    if not ponto:
        raise HTTPException(status_code=404, detail="Ponto de coleta não encontrado.")
    return _serializar_ponto(ponto)


@router.get("/pontos-coleta", tags=["Ponto de Coleta"])
async def listar_pontos_coleta(
    tipo_residuo: Optional[str] = None,
    lat: Optional[float] = None,
    long: Optional[float] = None,
    distancia_km: Optional[float] = None,
    incluir_inativos: bool = False,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
):
    """
    Lista pontos de coleta.

    Task 9 / RF007-RF009:
    - Permite filtrar por tipo de resíduo aceito.
    - Permite filtrar por distância a partir da latitude/longitude do usuário.
    - Retorna distância calculada quando lat/long são informados.
    """
    # Usuários comuns só enxergam pontos disponíveis.
    # Admin pode solicitar incluir_inativos=true para editar/reativar pontos pausados.
    if incluir_inativos and usuario_atual.role != "admin":
        incluir_inativos = False

    query = db.query(PontoColeta)
    if not incluir_inativos:
        query = query.filter(PontoColeta.ativo == 1)

    pontos = query.all()
    tipo_normalizado = tipo_residuo.strip().lower() if tipo_residuo else None
    resultado = []

    for ponto in pontos:
        tipos_aceitos = _normalizar_tipos(ponto.tipos_residuos_aceitos)
        if tipo_normalizado and tipo_normalizado not in tipos_aceitos:
            continue

        distancia_calculada_km = None
        if lat is not None and long is not None:
            distancia_metros = calcular_distancia_haversine(lat, long, ponto.latitude, ponto.longitude)
            distancia_calculada_km = distancia_metros / 1000
            if distancia_km is not None and distancia_calculada_km > distancia_km:
                continue

        resultado.append(_serializar_ponto(ponto, distancia_calculada_km))

    if lat is not None and long is not None:
        resultado.sort(key=lambda item: item["distancia_km"] if item["distancia_km"] is not None else 999999)

    return resultado


@router.get("/pontos", tags=["Ponto de Coleta"])
async def listar_pontos_alias(
    tipo_residuo: Optional[str] = None,
    lat: Optional[float] = None,
    long: Optional[float] = None,
    distancia_km: Optional[float] = None,
    incluir_inativos: bool = False,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
):
    """Alias compatível com a task GET /pontos."""
    return await listar_pontos_coleta(
        tipo_residuo=tipo_residuo,
        lat=lat,
        long=long,
        distancia_km=distancia_km,
        incluir_inativos=incluir_inativos,
        db=db,
        usuario_atual=usuario_atual,
    )


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

    if obj_in.nome is not None:
        ponto.nome = obj_in.nome
    if obj_in.endereco is not None:
        ponto.endereco = obj_in.endereco
    if obj_in.latitude is not None:
        ponto.latitude = obj_in.latitude
    if obj_in.longitude is not None:
        ponto.longitude = obj_in.longitude
    if obj_in.raio_operacao is not None:
        ponto.raio_operacao = obj_in.raio_operacao
    if obj_in.capacidade_maxima is not None:
        ponto.capacidade_maxima = obj_in.capacidade_maxima
    if obj_in.tipos_residuos_aceitos is not None:
        ponto.tipos_residuos_aceitos = _normalizar_tipos(obj_in.tipos_residuos_aceitos)
    if obj_in.horario_funcionamento is not None:
        ponto.horario_funcionamento = obj_in.horario_funcionamento
    if obj_in.status is not None:
        status = obj_in.status.lower()
        if status not in STATUS_VALIDOS:
            raise HTTPException(status_code=400, detail="Status inválido. Use: ativo, cheio ou inativo.")
        ponto.status = status
        ponto.ativo = 0 if status == "inativo" else 1
    if obj_in.ativo is not None:
        ponto.ativo = obj_in.ativo
        if obj_in.ativo == 0:
            ponto.status = "inativo"
        elif ponto.status == "inativo":
            ponto.status = "ativo"

    db.commit()
    db.refresh(ponto)
    return _serializar_ponto(ponto)


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
