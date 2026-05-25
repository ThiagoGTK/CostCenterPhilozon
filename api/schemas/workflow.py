from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


# ── Workflow ────────────────────────────────────────────────────────────────

class WorkflowIniciar(BaseModel):
    id_versao: int
    id_empresa: int
    criado_por: str


class WorkflowEnviar(BaseModel):
    enviado_por: str


class WorkflowAprovar(BaseModel):
    aprovado_por: str
    comentario: str | None = None


class WorkflowReprovar(BaseModel):
    reprovado_por: str
    comentario: str  # obrigatório ao reprovar


class WorkflowRead(BaseModel):
    id: int
    id_versao: int
    id_empresa: int
    status: str
    criado_por: str
    enviado_por: str | None
    aprovado_por: str | None
    reprovado_por: str | None
    data_envio: datetime | None
    data_decisao: datetime | None
    comentario: str | None
    criado_em: datetime
    atualizado_em: datetime

    model_config = {"from_attributes": True}


class WorkflowListItem(WorkflowRead):
    """WorkflowRead enriquecido com nomes de versão e empresa."""
    versao_nome: str
    versao_ano: int
    empresa_nome: str

    model_config = {"from_attributes": True}


# ── Justificativas ──────────────────────────────────────────────────────────

class JustificativaCreate(BaseModel):
    id_empresa: int
    id_versao: int
    id_conta_gerencial: int
    id_centro_custo: int
    ano: int
    mes: int
    valor_orcado: Decimal
    valor_realizado: Decimal
    variacao_absoluta: Decimal
    variacao_percentual: Decimal
    justificativa: str
    criado_por: str


class JustificativaRead(JustificativaCreate):
    id: int
    criado_em: datetime

    model_config = {"from_attributes": True}
