from decimal import Decimal
from pydantic import BaseModel, computed_field


class ComparativoItem(BaseModel):
    mes: int
    conta_gerencial_codigo: str
    conta_gerencial_nome: str
    centro_custo_codigo: str
    centro_custo_nome: str
    valor_orcado: Decimal
    valor_realizado: Decimal

    @computed_field
    @property
    def variacao_absoluta(self) -> Decimal:
        return self.valor_realizado - self.valor_orcado

    @computed_field
    @property
    def variacao_percentual(self) -> Decimal:
        if self.valor_orcado == Decimal("0"):
            return Decimal("0")
        return ((self.valor_realizado - self.valor_orcado) / abs(self.valor_orcado) * 100).quantize(Decimal("0.01"))

    model_config = {"from_attributes": True}


class ComparativoResponse(BaseModel):
    ano: int
    id_versao: int
    nome_versao: str
    itens: list[ComparativoItem]
    total_orcado: Decimal
    total_realizado: Decimal
    variacao_absoluta_total: Decimal
    variacao_percentual_total: Decimal
