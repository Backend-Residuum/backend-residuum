"""
Rotas Administrativas

Endpoints restritos a usuários com role=admin. Centralizam gestão de
usuários, descartes e métricas agregadas do sistema.

Todas as rotas deste módulo exigem JWT válido + role=admin
(via dependência global `require_role("admin")`).
"""

import csv
import io
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_role
from app.models.audit_log import AuditLog
from app.models.descarte import Descarte
from app.models.inventario_usuario import InventarioUsuario
from app.models.ponto_coleta import PontoColeta
from app.models.pontuacao import Pontuacao
from app.models.usuario import Usuario
from app.schemas.admin import (
    AjustePontuacaoRequest,
    RejeitarDescarteRequest,
    ReverterDescarteRequest,
    UpdateRoleRequest,
    UsuarioAdminUpdate,
)
from app.services.audit_service import registrar_acao
from app.services.serializacao_service import (
    serializar_descarte,
    serializar_usuario_basico,
)
from app.services.transferencia_service import debitar_residuo_do_ponto_coleta


router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_role("admin"))],
)


# ============================================================
# USUÁRIOS
# ============================================================
@router.get("/usuarios")
def listar_usuarios(
    db: Session = Depends(get_db),
    role: Optional[str] = Query(None, description="Filtrar por role"),
    email: Optional[str] = Query(None, description="Busca parcial por email"),
    nome: Optional[str] = Query(None, description="Busca parcial por nome"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Lista paginada de usuários com filtros opcionais."""
    query = db.query(Usuario)

    if role:
        query = query.filter(Usuario.role == role)
    if email:
        query = query.filter(Usuario.email.ilike(f"%{email}%"))
    if nome:
        query = query.filter(Usuario.nome.ilike(f"%{nome}%"))

    total = query.count()
    itens = (
        query.order_by(Usuario.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "itens": [serializar_usuario_basico(u) for u in itens],
    }


@router.get("/usuarios/{usuario_id}")
def detalhar_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """Retorna dados do usuário com agregados de descarte."""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    total_descartes = (
        db.query(func.count(Descarte.id_descarte))
        .filter(Descarte.usuario_id == usuario_id)
        .scalar()
    )
    kg_confirmados = (
        db.query(func.coalesce(func.sum(Descarte.quantidade_confirmada), 0))
        .filter(Descarte.usuario_id == usuario_id, Descarte.status == "confirmado")
        .scalar()
    )

    return {
        **serializar_usuario_basico(usuario),
        "estatisticas": {
            "total_descartes": total_descartes,
            "kg_confirmados": float(kg_confirmados or 0),
        },
    }


@router.patch("/usuarios/{usuario_id}")
def atualizar_usuario(
    usuario_id: int,
    dados: UsuarioAdminUpdate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_role("admin")),
):
    """Atualiza dados cadastrais básicos."""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    alteracoes: dict = {}
    if dados.email and dados.email != usuario.email:
        existe = db.query(Usuario).filter(Usuario.email == dados.email).first()
        if existe:
            raise HTTPException(status_code=400, detail="Email já cadastrado")
        alteracoes["email"] = {"de": usuario.email, "para": dados.email}
        usuario.email = dados.email
    if dados.nome is not None and dados.nome != usuario.nome:
        alteracoes["nome"] = {"de": usuario.nome, "para": dados.nome}
        usuario.nome = dados.nome
    if dados.telefone is not None and dados.telefone != usuario.telefone:
        alteracoes["telefone"] = {"de": usuario.telefone, "para": dados.telefone}
        usuario.telefone = dados.telefone

    if alteracoes:
        registrar_acao(
            db,
            admin_id=admin.id,
            action="usuario.atualizar",
            target_type="usuario",
            target_id=usuario.id,
            payload=alteracoes,
        )

    db.commit()
    db.refresh(usuario)
    return serializar_usuario_basico(usuario)


@router.patch("/usuarios/{usuario_id}/role")
def alterar_role(
    usuario_id: int,
    payload: UpdateRoleRequest,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_role("admin")),
):
    """Promove ou rebaixa o role do usuário."""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if usuario.id == admin.id and payload.role != "admin":
        raise HTTPException(
            status_code=400,
            detail="Você não pode remover seu próprio role de admin",
        )

    if usuario.role == "cooperativa" and payload.role != "cooperativa":
        possui_pontos_vinculados = db.query(PontoColeta.id).filter(PontoColeta.cooperativa_id == usuario.id).first()
        if possui_pontos_vinculados:
            raise HTTPException(
                status_code=400,
                detail="Reatribua os pontos de coleta desta cooperativa antes de alterar o role.",
            )

    role_anterior = usuario.role
    usuario.role = payload.role
    registrar_acao(
        db,
        admin_id=admin.id,
        action="usuario.alterar_role",
        target_type="usuario",
        target_id=usuario.id,
        payload={"de": role_anterior, "para": payload.role},
    )
    db.commit()
    db.refresh(usuario)
    return serializar_usuario_basico(usuario)


@router.post("/usuarios/{usuario_id}/ajuste-pontuacao")
def ajustar_pontuacao(
    usuario_id: int,
    payload: AjustePontuacaoRequest,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_role("admin")),
):
    """Crédito/débito manual de pontuação. Não permite saldo negativo."""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    novo_total = (usuario.pontuacao_total or 0) + payload.delta
    if novo_total < 0:
        raise HTTPException(
            status_code=400,
            detail="Ajuste resultaria em pontuação negativa",
        )

    pontuacao_anterior = usuario.pontuacao_total or 0
    usuario.pontuacao_total = novo_total
    registrar_acao(
        db,
        admin_id=admin.id,
        action="usuario.ajuste_pontuacao",
        target_type="usuario",
        target_id=usuario.id,
        motivo=payload.motivo,
        payload={
            "delta": payload.delta,
            "de": pontuacao_anterior,
            "para": novo_total,
        },
    )
    db.commit()
    db.refresh(usuario)
    return {
        "usuario_id": usuario.id,
        "pontuacao_total": usuario.pontuacao_total,
        "delta_aplicado": payload.delta,
        "motivo": payload.motivo,
        "aplicado_por": admin.id,
    }


@router.delete("/usuarios/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_role("admin")),
):
    """Remove um usuário. Impede auto-remoção."""
    if usuario_id == admin.id:
        raise HTTPException(status_code=400, detail="Você não pode remover a si mesmo")

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if usuario.role == "cooperativa":
        possui_pontos_vinculados = db.query(PontoColeta.id).filter(PontoColeta.cooperativa_id == usuario.id).first()
        if possui_pontos_vinculados:
            raise HTTPException(
                status_code=400,
                detail="Reatribua os pontos de coleta desta cooperativa antes de remover o usuário.",
            )

    registrar_acao(
        db,
        admin_id=admin.id,
        action="usuario.remover",
        target_type="usuario",
        target_id=usuario.id,
        payload={
            "nome": usuario.nome,
            "email": usuario.email,
            "role": usuario.role,
        },
    )
    db.delete(usuario)
    db.commit()
    return None


# ============================================================
# DESCARTES
# ============================================================
@router.get("/descartes")
def listar_descartes(
    db: Session = Depends(get_db),
    status_filtro: Optional[str] = Query(None, alias="status"),
    usuario_id: Optional[int] = None,
    ponto_coleta_id: Optional[int] = None,
    tipo_residuo: Optional[str] = None,
    data_inicio: Optional[datetime] = None,
    data_fim: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Lista descartes com filtros (status, usuário, ponto, tipo, período)."""
    query = db.query(Descarte)

    if status_filtro:
        query = query.filter(Descarte.status == status_filtro)
    if usuario_id:
        query = query.filter(Descarte.usuario_id == usuario_id)
    if ponto_coleta_id:
        query = query.filter(Descarte.ponto_coleta_id == ponto_coleta_id)
    if tipo_residuo:
        query = query.filter(Descarte.tipo_residuo == tipo_residuo)
    if data_inicio:
        query = query.filter(Descarte.data_desc >= data_inicio)
    if data_fim:
        query = query.filter(Descarte.data_desc <= data_fim)

    total = query.count()
    itens = (
        query.order_by(Descarte.data_desc.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "itens": [serializar_descarte(d, db) for d in itens],
    }


@router.get("/descartes/{id_descarte}")
def detalhar_descarte(id_descarte: int, db: Session = Depends(get_db)):
    """Detalhe de um descarte específico."""
    descarte = (
        db.query(Descarte).filter(Descarte.id_descarte == id_descarte).first()
    )
    if not descarte:
        raise HTTPException(status_code=404, detail="Descarte não encontrado")
    return serializar_descarte(descarte, db)


@router.post("/descartes/{id_descarte}/rejeitar")
def rejeitar_descarte(
    id_descarte: int,
    payload: RejeitarDescarteRequest,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_role("admin")),
):
    """Rejeita um descarte pendente, liberando a reserva de inventário."""
    descarte = (
        db.query(Descarte).filter(Descarte.id_descarte == id_descarte).first()
    )
    if not descarte:
        raise HTTPException(status_code=404, detail="Descarte não encontrado")
    if descarte.status != "pendente":
        raise HTTPException(
            status_code=400,
            detail="Apenas descartes pendentes podem ser rejeitados",
        )

    descarte.status = "rejeitado"

    # Libera a quantidade reservada no item de inventário, se houver.
    if descarte.inventario_usuario_id:
        item = (
            db.query(InventarioUsuario)
            .filter(
                InventarioUsuario.id == descarte.inventario_usuario_id,
                InventarioUsuario.usuario_id == descarte.usuario_id,
            )
            .first()
        )
        if item:
            reservada_atual = float(item.quantidade_reservada or 0)
            item.quantidade_reservada = max(
                reservada_atual - float(descarte.quantidade), 0
            )
            if item.status in ("em_transferencia",):
                item.status = "disponivel"

    registrar_acao(
        db,
        admin_id=admin.id,
        action="descarte.rejeitar",
        target_type="descarte",
        target_id=descarte.id_descarte,
        motivo=payload.motivo,
        payload={"status_anterior": "pendente"},
    )
    db.commit()
    db.refresh(descarte)
    return serializar_descarte(descarte, db)


@router.post("/descartes/{id_descarte}/reverter")
def reverter_descarte(
    id_descarte: int,
    payload: ReverterDescarteRequest,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_role("admin")),
):
    """
    Reverte um descarte confirmado: estorna a pontuação concedida e debita
    a quantidade confirmada do inventário do ponto de coleta.
    """
    descarte = (
        db.query(Descarte).filter(Descarte.id_descarte == id_descarte).first()
    )
    if not descarte:
        raise HTTPException(status_code=404, detail="Descarte não encontrado")
    if descarte.status != "confirmado":
        raise HTTPException(
            status_code=400,
            detail="Apenas descartes confirmados podem ser revertidos",
        )

    quantidade_confirmada = float(descarte.quantidade_confirmada or 0)
    # Pontos concedidos na confirmação: 10 por kg confirmado (RF014).
    pontos_estorno = int(quantidade_confirmada * 10)

    usuario = (
        db.query(Usuario).filter(Usuario.id == descarte.usuario_id).first()
    )
    if usuario and pontos_estorno > 0:
        novo_total = max((usuario.pontuacao_total or 0) - pontos_estorno, 0)
        usuario.pontuacao_total = novo_total
        db.add(Pontuacao(pontos=-pontos_estorno, usuario_id=usuario.id))

    # Debita o resíduo do inventário do ponto de coleta.
    if descarte.ponto_coleta_id and quantidade_confirmada > 0:
        debitar_residuo_do_ponto_coleta(
            descarte.tipo_residuo,
            quantidade_confirmada,
            descarte.ponto_coleta_id,
            db,
        )

    descarte.status = "revertido"
    descarte.quantidade_confirmada = None

    registrar_acao(
        db,
        admin_id=admin.id,
        action="descarte.reverter",
        target_type="descarte",
        target_id=descarte.id_descarte,
        motivo=payload.motivo,
        payload={
            "pontos_estornados": pontos_estorno,
            "kg_estornados": quantidade_confirmada,
        },
    )
    db.commit()
    db.refresh(descarte)
    return serializar_descarte(descarte, db)


# ============================================================
# PONTOS DE COLETA
# ============================================================
@router.delete(
    "/pontos-coleta/{ponto_id}", status_code=status.HTTP_204_NO_CONTENT
)
def desativar_ponto_coleta(
    ponto_id: int,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_role("admin")),
):
    """Desativa (soft-delete) um ponto de coleta."""
    ponto = db.query(PontoColeta).filter(PontoColeta.id == ponto_id).first()
    if not ponto:
        raise HTTPException(status_code=404, detail="Ponto de coleta não encontrado")

    ponto.ativo = 0
    ponto.status = "inativo"
    registrar_acao(
        db,
        admin_id=admin.id,
        action="ponto_coleta.desativar",
        target_type="ponto_coleta",
        target_id=ponto.id,
        payload={"nome": ponto.nome},
    )
    db.commit()
    return None


