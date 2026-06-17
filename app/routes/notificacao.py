from fastapi import APIRouter, Depends, HTTPException,Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.notificacao import Notificacao
from app.models.usuario import Usuario
from app.dependencies.auth import require_role
from typing import Optional

# Criamos o roteador com o prefixo padrão
router = APIRouter(prefix="/notificacoes", tags=["Notificações"])

@router.get("/")
def listar_notificacoes_nao_lidas(
    ponto_id: Optional[int] = Query(None, description="Filtrar por ID do Ponto de Coleta"), # <-- Novo parâmetro
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_role("admin"))
):
    query = db.query(Notificacao).filter(Notificacao.lida == False)
    if ponto_id:
        query = query.filter(Notificacao.ponto_coleta_id == ponto_id)
        
    return query.order_by(Notificacao.criado_em.desc()).all()

@router.patch("/{notificacao_id}/lida")
def marcar_como_lida(
    notificacao_id: int, 
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_role("admin"))
):
    """
    Marca um alerta como lido para que ele suma do painel.
    """
    notificacao = db.query(Notificacao).filter(Notificacao.id == notificacao_id).first()
    
    if not notificacao:
        raise HTTPException(status_code=404, detail="Notificação não encontrada.")
        
    notificacao.lida = True
    db.commit()
    
    return {"status": "Notificação marcada como lida"}