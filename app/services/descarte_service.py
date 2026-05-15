from sqlalchemy.orm import Session
from app.models.descarte import Descarte
from app.models.estoque import Estoque
from app.schemas.descarte import DescarteCreate, DescarteConfirmar

def registrar_novo_descarte(db: Session, descarte_data: DescarteCreate):
    novo_descarte = Descarte(**descarte_data.model_dump())
    db.add(novo_descarte)
    db.commit()
    db.refresh(novo_descarte)
    return novo_descarte

def confirmar_e_atualizar_estoque(db: Session, descarte_id: int, dados: DescarteConfirmar):
    # Busca o descarte
    descarte = db.query(Descarte).filter(Descarte.id_descarte == descarte_id).first()
    if not descarte:
        return None

    # Atualiza o status e a quantidade confirmada
    descarte.quantidade_confirmada = dados.quantidade_confirmada
    descarte.status = "concluido"

    # Atualiza ou Cria o registro no Estoque
    estoque_item = db.query(Estoque).filter(Estoque.tipo_residuo == descarte.tipo_residuo).first()
    
    if estoque_item:
        estoque_item.quantidade_total += dados.quantidade_confirmada
    else:
        novo_estoque = Estoque(
            tipo_residuo=descarte.tipo_residuo,
            quantidade_total=dados.quantidade_confirmada
        )
        db.add(novo_estoque)

    db.commit()
    db.refresh(descarte)
    return descarte