# ============================================================
# ESTOQUE (consolidado a partir do inventário dos pontos)
# ============================================================
def _total_inventario(inventario) -> float:
    if not inventario:
        return 0.0
    total = 0.0
    for valor in inventario.values():
        try:
            total += float(valor or 0)
        except (TypeError, ValueError):
            continue
    return total


@router.get("/estoque")
def estoque_consolidado(db: Session = Depends(get_db)):
    """Estoque total por tipo de resíduo, agregado de todos os pontos de coleta."""
    pontos = db.query(PontoColeta).all()
    por_tipo: dict[str, float] = {}
    for ponto in pontos:
        inventario = ponto.inventario or {}
        for tipo, qtd in inventario.items():
            try:
                por_tipo[tipo] = por_tipo.get(tipo, 0.0) + float(qtd or 0)
            except (TypeError, ValueError):
                continue

    itens = [
        {"tipo_residuo": tipo, "quantidade_total": round(qtd, 3)}
        for tipo, qtd in sorted(por_tipo.items())
    ]
    return {
        "total_geral": round(sum(por_tipo.values()), 3),
        "itens": itens,
    }


@router.get("/estoque/por-ponto")
def estoque_por_ponto(db: Session = Depends(get_db)):
    """Estoque detalhado por ponto de coleta, com percentual de ocupação."""
    pontos = db.query(PontoColeta).all()
    resultado = []
    for ponto in pontos:
        total = _total_inventario(ponto.inventario)
        percentual = None
        if ponto.capacidade_maxima and ponto.capacidade_maxima > 0:
            percentual = round((total / float(ponto.capacidade_maxima)) * 100, 2)
        resultado.append(
            {
                "ponto_coleta_id": ponto.id,
                "nome": ponto.nome,
                "capacidade_maxima": ponto.capacidade_maxima,
                "total_inventario": round(total, 3),
                "percentual_ocupacao": percentual,
                "inventario": ponto.inventario or {},
                "ativo": ponto.ativo,
            }
        )
    return resultado


