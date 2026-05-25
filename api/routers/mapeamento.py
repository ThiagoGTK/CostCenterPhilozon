"""
Router de mapeamentos SIA → Gerencial.

Endpoints:
  GET  /contas-sia                     — lista contas do DW (dim_conta_sia)
  GET  /mapeamentos/contas             — lista mapeamentos conta SIA→gerencial
  POST /mapeamentos/contas             — cria mapeamento
  PUT  /mapeamentos/contas/{id}        — atualiza conta gerencial de destino
  DELETE /mapeamentos/contas/{id}      — desativa mapeamento

  GET  /mapeamentos/centros-custo      — lista mapeamentos CC SIA→gerencial
  POST /mapeamentos/centros-custo      — cria mapeamento
  PUT  /mapeamentos/centros-custo/{id} — atualiza CC gerencial de destino
  DELETE /mapeamentos/centros-custo/{id} — desativa
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from api.db import get_db
from api.models.dimensoes import DimContaSia
from api.models.mapeamentos import MapeamentoContaSia, MapeamentoCentroCusto
from api.schemas.mapeamento import (
    ContaSiaResumo,
    MapeamentoContaCreate,
    MapeamentoContaRead,
    MapeamentoContaUpdate,
    MapeamentoCCCreate,
    MapeamentoCCRead,
    MapeamentoCCUpdate,
)

router = APIRouter(tags=["Mapeamentos SIA → Gerencial"])


# ── Contas SIA disponíveis no DW ──────────────────────────────────────────

@router.get("/contas-sia", response_model=list[ContaSiaResumo])
def listar_contas_sia(
    codpla: int | None = Query(None, description="Filtrar por plano (1=Philozon 2019, 2=Philozon 2023)"),
    nivel: int | None = Query(None, description="Filtrar por nível hierárquico"),
    db: Session = Depends(get_db),
):
    """Lista contas contábeis do SIA já carregadas no DW pelo ETL."""
    q = db.query(DimContaSia)
    if codpla is not None:
        q = q.filter(DimContaSia.codpla == codpla)
    if nivel is not None:
        q = q.filter(DimContaSia.conta_nivel == nivel)
    return q.order_by(DimContaSia.codpla, DimContaSia.conta_class).all()


# ── Mapeamento: conta SIA → conta gerencial ───────────────────────────────

@router.get("/mapeamentos/contas", response_model=list[MapeamentoContaRead])
def listar_mapeamentos_contas(
    id_empresa: int | None = Query(None),
    apenas_ativos: bool = True,
    db: Session = Depends(get_db),
):
    q = db.query(MapeamentoContaSia).options(joinedload(MapeamentoContaSia.conta_sia))
    if apenas_ativos:
        q = q.filter(MapeamentoContaSia.ativo == True)
    if id_empresa is not None:
        q = q.filter(MapeamentoContaSia.id_empresa == id_empresa)
    return q.order_by(MapeamentoContaSia.id_empresa, MapeamentoContaSia.id_conta_sia).all()


@router.post("/mapeamentos/contas", response_model=MapeamentoContaRead, status_code=status.HTTP_201_CREATED)
def criar_mapeamento_conta(payload: MapeamentoContaCreate, db: Session = Depends(get_db)):
    # Verifica duplicata ativa
    existente = db.query(MapeamentoContaSia).filter(
        MapeamentoContaSia.id_conta_sia == payload.id_conta_sia,
        MapeamentoContaSia.id_empresa == payload.id_empresa,
        MapeamentoContaSia.ativo == True,
    ).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Conta SIA {payload.id_conta_sia} já possui mapeamento ativo para esta empresa.",
        )
    obj = MapeamentoContaSia(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    # Eager load para resposta completa
    db.refresh(obj)
    _ = obj.conta_sia
    return obj


@router.put("/mapeamentos/contas/{id}", response_model=MapeamentoContaRead)
def atualizar_mapeamento_conta(id: int, payload: MapeamentoContaUpdate, db: Session = Depends(get_db)):
    obj = db.get(MapeamentoContaSia, id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapeamento não encontrado")
    obj.id_conta_gerencial = payload.id_conta_gerencial
    if payload.observacao is not None:
        obj.observacao = payload.observacao
    db.commit()
    db.refresh(obj)
    _ = obj.conta_sia
    return obj


@router.delete("/mapeamentos/contas/{id}", status_code=status.HTTP_204_NO_CONTENT)
def desativar_mapeamento_conta(id: int, db: Session = Depends(get_db)):
    obj = db.get(MapeamentoContaSia, id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapeamento não encontrado")
    obj.ativo = False
    db.commit()


# ── Mapeamento: CC SIA → CC gerencial ────────────────────────────────────

@router.get("/mapeamentos/centros-custo", response_model=list[MapeamentoCCRead])
def listar_mapeamentos_cc(
    id_empresa: int | None = Query(None),
    apenas_ativos: bool = True,
    db: Session = Depends(get_db),
):
    q = db.query(MapeamentoCentroCusto)
    if apenas_ativos:
        q = q.filter(MapeamentoCentroCusto.ativo == True)
    if id_empresa is not None:
        q = q.filter(MapeamentoCentroCusto.id_empresa == id_empresa)
    return q.order_by(MapeamentoCentroCusto.id_empresa, MapeamentoCentroCusto.cc_sia_codigo).all()


@router.post("/mapeamentos/centros-custo", response_model=MapeamentoCCRead, status_code=status.HTTP_201_CREATED)
def criar_mapeamento_cc(payload: MapeamentoCCCreate, db: Session = Depends(get_db)):
    existente = db.query(MapeamentoCentroCusto).filter(
        MapeamentoCentroCusto.cc_sia_codigo == payload.cc_sia_codigo,
        MapeamentoCentroCusto.id_empresa == payload.id_empresa,
        MapeamentoCentroCusto.ativo == True,
    ).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"CC SIA '{payload.cc_sia_codigo}' já possui mapeamento ativo para esta empresa.",
        )
    obj = MapeamentoCentroCusto(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/mapeamentos/centros-custo/{id}", response_model=MapeamentoCCRead)
def atualizar_mapeamento_cc(id: int, payload: MapeamentoCCUpdate, db: Session = Depends(get_db)):
    obj = db.get(MapeamentoCentroCusto, id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapeamento não encontrado")
    obj.id_centro_custo_gerencial = payload.id_centro_custo_gerencial
    if payload.cc_sia_nome is not None:
        obj.cc_sia_nome = payload.cc_sia_nome
    if payload.observacao is not None:
        obj.observacao = payload.observacao
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/mapeamentos/centros-custo/{id}", status_code=status.HTTP_204_NO_CONTENT)
def desativar_mapeamento_cc(id: int, db: Session = Depends(get_db)):
    obj = db.get(MapeamentoCentroCusto, id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapeamento não encontrado")
    obj.ativo = False
    db.commit()
