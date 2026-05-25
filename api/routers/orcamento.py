from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from api.db import get_db
from api.models.dimensoes import DimVersaoOrcamento
from api.models.fatos import FatoOrcamento
from api.schemas.orcamento import (
    OrcamentoCreate, OrcamentoRead,
    VersaoOrcamentoCreate, VersaoOrcamentoRead,
)
from datetime import date

router = APIRouter(prefix="/orcamento", tags=["Orçamento"])
router_versoes = APIRouter(prefix="/versoes-orcamento", tags=["Versões de Orçamento"])


# ── Versões ────────────────────────────────────────────────────────────────

@router_versoes.get("/{ano}", response_model=list[VersaoOrcamentoRead])
def listar_versoes(ano: int, db: Session = Depends(get_db)):
    return (
        db.query(DimVersaoOrcamento)
        .filter(DimVersaoOrcamento.ano == ano)
        .order_by(DimVersaoOrcamento.id)
        .all()
    )


@router_versoes.post("/", response_model=VersaoOrcamentoRead, status_code=status.HTTP_201_CREATED)
def criar_versao(payload: VersaoOrcamentoCreate, db: Session = Depends(get_db)):
    obj = DimVersaoOrcamento(**payload.model_dump(), data_criacao=date.today())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ── Lançamentos de Orçamento ────────────────────────────────────────────────

@router.get("/{ano}/{id_versao}", response_model=list[OrcamentoRead])
def listar_orcamento(
    ano: int,
    id_versao: int,
    id_empresa: int | None = None,
    id_centro_custo: int | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(FatoOrcamento).filter(
        and_(FatoOrcamento.ano == ano, FatoOrcamento.id_versao == id_versao)
    )
    if id_empresa:
        q = q.filter(FatoOrcamento.id_empresa == id_empresa)
    if id_centro_custo:
        q = q.filter(FatoOrcamento.id_centro_custo == id_centro_custo)
    return q.all()


@router.post("/", response_model=OrcamentoRead, status_code=status.HTTP_201_CREATED)
def criar_lancamento_orcamento(payload: OrcamentoCreate, db: Session = Depends(get_db)):
    versao = db.get(DimVersaoOrcamento, payload.id_versao)
    if not versao:
        raise HTTPException(status_code=404, detail="Versão de orçamento não encontrada")
    if versao.bloqueada:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Versão bloqueada — não permite alterações")

    # Upsert: se já existe lançamento para mesma combinação, atualiza o valor
    existente = db.query(FatoOrcamento).filter(
        and_(
            FatoOrcamento.id_empresa == payload.id_empresa,
            FatoOrcamento.id_versao == payload.id_versao,
            FatoOrcamento.id_conta_gerencial == payload.id_conta_gerencial,
            FatoOrcamento.id_centro_custo == payload.id_centro_custo,
            FatoOrcamento.ano == payload.ano,
            FatoOrcamento.mes == payload.mes,
        )
    ).first()

    if existente:
        existente.valor = payload.valor
        existente.observacao = payload.observacao
        db.commit()
        db.refresh(existente)
        return existente

    obj = FatoOrcamento(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
