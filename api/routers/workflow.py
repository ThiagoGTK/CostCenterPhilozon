"""
Workflow de aprovação de orçamentos.

Fluxo: RASCUNHO → ENVIADO → APROVADO | REPROVADO

Endpoints:
  GET  /workflow/                    — lista todos os registros
  GET  /workflow/{id}                — detalhe de um registro
  POST /workflow/iniciar             — cria RASCUNHO para uma versão/empresa
  POST /workflow/{id}/enviar         — RASCUNHO → ENVIADO (+ e-mail aprovadores)
  POST /workflow/{id}/aprovar        — ENVIADO → APROVADO (+ bloqueia versão + e-mail)
  POST /workflow/{id}/reprovar       — ENVIADO → REPROVADO (+ e-mail)
  GET  /workflow/{id}/justificativas — lista justificativas vinculadas
  POST /workflow/{id}/justificativas — adiciona justificativa de variação
"""

from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.auth.deps import get_current_user, require_admin_ou_gestor
from api.db import get_db
from api.models.usuario import Usuario
from api.models.dimensoes import DimEmpresa, DimVersaoOrcamento
from api.models.workflow import JustificativaVariacao, StatusWorkflow, WorkflowOrcamento
from api.schemas.workflow import (
    JustificativaCreate,
    JustificativaRead,
    WorkflowAprovar,
    WorkflowEnviar,
    WorkflowIniciar,
    WorkflowListItem,
    WorkflowRead,
    WorkflowReprovar,
)
from api.services import email as email_svc

router = APIRouter(prefix="/workflow", tags=["Workflow de Aprovação"])


# ── helpers ──────────────────────────────────────────────────────────────────

def _get_wf_or_404(wf_id: int, db: Session) -> WorkflowOrcamento:
    wf = db.get(WorkflowOrcamento, wf_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow não encontrado")
    return wf


def _exige_status(wf: WorkflowOrcamento, esperado: StatusWorkflow) -> None:
    if wf.status != esperado.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Status atual '{wf.status}' — esperado '{esperado.value}'",
        )


def _enriquecer(wf: WorkflowOrcamento) -> WorkflowListItem:
    return WorkflowListItem(
        **WorkflowRead.model_validate(wf).model_dump(),
        versao_nome=wf.versao.nome,
        versao_ano=wf.versao.ano,
        empresa_nome=wf.empresa.nome,
    )


# ── rotas ─────────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[WorkflowListItem])
def listar_workflows(
    ano: int | None = Query(None, description="Filtrar por ano da versão"),
    _u: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[WorkflowListItem]:
    q = db.query(WorkflowOrcamento)
    workflows = q.all()
    resultado = [_enriquecer(wf) for wf in workflows]
    if ano:
        resultado = [w for w in resultado if w.versao_ano == ano]
    return resultado


@router.get("/{wf_id}", response_model=WorkflowListItem)
def detalhe_workflow(
    wf_id: int,
    _u: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkflowListItem:
    return _enriquecer(_get_wf_or_404(wf_id, db))


@router.post("/iniciar", response_model=WorkflowListItem, status_code=status.HTTP_201_CREATED)
def iniciar_workflow(
    payload: WorkflowIniciar,
    _u: Usuario = Depends(require_admin_ou_gestor),
    db: Session = Depends(get_db),
) -> WorkflowListItem:
    """Cria um registro de workflow em status RASCUNHO."""
    versao = db.get(DimVersaoOrcamento, payload.id_versao)
    if not versao:
        raise HTTPException(status_code=404, detail="Versão não encontrada")

    empresa = db.get(DimEmpresa, payload.id_empresa)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    if versao.bloqueada:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Versão bloqueada — não é possível iniciar workflow",
        )

    # Bloqueia duplicata ativa
    existente = (
        db.query(WorkflowOrcamento)
        .filter(
            WorkflowOrcamento.id_versao == payload.id_versao,
            WorkflowOrcamento.id_empresa == payload.id_empresa,
            WorkflowOrcamento.status.in_(
                [StatusWorkflow.RASCUNHO.value, StatusWorkflow.ENVIADO.value]
            ),
        )
        .first()
    )
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe workflow ativo (status: {existente.status}) para esta versão/empresa",
        )

    wf = WorkflowOrcamento(
        id_versao=payload.id_versao,
        id_empresa=payload.id_empresa,
        status=StatusWorkflow.RASCUNHO.value,
        criado_por=payload.criado_por,
    )
    db.add(wf)
    db.commit()
    db.refresh(wf)
    return _enriquecer(wf)


