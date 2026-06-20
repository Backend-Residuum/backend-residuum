from fastapi import APIRouter, HTTPException, Depends
from app.schemas.base import BaseResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.descarte import Descarte
from app.models.usuario import Usuario
from app.schemas.descarte import DescarteCreate, DescarteResponse, DescarteConfirmar
from app.services.validacao_service import validar_quantidade, validar_residuo
from app.services.localizacao_service import validar_localizacao
from app.services.pontuacao_service import calcular_pontos_proporcionais

router = APIRouter()

@router.post("/", response_model=BaseResponse)
def registrar_descarte(
    descarte: DescarteCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user)
):
    """
    Registra um descarte de resíduos.

    O usuário autenticado:
    - Ganha pontuação
    - Tem descarte registrado
    """

    # Cria novo descarte
    novo_descarte = Descarte(
        usuario_id=usuario.id,
        residuo_id=descarte.residuo_id,
        quantidade=descarte.quantidade,
        pontos_ganhos=descarte.quantidade * 10
    )

    # Atualiza pontuação do usuário
    usuario.pontuacao_total += novo_descarte.pontos_ganhos

    # Salva no banco
    db.add(novo_descarte)
    db.commit()
    db.refresh(novo_descarte)

    # Retorna resposta padronizada
    return BaseResponse(
        success=True,
        message="Descarte registrado com sucesso",
        data={
            "id": novo_descarte.id,
            "usuario_id": usuario.id,
            "residuo_id": novo_descarte.residuo_id,
            "quantidade": novo_descarte.quantidade,
            "pontos_ganhos": novo_descarte.pontos_ganhos
        }
    )