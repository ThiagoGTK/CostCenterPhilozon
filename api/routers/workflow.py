from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.db import get_db
from api.models.workflow import WorkflowOrcamento, StatusWorkflow
from api.models.dimensoes import DimVersaoOrcamento
from api.schemas.workflow import WorkflowEnviar, WorkflowAprovar, WorkflowReprovar, WorkflowRead

router = APIRouter(prefix="/workflow", tags=["Workflow de Aprovação"])


@router.post("/enviar", response_model=WorkflowRead, status_code=status.HTTP_201_CREATED)
def enviar_para_revisao(payload: WorkflowEnviar, db: Session = Depends(get_db)):
    versao = db.get(DimVersaoOrcamento, payload.id_versao)
    if not versao:
        raise HTTPException(status_code=404, detail="Versão não encontrada")

    wf = WorkflowOrcamento(
        id_versao=payload.id_versao,
        id_empresa=payload.id_empresa,
        status=StatusWorkflow.ENVIADO.value,
        criado_por=payload.enviado_por,
        enviado_por=payload.enviado_por,
        data_envio=datetime.now(),
    )
    db.add(wf)
    db.commit()
    db.refresh(wf)
    return wf


@router.post("/aprovar", response_model=WorkflowRead)
def aprovar(payload: WorkflowAprovar, db: Session = Depends(get_db)):
    wf = db.get(WorkflowOrcamento, payload.id_workflow)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow não encontrado")
    if wf.status != StatusWorkflow.ENVIADO.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Workflow em status '{wf.status}' — esperado 'ENVIADO'"
        )
    wf.status = StatusWorkflow.APROVADO.value
    wf.aprovado_por = payload.aprovado_por
    wf.comentario = payload.comentario
    wf.data_decisao = datetime.now()

    # Bloquear a versão após aprovação
    versao = db.get(DimVersaoOrcamento, wf.id_versao)
    if versao:
        versao.bloqueada = True

    db.commit()
    db.refresh(wf)
    return wf


@router.post("/reprovar", response_model=WorkflowRead)
def reprovar(payload: WorkflowReprovar, db: Session = Depends(get_db)):
    wf = db.get(WorkflowOrcamento, payload.id_workflow)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow não encontrado")
    if wf.status != StatusWorkflow.ENVIADO.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Workflow em status '{wf.status}' — esperado 'ENVIADO'"
        )
    wf.status = StatusWorkflow.REPROVADO.value
    wf.reprovado_por = payload.reprovado_por
    wf.comentario = payload.comentario
    wf.data_decisao = datetime.now()
    db.commit()
    db.refresh(wf)
    return wf
