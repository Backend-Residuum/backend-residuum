"""Rotas publicas de consulta de sorteios."""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.decorators import public
from app.core.exceptions import raise_not_found
from app.database import get_db
from app.models.sorteio import Sorteio
from app.schemas.sorteio import SorteioResponse

router = APIRouter(prefix="/sorteios", tags=["Sorteios"])


def _filtrar_ativos(query):
    agora = datetime.utcnow()
    return query.filter(
        Sorteio.status == "ativo",
        or_(Sorteio.data_inicio.is_(None), Sorteio.data_inicio <= agora),
        or_(Sorteio.data_fim.is_(None), Sorteio.data_fim >= agora),
    )


@router.get("", response_model=list[SorteioResponse])
@public
def listar_sorteios(db: Session = Depends(get_db)):
    """Lista sorteios ativos por padrao."""
    return _filtrar_ativos(db.query(Sorteio)).order_by(Sorteio.criado_em.desc()).all()


@router.get("/{sorteio_id}", response_model=SorteioResponse)
@public
def obter_sorteio(sorteio_id: int, db: Session = Depends(get_db)):
    """Retorna o detalhe de um sorteio."""
    sorteio = db.query(Sorteio).filter(Sorteio.id == sorteio_id).first()
    if not sorteio:
        raise_not_found("Sorteio nao encontrado.")

    return sorteio
