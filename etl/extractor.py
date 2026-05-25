"""
Camada de extração do ETL.

IMPORTANTE:
- Conecta ao SIA em modo SOMENTE LEITURA.
- Nunca executar INSERT, UPDATE ou DELETE no SIA.
- Queries transacionais (CTB_MOVIMENTOS, CRC, CPG) filtram por CODEMP.
- CTB_CONTAS e CTB_CCUSTOS NÃO têm CODEMP — filtrar por plano (CON_CODPLA / CC_CODCCPL).
- GER_EMITENTES NÃO tem CODEMP — cadastro global.
- Campos monetários são NUMERIC nativos no Firebird (sem divisão por escala).
"""

import logging
from typing import Generator
import pandas as pd
import pyodbc
from etl.config import ETLConfig

logger = logging.getLogger(__name__)


def _build_sia_connection_string(cfg: ETLConfig) -> str:
    """
    Monta a connection string para o Firebird via ODBC.
    TODO: Ajustar conforme driver instalado (Firebird ODBC / IBPhoenix).
    """
    return (
        f"DRIVER={{Firebird/InterBase(r) driver}};"
        f"DBNAME={cfg.sia_host}/{cfg.sia_port}:{cfg.sia_database};"
        f"UID={cfg.sia_user};"
        f"PWD={cfg.sia_password};"
        "CHARSET=UTF8;"
    )


class SIAExtractor:
    """
    Extrator de dados do SIA (read-only).
    Usa pyodbc + Firebird ODBC driver.
    """

    def __init__(self, cfg: ETLConfig):
        self._cfg = cfg
        self._conn: pyodbc.Connection | None = None

    def connect(self) -> None:
        conn_str = _build_sia_connection_string(self._cfg)
        # Conexão somente leitura: autocommit=False, sem write operations
        self._conn = pyodbc.connect(conn_str, autocommit=False, readonly=True)
        logger.info("Conectado ao SIA (read-only)")

    def disconnect(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("Desconectado do SIA")

    def __enter__(self) -> "SIAExtractor":
        self.connect()
        return self

    def __exit__(self, *_) -> None:
        self.disconnect()

    def _query(self, sql: str, params: dict | None = None) -> pd.DataFrame:
        """Executa query SELECT e retorna DataFrame."""
        if not self._conn:
            raise RuntimeError("Não conectado ao SIA. Use 'with SIAExtractor(cfg):'")
        df = pd.read_sql(sql, self._conn, params=params)
        return df

    # ── Extrações específicas ──────────────────────────────────────────────

    def extrair_empresas(self) -> pd.DataFrame:
        """GER_EMPRESAS — todas as empresas ativas (sem filtro por CODEMP)."""
        from etl.queries.ger import SQL_EMPRESAS
        return self._query(SQL_EMPRESAS)

    def extrair_plano_de_contas(self) -> pd.DataFrame:
        """CTB_CONTAS — plano de contas Philozon (planos 1 e 2).
        Nota: CTB_CONTAS não tem coluna CODEMP — filtrado por CON_CODPLA."""
        from etl.queries.ctb import SQL_PLANO_CONTAS
        return self._query(SQL_PLANO_CONTAS)

    def extrair_centros_custo_sia(self) -> pd.DataFrame:
        """CTB_CCUSTOS — CCs do plano 3 (Philozon & Ozoncare).
        Nota: CTB_CCUSTOS não tem coluna CODEMP — filtrado por CC_CODCCPL."""
        from etl.queries.ctb import SQL_CENTROS_CUSTO
        return self._query(SQL_CENTROS_CUSTO)

    def extrair_lancamentos_contabeis(self, ano: int, mes: int) -> pd.DataFrame:
        """CTB_MOVIMENTOS — lançamentos contábeis de um período."""
        from etl.queries.ctb import SQL_LANCAMENTOS
        return self._query(SQL_LANCAMENTOS, {"codemp": self._cfg.sia_codemp, "ano": ano, "mes": mes})

    def extrair_contas_receber(self, ano: int, mes: int) -> pd.DataFrame:
        """CRC_TITULO + CRC_TITULOPARC — contas a receber."""
        from etl.queries.crc import SQL_CONTAS_RECEBER
        return self._query(SQL_CONTAS_RECEBER, {"codemp": self._cfg.sia_codemp, "ano": ano, "mes": mes})

    def extrair_contas_pagar(self, ano: int, mes: int) -> pd.DataFrame:
        """CPG_TITULO — contas a pagar."""
        from etl.queries.cpg import SQL_CONTAS_PAGAR
        return self._query(SQL_CONTAS_PAGAR, {"codemp": self._cfg.sia_codemp, "ano": ano, "mes": mes})

    def extrair_receitas(self, ano: int, mes: int) -> pd.DataFrame:
        """EST_VENDA / FIS_MOVIMENTO — receitas brutas."""
        from etl.queries.fis import SQL_RECEITAS
        return self._query(SQL_RECEITAS, {"codemp": self._cfg.sia_codemp, "ano": ano, "mes": mes})