# ============================================================
# MÉTRICAS / DASHBOARD
# ============================================================
@router.get("/metrics/resumo")
def metrics_resumo(db: Session = Depends(get_db)):
    """Indicadores agregados para o dashboard admin."""
    total_usuarios = db.query(func.count(Usuario.id)).scalar()
    total_admins = db.query(func.count(Usuario.id)).filter(Usuario.role == "admin").scalar()
    total_pontos = db.query(func.count(PontoColeta.id)).scalar()

    total_descartes = db.query(func.count(Descarte.id_descarte)).scalar()
    descartes_pendentes = (
        db.query(func.count(Descarte.id_descarte))
        .filter(Descarte.status == "pendente")
        .scalar()
    )
    kg_confirmados = (
        db.query(func.coalesce(func.sum(Descarte.quantidade_confirmada), 0))
        .filter(Descarte.status == "confirmado")
        .scalar()
    )
    pontos_distribuidos = (
        db.query(func.coalesce(func.sum(Usuario.pontuacao_total), 0)).scalar()
    )

    return {
        "usuarios": {
            "total": total_usuarios,
            "admins": total_admins,
        },
        "pontos_coleta": {"total": total_pontos},
        "descartes": {
            "total": total_descartes,
            "pendentes": descartes_pendentes,
            "kg_confirmados": float(kg_confirmados or 0),
        },
        "gamificacao": {
            "pontos_distribuidos": int(pontos_distribuidos or 0),
        },
    }


