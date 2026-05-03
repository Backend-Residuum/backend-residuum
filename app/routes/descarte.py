from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.descarte import Descarte
from app.models.usuario import Usuario
from app.schemas.descarte import DescarteCreate, DescarteResponse, DescarteConfirmar
from app.services.validacao_service import validar_quantidade, validar_residuo
from app.services.localizacao_service import validar_localizacao
from app.services.pontuacao_service import calcular_pontos_proporcionais

router = APIRouter()

@router.post("/", response_model=DescarteResponse)
async def registrar_descarte(obj_in: DescarteCreate, db: Session = Depends(get_db)):
    if not validar_quantidade(obj_in.quantidade):
        raise HTTPException(status_code=400, detail="Quantidade inválida.")
    if not validar_residuo(obj_in.tipo_residuo):
        raise HTTPException(status_code=400, detail="Apenas 'garrafa pet' é aceito.")
    if not validar_localizacao(obj_in.usuario_lat, obj_in.usuario_long, obj_in.ponto_lat, obj_in.ponto_long):
        raise HTTPException(status_code=403, detail="Muito longe do ponto de coleta.")

    novo_descarte = Descarte(
        quantidade=obj_in.quantidade,
        tipo_residuo=obj_in.tipo_residuo,
        observacao=obj_in.observacao,
        status='pendente',
        usuario_id=obj_in.usuario_id
    )
    db.add(novo_descarte)
    db.commit()
    db.refresh(novo_descarte)
    return novo_descarte

@router.get("/historico")
async def ver_historico(db: Session = Depends(get_db)):
    return db.query(Descarte).all()

@router.put("/{id_descarte}/confirmar")
async def confirmar_descarte(id_descarte: int, obj_in: DescarteConfirmar, db: Session = Depends(get_db)):
    descarte = db.query(Descarte).filter(Descarte.id_descarte == id_descarte).first()
    if not descarte:
        raise HTTPException(status_code=404, detail="Descarte não encontrado.")
    if descarte.status == 'confirmado':
        raise HTTPException(status_code=400, detail="Descarte já foi confirmado.")

    pontos = calcular_pontos_proporcionais(descarte.quantidade, obj_in.quantidade_confirmada)

    descarte.quantidade_confirmada = obj_in.quantidade_confirmada
    descarte.status = 'confirmado'

    usuario = db.query(Usuario).filter(Usuario.id == descarte.usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário do descarte não encontrado.")

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
