"""
Rotas de Resíduo

Responsável pelo gerenciamento do estoque de resíduos recicláveis.

Permite:
- cadastrar novos resíduos
- atualizar quantidade em estoque
- consultar resíduos cadastrados

O sistema utiliza o código de barras para identificar resíduos já existentes.
Caso o código já esteja cadastrado, a quantidade é somada automaticamente
ao estoque existente, evitando duplicidade de registros.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.residuo import Residuo
from app.schemas.residuo import ResiduoCreate, ResiduoResponse

router = APIRouter()


@router.post("/", response_model=ResiduoResponse)
async def adicionar_residuo(
    obj_in: ResiduoCreate,
    db: Session = Depends(get_db),
):

    existente = db.query(Residuo).filter(
        Residuo.codigo_barras == obj_in.codigo_barras
    ).first()

    if existente:

        existente.quantidade += obj_in.quantidade

        db.commit()
        db.refresh(existente)

        return existente

    novo = Residuo(
        nome=obj_in.nome,
        codigo_barras=obj_in.codigo_barras,
        quantidade=obj_in.quantidade
    )

    db.add(novo)

    db.commit()

    db.refresh(novo)

    return novo