@router.get("/metrics/por-tipo-residuo")
def metrics_por_tipo(db: Session = Depends(get_db)):
    """Kg confirmados agrupados por tipo de resíduo."""
    linhas = (
        db.query(
            Descarte.tipo_residuo,
            func.coalesce(func.sum(Descarte.quantidade_confirmada), 0).label("kg"),
            func.count(Descarte.id_descarte).label("qtd"),
        )
        .filter(Descarte.status == "confirmado")
        .group_by(Descarte.tipo_residuo)
        .all()
    )

    return [
        {"tipo_residuo": tipo, "kg": float(kg or 0), "descartes": qtd}
        for tipo, kg, qtd in linhas
    ]


@router.get("/metrics/ranking-usuarios")
def metrics_ranking(
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=100),
):
    """Top usuários por pontuação total."""
    usuarios = (
        db.query(Usuario)
        .order_by(Usuario.pontuacao_total.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": u.id,
            "nome": u.nome,
            "email": u.email,
            "pontuacao_total": u.pontuacao_total or 0,
        }
        for u in usuarios
    ]


@router.get("/metrics/descartes-por-periodo")
def metrics_descartes_periodo(
    db: Session = Depends(get_db),
    dias: int = Query(30, ge=1, le=365),
):
    """Soma diária de kg confirmados nos últimos N dias."""
    desde = datetime.utcnow() - timedelta(days=dias)
    linhas = (
        db.query(
            func.date(Descarte.data_desc).label("dia"),
            func.coalesce(func.sum(Descarte.quantidade_confirmada), 0).label("kg"),
            func.count(Descarte.id_descarte).label("qtd"),
        )
        .filter(Descarte.data_desc >= desde, Descarte.status == "confirmado")
        .group_by(func.date(Descarte.data_desc))
        .order_by(func.date(Descarte.data_desc))
        .all()
    )

    return [
        {"dia": str(dia), "kg": float(kg or 0), "descartes": qtd}
        for dia, kg, qtd in linhas
    ]


