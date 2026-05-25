"""
Camada de transformação do ETL.

Responsabilidades:
- Normalizar campos monetários INT64 do SIA para Decimal.
- Aplicar mapeamentos SIA → gerencial.
- Enriquecer com dimensões de tempo.
- Garantir tipos corretos antes da carga.
"""

import logging
from decimal import Decimal
from datetime import date
import pandas as pd

logger = logging.getLogger(__name__)

# Mapa de escala dos campos monetários por tabela.
# TODO: Validar escala real consultando dicionário de dados do SIA.
# Valores possíveis: 100 (dividir por 100) ou 10000 (dividir por 10000).
ESCALA_MONETARIA: dict[str, int] = {
    "CTB_MOVIMENTOS.valor": 100,
    "CRC_TITULO.valor": 100,
    "CPG_TITULO.valor": 100,
    "EST_VENDA.valor": 100,
    "FIS_MOVIMENTO.valor": 100,
    "RH_MOVIMENTO.valor": 100,
}


def normalizar_valor_monetario(valor_int64: int | None, tabela_campo: str) -> Decimal:
    """
    Converte campo monetário INT64 do SIA para Decimal.
    Usa a escala definida no mapa ESCALA_MONETARIA.
    """
    if valor_int64 is None:
        return Decimal("0")
    escala = ESCALA_MONETARIA.get(tabela_campo, 100)
    return Decimal(str(valor_int64)) / Decimal(str(escala))


def normalizar_coluna_monetaria(df: pd.DataFrame, coluna: str, tabela_campo: str) -> pd.DataFrame:
    """Normaliza uma coluna inteira de valores monetários INT64."""
    escala = ESCALA_MONETARIA.get(tabela_campo, 100)
    df[coluna] = df[coluna].apply(
        lambda v: Decimal(str(int(v))) / Decimal(str(escala)) if pd.notna(v) else Decimal("0")
    )
    return df


def transformar_lancamentos_contabeis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforma lançamentos contábeis do CTB_MOVIMENTOS.

    Colunas esperadas do SIA (TODO: confirmar nomes reais):
    - MOV_CODEMP, MOV_DATA, MOV_CONTA, MOV_CCUSTO, MOV_VALOR, MOV_TIPO, MOV_HISTORICO, MOV_NUMERO
    """
    if df.empty:
        return df

    df = df.copy()

    # Normalizar valor monetário
    df = normalizar_coluna_monetaria(df, "MOV_VALOR", "CTB_MOVIMENTOS.valor")

    # Chave de idempotência: empresa + número do lançamento
    df["sia_lancamento_id"] = df["MOV_CODEMP"].astype(str) + "_" + df["MOV_NUMERO"].astype(str)

    # Mapear tipo: D/C
    df["tipo_lancamento"] = df["MOV_TIPO"].str.upper().str.strip()

    # Renomear para padrão interno
    df = df.rename(columns={
        "MOV_CODEMP": "codemp",
        "MOV_DATA": "data_referencia",
        "MOV_CONTA": "conta_sia_codigo",
        "MOV_CCUSTO": "cc_sia_codigo",
        "MOV_VALOR": "valor",
        "MOV_HISTORICO": "historico",
    })

    logger.info("Transformados %d lançamentos contábeis", len(df))
    return df


def gerar_dim_tempo(data_inicio: date, data_fim: date) -> pd.DataFrame:
    """Gera registros para a dimensão tempo entre duas datas."""
    datas = pd.date_range(start=data_inicio, end=data_fim, freq="D")
    NOMES_MESES = [
        "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
    ]
    return pd.DataFrame({
        "data": datas.date,
        "ano": datas.year,
        "mes": datas.month,
        "trimestre": datas.quarter,
        "semestre": datas.month.map(lambda m: 1 if m <= 6 else 2),
        "nome_mes": datas.month.map(lambda m: NOMES_MESES[m]),
    })
