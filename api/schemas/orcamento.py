from decimal import Decimal
from datetime import date
from pydantic import BaseModel, Field, field_validator
from typing import Literal


class VersaoOrcamentoCreate(BaseModel):
    ano: int = Field(..., ge=2000, le=2100)
    tipo: Literal["ORIGINAL", "REVISAO", "FORECAST"]
    nome: str = Field(..., min_length=1, max_length=100)
    descricao: str | None = None


class VersaoOrcamentoRead(VersaoOrcamentoCreate):
    id: int
    data_criacao: date
    bloqueada: bool

    model_config = {"from_attributes": True}


class OrcamentoCreate(BaseModel):
    id_empresa: int
    id_versao: int
    id_conta_gerencial: int
    id_centro_custo: int
    ano: int = Field(..., ge=2000, le=2100)
    mes: int = Field(..., ge=1, le=12)
    valor: Decimal = Field(..., decimal_places=2)
    observacao: str | None = None

    @field_validator("valor")
    @classmethod
    def valor_nao_negativo(cls, v: Decimal) -> Decimal:
        if v < Decimal("0"):
            raise ValueError("Valor do orçamento não pode ser negativo")
        return v


class OrcamentoRead(OrcamentoCreate):
    id: int
    criado_por: str | None

    model_config = {"from_attributes": True}
