"""
Camada de carga do ETL — carga idempotente no Data Warehouse.

Regra de idempotência: executar o pipeline duas vezes com os mesmos
dados de entrada deve produzir o mesmo estado no DW (sem duplicatas).
Estratégia: INSERT ... ON CONFLICT DO UPDATE (upsert) usando a chave de negócio.
"""

import logging
from decimal import Decimal
from datetime import date
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
        logger.info("dim_tempo: %d registros inseridos", result.rowcount)
        return result.rowcount

    def upsert_dim_empresa(self, records: list[dict]) -> int:
        """Chave: codemp. Atualiza nome, cnpj e ativa em conflito."""
        if not records:
            return 0
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
        """
        Chave: (codpla, conta_codigo).
        conta_codigo = CON_COD (inteiro como string).
        conta_class  = CON_CLASS (código hierárquico legível).
        """
        if not records:
            return 0
        sql = text("""
            INSERT INTO dw.dim_conta_sia
                (codpla, conta_codigo, conta_class, conta_codsup,
                 conta_nome, conta_tipo, conta_nivel)
            VALUES
                (:codpla, :conta_codigo, :conta_class, :conta_codsup,
                 :conta_nome, :conta_tipo, :conta_nivel)
            ON CONFLICT (codpla, conta_codigo) DO UPDATE SET
                conta_class  = EXCLUDED.conta_class,
                conta_codsup = EXCLUDED.conta_codsup,
                conta_nome   = EXCLUDED.conta_nome,
                conta_tipo   = EXCLUDED.conta_tipo,
                conta_nivel  = EXCLUDED.conta_nivel
        """)
        with self._engine.begin() as conn:
            result = conn.execute(sql, records)
        logger.info("dim_conta_sia: %d registros processados", result.rowcount)
        return result.rowcount

    def upsert_dim_cliente(self, records: list[dict]) -> int:
        """Chave: (codemp, cod_sia)."""
        if not records:
            return 0
        sql = text("""
            INSERT INTO dw.dim_cliente (codemp, cod_sia, nome, cnpj_cpf, ativo)
            VALUES (:codemp, :cod_sia, :nome, :cnpj_cpf, :ativo)
            ON CONFLICT (codemp, cod_sia) DO UPDATE SET
                nome     = EXCLUDED.nome,
                cnpj_cpf = EXCLUDED.cnpj_cpf,
                ativo    = EXCLUDED.ativo
        """)
        with self._engine.begin() as conn:
            result = conn.execute(sql, records)
        logger.info("dim_cliente: %d registros processados", result.rowcount)
        return result.rowcount

    def upsert_dim_fornecedor(self, records: list[dict]) -> int:
        """Chave: cod_sia. GER_EMITENTES é cadastro global (sem CODEMP)."""
        if not records:
            return 0
        sql = text("""
            INSERT INTO dw.dim_fornecedor (cod_sia, nome, nome_fantasia, cnpj_cpf, ativo)
            VALUES (:cod_sia, :nome, :nome_fantasia, :cnpj_cpf, :ativo)
            ON CONFLICT (cod_sia) DO UPDATE SET
                nome         = EXCLUDED.nome,
                nome_fantasia = EXCLUDED.nome_fantasia,
                cnpj_cpf     = EXCLUDED.cnpj_cpf,
                ativo        = EXCLUDED.ativo
        """)
        with self._engine.begin() as conn:
            result = conn.execute(sql, records)
        logger.info("dim_fornecedor: %d registros processados", result.rowcount)
        return result.rowcount

    # ── Resolvedores de FK ─────────────────────────────────────────────────

    def resolver_ids_empresa(self, codemp_list: list[int]) -> dict[int, int]:
        """Retorna {codemp → id} para os codigos fornecidos."""
        if not codemp_list:
            return {}
        sql = text("SELECT id, codemp FROM dw.dim_empresa WHERE codemp = ANY(:vals)")
        with self._engine.connect() as conn:
            rows = conn.execute(sql, {"vals": codemp_list}).fetchall()
        return {row[1]: row[0] for row in rows}

    def resolver_ids_tempo(self, datas: list[date]) -> dict[str, int]:
        """Retorna {data_str → id} para as datas fornecidas."""
        if not datas:
            return {}
        # Converter para string ISO para garantir comparação correta
        datas_str = [d.isoformat() if hasattr(d, "isoformat") else str(d) for d in datas]
        sql = text("SELECT id, data::text FROM dw.dim_tempo WHERE data::text = ANY(:vals)")
        with self._engine.connect() as conn:
            rows = conn.execute(sql, {"vals": datas_str}).fetchall()
        return {row[1]: row[0] for row in rows}

    def resolver_ids_conta_sia(self, conta_codigos: list[str]) -> dict[str, int]:
        """
        Retorna {conta_codigo → id}.
        Como podem existir contas com mesmo CON_COD em planos diferentes,
        retorna o primeiro match (plano mais recente = maior codpla).
        """
        if not conta_codigos:
            return {}
        sql = text("""
            SELECT DISTINCT ON (conta_codigo) id, conta_codigo
            FROM dw.dim_conta_sia
            WHERE conta_codigo = ANY(:vals)
            ORDER BY conta_codigo, codpla DESC
        """)
        with self._engine.connect() as conn:
            rows = conn.execute(sql, {"vals": conta_codigos}).fetchall()
        return {row[1]: row[0] for row in rows}

    def resolver_mapeamentos_conta(self, id_empresa: int) -> dict[str, int]:
        """
        Retorna {conta_codigo → id_conta_gerencial} para mapeamentos ativos.
        Usado pelo pipeline para popular id_conta_gerencial em fato_lancamento_realizado.
        """
        sql = text("""
            SELECT cs.conta_codigo, m.id_conta_gerencial
            FROM dw.mapeamento_conta_sia_gerencial m
            JOIN dw.dim_conta_sia cs ON cs.id = m.id_conta_sia
            WHERE m.id_empresa = :id_empresa
              AND m.ativo = true
        """)
        with self._engine.connect() as conn:
            rows = conn.execute(sql, {"id_empresa": id_empresa}).fetchall()
        return {row[0]: row[1] for row in rows}

    def resolver_mapeamentos_cc(self, id_empresa: int) -> dict[str, int]:
        """
        Retorna {cc_sia_codigo → id_centro_custo} para mapeamentos ativos.
        Usado pelo pipeline para popular id_centro_custo em fato_lancamento_realizado.
        """
        sql = text("""
            SELECT cc_sia_codigo, id_centro_custo_gerencial
            FROM dw.mapeamento_centro_custo_sia_gerencial
            WHERE id_empresa = :id_empresa
              AND ativo = true
        """)
        with self._engine.connect() as conn:
            rows = conn.execute(sql, {"id_empresa": id_empresa}).fetchall()
        return {row[0]: row[1] for row in rows}

    # ── Fatos ──────────────────────────────────────────────────────────────

    def upsert_fato_lancamento_realizado(self, records: list[dict]) -> int:
        """
        Idempotência via sia_lancamento_id (chave única de negócio).
        Em caso de conflito, atualiza valor e historico (corrigível no SIA).
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
