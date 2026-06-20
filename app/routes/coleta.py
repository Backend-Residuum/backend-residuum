from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db

from app.models.coleta import Coleta
from app.models.descarte import Descarte

from app.schemas.coleta import (
    ColetaCreate,
    ColetaResponse
)

router = APIRouter(
    prefix="/coletas",
    tags=["Coletas"]
)


@router.post("/", response_model=ColetaResponse)
def registrar_coleta(
    dados: ColetaCreate,
    db: Session = Depends(get_db)
):

    descarte = (
        db.query(Descarte)
        .filter(
            Descarte.id_descarte == dados.descarte_id
        )
        .first()
    )

    if not descarte:
        raise HTTPException(
            status_code=404,
            detail="Descarte não encontrado"
        )

    coleta = Coleta(
        descarte_id=dados.descarte_id,
        peso_real=dados.peso_real,
        responsavel=dados.responsavel,
        observacao=dados.observacao
    )

    descarte.status = "coletado"
    descarte.quantidade_confirmada = dados.peso_real

    db.add(coleta)
    db.commit()
    db.refresh(coleta)

    return coleta