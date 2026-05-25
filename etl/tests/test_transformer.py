"""
Testes da camada de transformação do ETL.
Foco em tipagem Decimal e idempotência.

Contexto SIA (validado via MCP Firebird 2026-05):
- MOV_VALOR é NUMERIC nativo — não há divisão por escala.
- MOV_TIPO é inteiro: 1=Débito, 2=Crédito.
- MOV_CECT pode ser NULL.
"""

import pytest
from decimal import Decimal
import pandas as pd
from etl.transformer import (
    sia_decimal,
    normalizar_coluna_monetaria,
    gerar_dim_tempo,
    transformar_lancamentos_contabeis,
)
from datetime import date


class TestSiaDecimal:
    def test_converte_float_para_decimal(self):
        resultado = sia_decimal(1234.56)
        assert isinstance(resultado, Decimal)
        assert resultado == Decimal("1234.56")

    def test_none_retorna_zero(self):
        assert sia_decimal(None) == Decimal("0")

    def test_sem_float_no_resultado(self):
        resultado = sia_decimal(100.0)
        assert type(resultado) is Decimal

    def test_valor_ja_decimal_preservado(self):
        assert sia_decimal(Decimal("9999.99")) == Decimal("9999.99")

    def test_normaliza_coluna_dataframe(self):
        df = pd.DataFrame({"MOV_VALOR": [1807.10, 180.00, 0.0, None]})
        df = normalizar_coluna_monetaria(df, "MOV_VALOR")
        assert df["MOV_VALOR"].iloc[0] == Decimal("1807.10")
        assert df["MOV_VALOR"].iloc[1] == Decimal("180.00")
        assert df["MOV_VALOR"].iloc[2] == Decimal("0")
        assert df["MOV_VALOR"].iloc[3] == Decimal("0")


class TestTransformarLancamentos:
    def _df_lancamentos(self) -> pd.DataFrame:
        return pd.DataFrame({
            "MOV_CODEMP": [1, 1],
            "MOV_NUMLAN": [42, 42],
            "MOV_DATA":   [date(2025, 1, 15), date(2025, 1, 15)],
            "MOV_CODCON": [454, 595],
            "MOV_CECT":   [10, None],
            "MOV_TIPO":   [1, 2],
            "MOV_VALOR":  [1500.00, 1500.00],
            "MOV_HIST":   ["Compra material", "Pagamento fornecedor"],
        })

    def test_tipo_lancamento_mapeado(self):
        df = transformar_lancamentos_contabeis(self._df_lancamentos())
        assert list(df["tipo_lancamento"]) == ["D", "C"]

    def test_valor_convertido_para_decimal(self):
        df = transformar_lancamentos_contabeis(self._df_lancamentos())
        for v in df["valor"]:
            assert isinstance(v, Decimal)

    def test_chave_upsert_unica(self):
        df = transformar_lancamentos_contabeis(self._df_lancamentos())
        assert df["sia_lancamento_id"].nunique() == 2

    def test_cect_null_vira_string_vazia(self):
        df = transformar_lancamentos_contabeis(self._df_lancamentos())
        assert df["cc_sia_codigo"].iloc[1] == ""

    def test_colunas_renomeadas(self):
        df = transformar_lancamentos_contabeis(self._df_lancamentos())
        assert "codemp" in df.columns
        assert "data_referencia" in df.columns
        assert "conta_sia_codigo" in df.columns
        assert "valor" in df.columns

    def test_dataframe_vazio_retorna_vazio(self):
        df_empty = pd.DataFrame(columns=[
            "MOV_CODEMP", "MOV_NUMLAN", "MOV_DATA",
            "MOV_CODCON", "MOV_CECT", "MOV_TIPO", "MOV_VALOR", "MOV_HIST",
        ])
        resultado = transformar_lancamentos_contabeis(df_empty)
        assert resultado.empty


class TestDimTempo:
    def test_gera_todos_os_dias_do_mes(self):
        df = gerar_dim_tempo(date(2025, 1, 1), date(2025, 1, 31))
        assert len(df) == 31

    def test_colunas_corretas(self):
        df = gerar_dim_tempo(date(2025, 3, 1), date(2025, 3, 31))
        assert set(df.columns) == {"data", "ano", "mes", "trimestre", "semestre", "nome_mes"}

    def test_trimestre_correto(self):
        df = gerar_dim_tempo(date(2025, 4, 1), date(2025, 4, 1))
        assert df["trimestre"].iloc[0] == 2

    def test_semestre_correto(self):
        df = gerar_dim_tempo(date(2025, 7, 1), date(2025, 7, 1))
        assert df["semestre"].iloc[0] == 2

    def test_nome_mes_janeiro(self):
        df = gerar_dim_tempo(date(2025, 1, 15), date(2025, 1, 15))
        assert df["nome_mes"].iloc[0] == "Janeiro"