@router.get("/metrics/ocupacao-pontos")
def metrics_ocupacao(
    db: Session = Depends(get_db),
    alerta_pct: float = Query(90.0, ge=0, le=100, description="Limite p/ alerta"),
):
    """Ocupação dos pontos de coleta, ordenada do mais cheio ao mais vazio."""
    pontos = db.query(PontoColeta).all()
    linhas = []
    for ponto in pontos:
        total = _total_inventario(ponto.inventario)
        percentual = None
        if ponto.capacidade_maxima and ponto.capacidade_maxima > 0:
            percentual = round((total / float(ponto.capacidade_maxima)) * 100, 2)
        linhas.append(
            {
                "ponto_coleta_id": ponto.id,
                "nome": ponto.nome,
                "capacidade_maxima": ponto.capacidade_maxima,
                "total_inventario": round(total, 3),
                "percentual_ocupacao": percentual,
                "alerta": percentual is not None and percentual >= alerta_pct,
            }
        )

    linhas.sort(
        key=lambda item: item["percentual_ocupacao"]
        if item["percentual_ocupacao"] is not None
        else -1,
        reverse=True,
    )
    return linhas


# ============================================================
# AUDITORIA
# ============================================================
@router.get("/auditoria")
def listar_auditoria(
    db: Session = Depends(get_db),
    admin_id: Optional[int] = None,
    action: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[int] = None,
    data_inicio: Optional[datetime] = None,
    data_fim: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """Lista entradas do audit log com filtros (admin, ação, alvo, período)."""
    query = db.query(AuditLog)

    if admin_id:
        query = query.filter(AuditLog.admin_id == admin_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if target_type:
        query = query.filter(AuditLog.target_type == target_type)
    if target_id:
        query = query.filter(AuditLog.target_id == target_id)
    if data_inicio:
        query = query.filter(AuditLog.created_at >= data_inicio)
    if data_fim:
        query = query.filter(AuditLog.created_at <= data_fim)

    total = query.count()
    itens = (
        query.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    admin_ids = {i.admin_id for i in itens}
    admins = {
        u.id: u
        for u in db.query(Usuario).filter(Usuario.id.in_(admin_ids)).all()
    } if admin_ids else {}

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "itens": [
            {
                "id": i.id,
                "admin_id": i.admin_id,
                "admin_nome": admins[i.admin_id].nome if i.admin_id in admins else None,
                "action": i.action,
                "target_type": i.target_type,
                "target_id": i.target_id,
                "motivo": i.motivo,
                "payload": i.payload,
                "created_at": i.created_at,
            }
            for i in itens
        ],
    }


# ============================================================
# RELATÓRIOS (export CSV)
# ============================================================
def _csv_response(filename: str, header: list[str], linhas) -> StreamingResponse:
    """Gera uma resposta CSV a partir de um cabeçalho e linhas iteráveis."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    for linha in linhas:
        writer.writerow(linha)
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/relatorios/descartes.csv")
def relatorio_descartes_csv(
    db: Session = Depends(get_db),
    status_filtro: Optional[str] = Query(None, alias="status"),
    usuario_id: Optional[int] = None,
    ponto_coleta_id: Optional[int] = None,
    tipo_residuo: Optional[str] = None,
    data_inicio: Optional[datetime] = None,
    data_fim: Optional[datetime] = None,
):
    """Exporta descartes filtrados em CSV."""
    query = db.query(Descarte)
    if status_filtro:
        query = query.filter(Descarte.status == status_filtro)
    if usuario_id:
        query = query.filter(Descarte.usuario_id == usuario_id)
    if ponto_coleta_id:
        query = query.filter(Descarte.ponto_coleta_id == ponto_coleta_id)
    if tipo_residuo:
        query = query.filter(Descarte.tipo_residuo == tipo_residuo)
    if data_inicio:
        query = query.filter(Descarte.data_desc >= data_inicio)
    if data_fim:
        query = query.filter(Descarte.data_desc <= data_fim)

    descartes = query.order_by(Descarte.data_desc.desc()).all()
    header = [
        "id_descarte",
        "data_desc",
        "status",
        "tipo_residuo",
        "quantidade",
        "quantidade_confirmada",
        "usuario_id",
        "ponto_coleta_id",
    ]
    linhas = (
        [
            d.id_descarte,
            d.data_desc,
            d.status,
            d.tipo_residuo,
            d.quantidade,
            d.quantidade_confirmada,
            d.usuario_id,
            d.ponto_coleta_id,
        ]
        for d in descartes
    )
    return _csv_response("descartes.csv", header, linhas)


@router.get("/relatorios/usuarios.csv")
def relatorio_usuarios_csv(db: Session = Depends(get_db)):
    """Exporta a lista de usuários em CSV."""
    usuarios = db.query(Usuario).order_by(Usuario.id).all()
    header = ["id", "nome", "email", "telefone", "role", "pontuacao_total"]
    linhas = (
        [u.id, u.nome, u.email, u.telefone, u.role, u.pontuacao_total or 0]
        for u in usuarios
    )
    return _csv_response("usuarios.csv", header, linhas)


@router.get("/relatorios/auditoria.csv")
def relatorio_auditoria_csv(
    db: Session = Depends(get_db),
    data_inicio: Optional[datetime] = None,
    data_fim: Optional[datetime] = None,
):
    """Exporta o audit log em CSV."""
    query = db.query(AuditLog)
    if data_inicio:
        query = query.filter(AuditLog.created_at >= data_inicio)
    if data_fim:
        query = query.filter(AuditLog.created_at <= data_fim)

    entradas = query.order_by(AuditLog.created_at.desc()).all()
    header = [
        "id",
        "created_at",
        "admin_id",
        "action",
        "target_type",
        "target_id",
        "motivo",
    ]
    linhas = (
        [
            e.id,
            e.created_at,
            e.admin_id,
            e.action,
            e.target_type,
            e.target_id,
            e.motivo,
        ]
        for e in entradas
    )
    return _csv_response("auditoria.csv", header, linhas)
