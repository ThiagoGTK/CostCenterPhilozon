"""Schemas de mapeamento SIA → Gerencial."""

from pydantic import BaseModel, Field


# ── Contas SIA (dim_conta_sia) ─────────────────────────────────────────────

class ContaSiaResumo(BaseModel):
    """Resumo de conta SIA para uso em respostas de mapeamento."""
    id: int
    codpla: int
    conta_codigo: str
    conta_class: str | None
    conta_nome: str
    conta_tipo: str | None
    conta_nivel: int | None

    model_config = {"from_attributes": True}


# ── Mapeamento Conta SIA → Gerencial ──────────────────────────────────────

class MapeamentoContaCreate(BaseModel):
    id_conta_sia: int = Field(..., description="ID da conta em dim_conta_sia")
    id_conta_gerencial: int = Field(..., description="ID da conta em dim_conta_gerencial")
    id_empresa: int = Field(..., description="ID da empresa em dim_empresa")
    observacao: str | None = Field(None, max_length=500)


class MapeamentoContaRead(MapeamentoContaCreate):
    id: int
    ativo: bool
    conta_sia: ContaSiaResumo | None = None

    model_config = {"from_attributes": True}


class MapeamentoContaUpdate(BaseModel):
    id_conta_gerencial: int
    observacao: str | None = None


# ── Mapeamento CC SIA → CC Gerencial ──────────────────────────────────────

class MapeamentoCCCreate(BaseModel):
    cc_sia_codigo: str = Field(..., min_length=1, max_length=50,
                               description="CC_COD do CTB_CCUSTOS")
    cc_sia_nome: str | None = Field(None, max_length=200,
                                    description="CC_DESC — opcional, apenas para exibição")
    id_empresa: int
    id_centro_custo_gerencial: int
    observacao: str | None = Field(None, max_length=500)


class MapeamentoCCRead(MapeamentoCCCreate):
    id: int
    ativo: bool

    model_config = {"from_attributes": True}


class MapeamentoCCUpdate(BaseModel):
    id_centro_custo_gerencial: int
    cc_sia_nome: str | None = None
    observacao: str | None = None
