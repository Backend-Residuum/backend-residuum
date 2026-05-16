"""
Serviço de Transferência de Inventário

RF012: Motor de Transferência de Inventário
Implementa a lógica de transferência de resíduos para o ponto de coleta
e atualização do inventário no banco de dados.
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.ponto_coleta import PontoColeta
from fastapi import HTTPException
import json


def transferir_residuo_para_ponto_coleta(
    tipo_residuo: str,
    quantidade: float,
    ponto_coleta_id: int,
    db: Session
) -> dict:
    """
    Transfere a quantidade de resíduos registrada para o inventário do ponto de coleta.
    
    RF012: Motor de Transferência de Inventário
    - Verifica se o ponto de coleta existe
    - Registra a entrada da quantidade de resíduos no inventário
    - Atualiza o campo inventario (JSON) do ponto de coleta
    
    Args:
        tipo_residuo: Tipo de resíduo (ex: "garrafa pet")
        quantidade: Quantidade em kg
        ponto_coleta_id: ID do ponto de coleta
        db: Sessão do banco de dados
    
    Returns:
        Dicionário com status da transferência
    
    Raises:
        HTTPException: Se o ponto de coleta não existir
    """
    # Validações
    if not tipo_residuo or quantidade <= 0:
        raise HTTPException(status_code=400, detail="Tipo de resíduo ou quantidade inválida.")
    
    # Busca o ponto de coleta
    ponto = db.query(PontoColeta).filter(PontoColeta.id == ponto_coleta_id).first()
    
    if not ponto:
        raise HTTPException(status_code=404, detail="Ponto de coleta não encontrado.")
    
    # Atualiza o inventário (JSON)
    inventario = ponto.inventario if ponto.inventario else {}
    
    # Se for dict, converte para dict se for string JSON
    if isinstance(inventario, str):
        try:
            inventario = json.loads(inventario)
        except:
            inventario = {}
    
    # Soma à quantidade existente
    if tipo_residuo in inventario:
        inventario[tipo_residuo] += quantidade
    else:
        inventario[tipo_residuo] = quantidade
    
    # Atualiza o ponto
    ponto.inventario = inventario
    db.commit()
    
    return {
        "tipo_residuo": tipo_residuo,
        "quantidade_transferida": quantidade,
        "novo_estoque": inventario.get(tipo_residuo, 0),
        "ponto_coleta_id": ponto_coleta_id,
        "status": "transferencia_registrada"
    }

