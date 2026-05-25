"""
Testes da camada de transformação do ETL.
Foco em normalização monetária e idempotência.
"""

import pytest
from decimal import Decimal
import pandas as pd
from etl.transformer import (
    normalizar_valor_monetario,
    normalizar_coluna_monetaria,
    gerar_dim_tempo,
)
from datetime import date


class TestNormalizacaoMonetaria:
    def test_normaliza_int64_por_100(self):
        resultado = normalizar_valor_monetario(123456, "CTB_MOVIMENTOS.valor")
        assert resultado == Decimal("1234.56")
        assert isinstance(resultado, Decimal)

    def test_normaliza_int64_por_10000(self):
        from etl.transformer import ESCALA_MONETARIA
        # Adiciona escala de teste temporária
        ESCALA_MONETARIA["TESTE.valor"] = 10000
        resultado = normalizar_valor_monetario(123456, "TESTE.valor")
        assert resultado == Decimal("12.3456")
        del ESCALA_MONETARIA["TESTE.valor"]

    def test_valor_none_retorna_zero(self):
        resultado = normalizar_valor_monetario(None, "CTB_MOVIMENTOS.valor")
        assert resultado == Decimal("0")

    def test_sem_float_em_nenhum_passo(self):
        resultado = normalizar_valor_monetario(100, "CTB_MOVIMENTOS.valor")
        # Garante que o resultado é Decimal e não float
        assert type(resultado) is Decimal
        assert resultado == Decimal("1.00")

    def test_normaliza_coluna_dataframe(self):
        df = pd.DataFrame({"MOV_VALOR": [100000, 250000, 0, None]})
        df = normalizar_coluna_monetaria(df, "MOV_VALOR", "CTB_MOVIMENTOS.valor")
        assert df["MOV_VALOR"].iloc[0] == Decimal("1000.00")
        assert df["MOV_VALOR"].iloc[1] == Decimal("2500.00")
        assert df["MOV_VALOR"].iloc[2] == Decimal("0")
        assert df["MOV_VALOR"].iloc[3] == Decimal("0")


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
