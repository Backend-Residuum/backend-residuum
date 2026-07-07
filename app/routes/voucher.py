"""Rotas publicas de consulta de vouchers."""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.decorators import public
from app.database import get_db
from app.models.voucher import Voucher
from app.schemas.voucher import VoucherResponse

router = APIRouter(prefix="/vouchers", tags=["Vouchers"])


@router.get("", response_model=list[VoucherResponse])
@public
def listar_vouchers(db: Session = Depends(get_db)):
    """Lista vouchers ativos e com quantidade disponivel."""
    agora = datetime.utcnow()
    return (
        db.query(Voucher)
        .filter(
            Voucher.status == "ativo",
            Voucher.quantidade_disponivel > 0,
            or_(Voucher.data_inicio.is_(None), Voucher.data_inicio <= agora),
            or_(Voucher.data_fim.is_(None), Voucher.data_fim >= agora),
        )
        .order_by(Voucher.criado_em.desc())
        .all()
    )
