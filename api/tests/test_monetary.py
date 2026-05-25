"""
Testes das regras monetárias críticas.
Regra: NUNCA usar float para valores financeiros. Sempre Decimal.
"""

import pytest
from decimal import Decimal
from pydantic import ValidationError
from api.schemas.orcamento import OrcamentoCreate


class TestDecimalMonetary:
    def test_valor_orcamento_aceita_decimal(self):
        payload = OrcamentoCreate(
            id_empresa=1,
            id_versao=1,
            id_conta_gerencial=1,
            id_centro_custo=1,
            ano=2025,
            mes=1,
            valor=Decimal("12345.67"),
        )
        assert payload.valor == Decimal("12345.67")
        assert isinstance(payload.valor, Decimal)

    def test_valor_orcamento_nao_pode_ser_negativo(self):
        with pytest.raises(ValidationError) as exc_info:
            OrcamentoCreate(
                id_empresa=1,
                id_versao=1,
                id_conta_gerencial=1,
                id_centro_custo=1,
                ano=2025,
                mes=1,
                valor=Decimal("-1.00"),
            )
        assert "não pode ser negativo" in str(exc_info.value)

    def test_valor_zero_e_valido(self):
        payload = OrcamentoCreate(
            id_empresa=1,
            id_versao=1,
            id_conta_gerencial=1,
            id_centro_custo=1,
            ano=2025,
            mes=1,
            valor=Decimal("0"),
        )
        assert payload.valor == Decimal("0")

    def test_precisao_decimal_preservada(self):
        """Garante que Decimal não perde precisão como float faria."""
        v = Decimal("0.1") + Decimal("0.2")
        assert v == Decimal("0.3")
        # Com float isso falharia: 0.1 + 0.2 == 0.30000000000000004


class TestComparativoSchema:
    def test_variacao_percentual_calcula_corretamente(self):
        from api.schemas.comparativo import ComparativoItem
        item = ComparativoItem(
            mes=1,
            conta_gerencial_codigo="3.1",
            conta_gerencial_nome="Receita Bruta",
            centro_custo_codigo="CC01",
            centro_custo_nome="Comercial",
            valor_orcado=Decimal("100000.00"),
            valor_realizado=Decimal("110000.00"),
        )
        assert item.variacao_absoluta == Decimal("10000.00")
        assert item.variacao_percentual == Decimal("10.00")

    def test_variacao_percentual_com_orcado_zero(self):
        from api.schemas.comparativo import ComparativoItem
        item = ComparativoItem(
            mes=1,
            conta_gerencial_codigo="3.1",
            conta_gerencial_nome="Receita Bruta",
            centro_custo_codigo="CC01",
            centro_custo_nome="Comercial",
            valor_orcado=Decimal("0"),
            valor_realizado=Decimal("5000.00"),
        )
        # Sem divisão por zero
        assert item.variacao_percentual == Decimal("0")
