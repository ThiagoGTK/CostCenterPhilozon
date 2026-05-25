"""
Camada de carga do ETL — carga idempotente no Data Warehouse.

Regra de idempotência: executar o pipeline duas vezes com os mesmos
dados de entrada deve produzir o mesmo estado no DW (sem duplicatas).
Estratégia: INSERT ... ON CONFLICT DO UPDATE (upsert) usando a chave de negócio.
"""

import logging
from decimal import Decimal
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


class DWLoader:
    def __init__(self, engine: Engine):
        self._engine = engine

    # ── Dimensões ──────────────────────────────────────────────────────────

    def upsert_dim_tempo(self, df: pd.DataFrame) -> int:
        """Insere ou ignora datas na dim_tempo. Chave: data."""
        if df.empty:
            return 0
        sql = text("""
            INSERT INTO dw.dim_tempo (data, ano, mes, trimestre, semestre, nome_mes)
            VALUES (:data, :ano, :mes, :trimestre, :semestre, :nome_mes)
            ON CONFLICT (data) DO NOTHING
        """)
        with self._engine.begin() as conn:
            result = conn.execute(sql, df.to_dict("records"))
        inserted = result.rowcount
        logger.info("dim_tempo: %d registros inseridos", inserted)
        return inserted

    def upsert_dim_empresa(self, records: list[dict]) -> int:
        sql = text("""
            INSERT INTO dw.dim_empresa (codemp, nome, cnpj, ativa)
            VALUES (:codemp, :nome, :cnpj, :ativa)
            ON CONFLICT (codemp) DO UPDATE SET
                nome  = EXCLUDED.nome,
                cnpj  = EXCLUDED.cnpj,
                ativa = EXCLUDED.ativa
        """)
        with self._engine.begin() as conn:
            result = conn.execute(sql, records)
        logger.info("dim_empresa: %d registros processados", result.rowcount)
        return result.rowcount

    def upsert_dim_conta_sia(self, records: list[dict]) -> int:
        """Chave de negócio: codemp + conta_codigo."""
        sql = text("""
            INSERT INTO dw.dim_conta_sia (codemp, conta_codigo, conta_nome, conta_tipo, conta_nivel)
            VALUES (:codemp, :conta_codigo, :conta_nome, :conta_tipo, :conta_nivel)
            ON CONFLICT (codemp, conta_codigo) DO UPDATE SET
                conta_nome  = EXCLUDED.conta_nome,
                conta_tipo  = EXCLUDED.conta_tipo,
                conta_nivel = EXCLUDED.conta_nivel
        """)
        # TODO: adicionar constraint UNIQUE(codemp, conta_codigo) na migration
        with self._engine.begin() as conn:
            result = conn.execute(sql, records)
        logger.info("dim_conta_sia: %d registros processados", result.rowcount)
        return result.rowcount

    # ── Fatos ──────────────────────────────────────────────────────────────

    def upsert_fato_lancamento_realizado(self, records: list[dict]) -> int:
        """
        Idempotência via sia_lancamento_id (chave única de negócio).
        Em caso de conflito, atualiza o valor (re-run seguro após correção no SIA).
        """
        if not records:
            return 0

        sql = text("""
            INSERT INTO dw.fato_lancamento_realizado
                (id_empresa, id_tempo, id_conta_sia, id_conta_gerencial, id_centro_custo,
                 sia_lancamento_id, valor, tipo_lancamento, historico, data_referencia)
            VALUES
                (:id_empresa, :id_tempo, :id_conta_sia, :id_conta_gerencial, :id_centro_custo,
                 :sia_lancamento_id, :valor, :tipo_lancamento, :historico, :data_referencia)
            ON CONFLICT (sia_lancamento_id) DO UPDATE SET
                valor           = EXCLUDED.valor,
                tipo_lancamento = EXCLUDED.tipo_lancamento,
                historico       = EXCLUDED.historico,
                data_carga      = now()
        """)
        with self._engine.begin() as conn:
            result = conn.execute(sql, records)
        logger.info("fato_lancamento_realizado: %d registros processados", result.rowcount)
        return result.rowcount

    def upsert_fato_receita(self, records: list[dict]) -> int:
        """Idempotência via chave_upsert."""
        if not records:
            return 0
        sql = text("""
            INSERT INTO dw.fato_receita
                (id_empresa, id_tempo, id_cliente, chave_upsert,
                 receita_bruta, deducoes, receita_liquida)
            VALUES
                (:id_empresa, :id_tempo, :id_cliente, :chave_upsert,
                 :receita_bruta, :deducoes, :receita_liquida)
            ON CONFLICT (chave_upsert) DO UPDATE SET
                receita_bruta   = EXCLUDED.receita_bruta,
                deducoes        = EXCLUDED.deducoes,
                receita_liquida = EXCLUDED.receita_liquida,
                data_carga      = now()
        """)
        with self._engine.begin() as conn:
            result = conn.execute(sql, records)
        logger.info("fato_receita: %d registros processados", result.rowcount)
        return result.rowcount