@router.post("/{wf_id}/enviar", response_model=WorkflowListItem)
def enviar_para_revisao(
    wf_id: int,
    payload: WorkflowEnviar,
    background_tasks: BackgroundTasks,
    _u: Usuario = Depends(require_admin_ou_gestor),
    db: Session = Depends(get_db),
) -> WorkflowListItem:
    """Transição RASCUNHO → ENVIADO. Dispara e-mail para aprovadores em background."""
    wf = _get_wf_or_404(wf_id, db)
    _exige_status(wf, StatusWorkflow.RASCUNHO)

    wf.status = StatusWorkflow.ENVIADO.value
    wf.enviado_por = payload.enviado_por
    wf.data_envio = datetime.now()
    db.commit()
    db.refresh(wf)

    versao_nome = wf.versao.nome
    empresa_nome = wf.empresa.nome
    background_tasks.add_task(
        email_svc.notificar_envio_para_revisao,
        versao_nome,
        empresa_nome,
        payload.enviado_por,
    )

    return _enriquecer(wf)


@router.post("/{wf_id}/aprovar", response_model=WorkflowListItem)
def aprovar(
    wf_id: int,
    payload: WorkflowAprovar,
    background_tasks: BackgroundTasks,
    _u: Usuario = Depends(require_admin_ou_gestor),
    db: Session = Depends(get_db),
) -> WorkflowListItem:
    """Transição ENVIADO → APROVADO. Bloqueia versão e envia e-mail."""
    wf = _get_wf_or_404(wf_id, db)
    _exige_status(wf, StatusWorkflow.ENVIADO)

    wf.status = StatusWorkflow.APROVADO.value
    wf.aprovado_por = payload.aprovado_por
    wf.comentario = payload.comentario
    wf.data_decisao = datetime.now()

    # Bloquear versão após aprovação
    versao = db.get(DimVersaoOrcamento, wf.id_versao)
    if versao:
        versao.bloqueada = True

    db.commit()
    db.refresh(wf)

    versao_nome = wf.versao.nome
    empresa_nome = wf.empresa.nome
    from api.config import get_settings
    email_responsavel = get_settings().email_notificacao_workflow or None
    background_tasks.add_task(
        email_svc.notificar_aprovado,
        versao_nome,
        empresa_nome,
        payload.aprovado_por,
        payload.comentario,
        email_responsavel,
    )

    return _enriquecer(wf)


@router.post("/{wf_id}/reprovar", response_model=WorkflowListItem)
def reprovar(
    wf_id: int,
    payload: WorkflowReprovar,
    background_tasks: BackgroundTasks,
    _u: Usuario = Depends(require_admin_ou_gestor),
    db: Session = Depends(get_db),
) -> WorkflowListItem:
    """Transição ENVIADO → REPROVADO. Envia e-mail com motivo."""
    wf = _get_wf_or_404(wf_id, db)
    _exige_status(wf, StatusWorkflow.ENVIADO)

    wf.status = StatusWorkflow.REPROVADO.value
    wf.reprovado_por = payload.reprovado_por
    wf.comentario = payload.comentario
    wf.data_decisao = datetime.now()
    db.commit()
    db.refresh(wf)

    versao_nome = wf.versao.nome
    empresa_nome = wf.empresa.nome
    from api.config import get_settings
    email_responsavel = get_settings().email_notificacao_workflow or None
    background_tasks.add_task(
        email_svc.notificar_reprovado,
        versao_nome,
        empresa_nome,
        payload.reprovado_por,
        payload.comentario,
        email_responsavel,
    )

    return _enriquecer(wf)


# ── Justificativas ────────────────────────────────────────────────────────────

@router.get("/{wf_id}/justificativas", response_model=list[JustificativaRead])
def listar_justificativas(
    wf_id: int,
    _u: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[JustificativaRead]:
    wf = _get_wf_or_404(wf_id, db)
    return (
        db.query(JustificativaVariacao)
        .filter(
            JustificativaVariacao.id_versao == wf.id_versao,
            JustificativaVariacao.id_empresa == wf.id_empresa,
        )
        .all()
    )


@router.post(
    "/{wf_id}/justificativas",
    response_model=JustificativaRead,
    status_code=status.HTTP_201_CREATED,
)
def criar_justificativa(
    wf_id: int,
    payload: JustificativaCreate,
    _u: Usuario = Depends(require_admin_ou_gestor),
    db: Session = Depends(get_db),
) -> JustificativaRead:
    """Registra justificativa de variação vinculada ao workflow."""
    _get_wf_or_404(wf_id, db)
    j = JustificativaVariacao(**payload.model_dump())
    db.add(j)
    db.commit()
    db.refresh(j)
    return j
