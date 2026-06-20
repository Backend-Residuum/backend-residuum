"""
Rotas de Endereço

Gerencia o endereço do usuário autenticado.
O id do usuário é sempre obtido do token, nunca de path/body.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.base import BaseResponse
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.endereco import Endereco
from app.models.usuario import Usuario
from app.schemas.endereco import EnderecoCreate

router = APIRouter()

@router.put("/me/endereco", response_model=BaseResponse)
def cadastrar_endereco(
    endereco: EnderecoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user)
):
    """
    Cadastra ou atualiza endereço do usuário autenticado.
    """

    # Verifica se usuário já possui endereço
    endereco_existente = db.query(Endereco).filter(
        Endereco.usuario_id == usuario.id
    ).first()

    # Atualiza endereço existente
    if endereco_existente:

        endereco_existente.rua = endereco.rua
        endereco_existente.numero = endereco.numero
        endereco_existente.bairro = endereco.bairro
        endereco_existente.cep = endereco.cep
        endereco_existente.cidade = endereco.cidade

        db.commit()
        db.refresh(endereco_existente)

        return BaseResponse(
            success=True,
            message="Endereço atualizado com sucesso",
            data={
                "id_end": endereco_existente.id_end,
                "rua": endereco_existente.rua,
                "numero": endereco_existente.numero,
                "bairro": endereco_existente.bairro,
                "cep": endereco_existente.cep,
                "cidade": endereco_existente.cidade
            }
        )

    # Cria novo endereço
    novo_endereco = Endereco(
        usuario_id=usuario.id,
        rua=endereco.rua,
        numero=endereco.numero,
        bairro=endereco.bairro,
        cep=endereco.cep,
        cidade=endereco.cidade
    )

    # Salva no banco
    db.add(novo_endereco)
    db.commit()
    db.refresh(novo_endereco)

    # Retorna resposta padronizada
    return BaseResponse(
        success=True,
        message="Endereço cadastrado com sucesso",
        data={
            "id_end": novo_endereco.id_end,
            "rua": novo_endereco.rua,
            "numero": novo_endereco.numero,
            "bairro": novo_endereco.bairro,
            "cep": novo_endereco.cep,
            "cidade": novo_endereco.cidade
        }
    )