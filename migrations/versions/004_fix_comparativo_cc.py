"""Fix v_comparativo_mensal — remover join por centro de custo

Todos os lançamentos do SIA têm MOV_CECT = NULL, portanto
id_centro_custo em fato_lancamento_realizado é sempre NULL.
O realizado_agg original filtrava AND id_centro_custo IS NOT NULL,
excluindo 100% dos lançamentos, e o JOIN exigia r.id_centro_custo = fo.id_centro_custo,
que nunca casava com NULL — valor_realizado era sempre zero.

Correção:
  • realizado_agg agrega por (conta, empresa, ano, mes) sem CC
  • fato_orcamento é agregado somando todos os CCs por conta-mes
  • JOIN usa apenas conta + empresa + período
  • Colunas id_centro_custo / cc_codigo / cc_nome removidas da view

Revision ID: 004
Revises: 003
Create Date: 2026-05-25 00:00:00
"""

from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE OR REPLACE VIEW dw.v_comparativo_mensal AS
        WITH realizado_agg AS (
            -- Agrega realizado por conta+empresa+período ignorando CC
            -- (MOV_CECT = NULL em todos os lançamentos do SIA)
            SELECT
                id_empresa,
                id_conta_gerencial,
                EXTRACT(YEAR  FROM data_referencia)::int AS ano,
                EXTRACT(MONTH FROM data_referencia)::int AS mes,
                SUM(valor * CASE WHEN tipo_lancamento = 'D' THEN 1 ELSE -1 END)
                    AS valor_realizado
            FROM dw.fato_lancamento_realizado
            WHERE id_conta_gerencial IS NOT NULL
            GROUP BY id_empresa, id_conta_gerencial,
                     EXTRACT(YEAR  FROM data_referencia),
                     EXTRACT(MONTH FROM data_referencia)
        )
        SELECT
            fo.ano,
            fo.mes,
            CASE fo.mes
                WHEN  1 THEN 'Janeiro'   WHEN  2 THEN 'Fevereiro' WHEN  3 THEN 'Março'
                WHEN  4 THEN 'Abril'     WHEN  5 THEN 'Maio'      WHEN  6 THEN 'Junho'
                WHEN  7 THEN 'Julho'     WHEN  8 THEN 'Agosto'    WHEN  9 THEN 'Setembro'
                WHEN 10 THEN 'Outubro'   WHEN 11 THEN 'Novembro'  WHEN 12 THEN 'Dezembro'
            END                                 AS nome_mes,
            v.id                                AS id_versao,
            v.nome                              AS versao_nome,
            v.tipo                              AS versao_tipo,
            e.id                                AS id_empresa,
            e.nome                              AS empresa_nome,
            cg.id                               AS id_conta_gerencial,
            cg.codigo                           AS conta_codigo,
            cg.nome                             AS conta_nome,
            cg.tipo                             AS conta_tipo,
            cg.natureza                         AS conta_natureza,
            SUM(fo.valor)                       AS valor_orcado,
            COALESCE(MAX(r.valor_realizado), 0) AS valor_realizado,
            COALESCE(MAX(r.valor_realizado), 0) - SUM(fo.valor)
                                                AS variacao_absoluta,
            CASE
                WHEN SUM(fo.valor) = 0 THEN NULL
                ELSE ROUND(
                    ((COALESCE(MAX(r.valor_realizado), 0) - SUM(fo.valor))
                     / ABS(SUM(fo.valor)) * 100)::numeric,
                    2
                )
            END                                 AS variacao_percentual
        FROM dw.fato_orcamento fo
        JOIN dw.dim_versao_orcamento  v ON  v.id = fo.id_versao
        JOIN dw.dim_empresa            e ON  e.id = fo.id_empresa
        JOIN dw.dim_conta_gerencial   cg ON cg.id = fo.id_conta_gerencial
        LEFT JOIN realizado_agg        r
            ON  r.id_empresa         = fo.id_empresa
            AND r.id_conta_gerencial = fo.id_conta_gerencial
            AND r.ano                = fo.ano
            AND r.mes                = fo.mes
        GROUP BY
            fo.ano, fo.mes,
            v.id, v.nome, v.tipo,
            e.id, e.nome,
            cg.id, cg.codigo, cg.nome, cg.tipo, cg.natureza
    """)

    op.execute("GRANT SELECT ON ALL TABLES IN SCHEMA dw TO metabase_reader")


def downgrade() -> None:
    # Restaura a versão original (com o bug de CC) — apenas para rollback de emergência
    op.execute("""
        CREATE OR REPLACE VIEW dw.v_comparativo_mensal AS
        WITH realizado_agg AS (
            SELECT
                id_empresa,
                id_conta_gerencial,
                id_centro_custo,
                EXTRACT(YEAR  FROM data_referencia)::int AS ano,
                EXTRACT(MONTH FROM data_referencia)::int AS mes,
                SUM(valor * CASE WHEN tipo_lancamento = 'D' THEN 1 ELSE -1 END)
                    AS valor_realizado
            FROM dw.fato_lancamento_realizado
            WHERE id_conta_gerencial IS NOT NULL
              AND id_centro_custo    IS NOT NULL
            GROUP BY id_empresa, id_conta_gerencial, id_centro_custo,
                     EXTRACT(YEAR  FROM data_referencia),
                     EXTRACT(MONTH FROM data_referencia)
        )
        SELECT
            fo.ano, fo.mes,
            v.id AS id_versao, v.nome AS versao_nome,
            e.id AS id_empresa, e.nome AS empresa_nome,
            cg.id AS id_conta_gerencial, cg.codigo AS conta_codigo, cg.nome AS conta_nome,
            cc.id AS id_centro_custo, cc.codigo AS cc_codigo, cc.nome AS cc_nome,
            fo.valor AS valor_orcado,
            COALESCE(r.valor_realizado, 0) AS valor_realizado,
            COALESCE(r.valor_realizado, 0) - fo.valor AS variacao_absoluta,
            NULL::numeric AS variacao_percentual
        FROM dw.fato_orcamento fo
        JOIN dw.dim_versao_orcamento  v ON v.id = fo.id_versao
        JOIN dw.dim_empresa            e ON e.id = fo.id_empresa
        JOIN dw.dim_conta_gerencial   cg ON cg.id = fo.id_conta_gerencial
        JOIN dw.dim_centro_custo      cc ON cc.id = fo.id_centro_custo
        LEFT JOIN realizado_agg        r
            ON  r.id_empresa = fo.id_empresa
            AND r.id_conta_gerencial = fo.id_conta_gerencial
            AND r.id_centro_custo = fo.id_centro_custo
            AND r.ano = fo.ano AND r.mes = fo.mes
    """)
