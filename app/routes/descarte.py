from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.descarte import Descarte
from app.models.usuario import Usuario
from app.schemas.descarte import DescarteCreate, DescarteResponse, DescarteConfirmar
from app.services.validacao_service import validar_quantidade, validar_residuo
from app.services.localizacao_service import validar_localizacao
from app.services.pontuacao_service import calcular_pontos_proporcionais
from app.services.transferencia_service import transferir_residuo_para_ponto_coleta # importação de transferencia de residuos 

router = APIRouter()

@router.post("/", response_model=DescarteResponse)
async def registrar_descarte(
    obj_in: DescarteCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    if not validar_quantidade(obj_in.quantidade):
        raise HTTPException(status_code=400, detail="Quantidade inválida. O valor deve estar entre 1 e 1000.")
    if not validar_residuo(obj_in.tipo_residuo):
        raise HTTPException(status_code=400, detail="Tipo de resíduo não aceito.")
    if not validar_localizacao(obj_in.usuario_lat, obj_in.usuario_long, obj_in.ponto_lat, obj_in.ponto_long):
        raise HTTPException(status_code=403, detail="Muito longe do ponto de coleta.")

    usuario = db.query(Usuario).filter(Usuario.id == obj_in.usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

# Lógica inicial de transferência parte do kaue
    transferir_residuo_para_ponto_coleta(
        obj_in.tipo_residuo,
        obj_in.quantidade
)


    novo_descarte = Descarte(
        quantidade=obj_in.quantidade,
        tipo_residuo=obj_in.tipo_residuo,
        observacao=obj_in.observacao,
        status='pendente',
        usuario_id=usuario.id,
        usuario_lat=obj_in.usuario_lat,
        usuario_long=obj_in.usuario_long, 
        ponto_lat=obj_in.ponto_lat,       
        ponto_long=obj_in.ponto_long      
    )
    db.add(novo_descarte)
    db.commit()
    db.refresh(novo_descarte)
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
