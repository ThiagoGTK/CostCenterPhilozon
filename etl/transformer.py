"""
Camada de transformação do ETL.

Responsabilidades:
- Garantir tipos Decimal para todos os campos monetários.
- Aplicar mapeamentos SIA → gerencial.
- Enriquecer com dimensões de tempo.
- Calcular chave de idempotência para upsert.
"""

import logging
from decimal import Decimal
from datetime import date
import pandas as pd

logger = logging.getLogger(__name__)

# MOV_TIPO em CTB_MOVIMENTOS
MOV_TIPO_DEBITO = 1
MOV_TIPO_CREDITO = 2
# Tipos 3 (encerramento de exercício) e 4 (transferência entre contas) são
# excluídos diretamente na query SQL — não chegam ao transformer.

_MOV_TIPO_LABEL: dict[int, str] = {
    1: "D",  # Débito
    2: "C",  # Crédito
}


def sia_decimal(valor) -> Decimal:
    """
    Converte campo monetário do SIA para Decimal.
    MOV_VALOR, TIT_VAL, TITPAR_VAL etc. já são NUMERIC nativos no Firebird —
    não há divisão por escala. Apenas garante o tipo Python correto.
    """
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return Decimal("0")
    return Decimal(str(valor))


def normalizar_coluna_monetaria(df: pd.DataFrame, coluna: str) -> pd.DataFrame:
    """Converte coluna de valores monetários do SIA para Decimal."""
    df[coluna] = df[coluna].apply(sia_decimal)
    return df


# Mantida por compatibilidade com testes existentes.
# tabela_campo ignorado — SIA usa NUMERIC nativo sem escala.
def normalizar_valor_monetario(valor, tabela_campo: str = "") -> Decimal:
    return sia_decimal(valor)


def transformar_lancamentos_contabeis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforma lançamentos contábeis do CTB_MOVIMENTOS.

    Colunas esperadas:
        MOV_CODEMP, MOV_NUMLAN, MOV_DATA, MOV_CODCON,
        MOV_CECT, MOV_TIPO, MOV_VALOR, MOV_HIST
    """
    if df.empty:
        return df

    df = df.copy()

    # Garantir Decimal no valor (já é NUMERIC no Firebird, mas pyodbc pode
    # retornar float em alguns drivers)
    df = normalizar_coluna_monetaria(df, "MOV_VALOR")

    # Chave de idempotência: empresa + data + lançamento + conta + tipo
    # MOV_NUMLAN é sequencial por empresa/data — não é globalmente único sozinho
    df["sia_lancamento_id"] = (
        df["MOV_CODEMP"].astype(str) + "_"
        + df["MOV_DATA"].astype(str) + "_"
        + df["MOV_NUMLAN"].astype(str) + "_"
        + df["MOV_CODCON"].astype(str) + "_"
        + df["MOV_TIPO"].astype(str)
    )

    # Traduz inteiro para 'D'/'C' (padrão interno do DW)
    df["tipo_lancamento"] = df["MOV_TIPO"].map(_MOV_TIPO_LABEL)

    # MOV_CECT pode ser NULL — normalizar para string vazia
    df["MOV_CECT"] = df["MOV_CECT"].fillna("").astype(str)

    df = df.rename(columns={
        "MOV_CODEMP": "codemp",
        "MOV_NUMLAN": "numlan",
        "MOV_DATA":   "data_referencia",
        "MOV_CODCON": "conta_sia_codigo",
        "MOV_CECT":   "cc_sia_codigo",
        "MOV_VALOR":  "valor",
        "MOV_HIST":   "historico",
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
        "data":       datas.date,
        "ano":        datas.year,
        "mes":        datas.month,
        "trimestre":  datas.quarter,
        "semestre":   datas.month.map(lambda m: 1 if m <= 6 else 2),
        "nome_mes":   datas.month.map(lambda m: NOMES_MESES[m]),
    })
