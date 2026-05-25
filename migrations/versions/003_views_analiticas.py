"""Views analíticas para Metabase — schema dw

Cria cinco views somente-leitura que expõem os dados do DW de forma
desnormalizada e pronta para dashboards no Metabase (ou qualquer BI).

Views criadas:
  dw.v_lancamentos_detalhado  — lançamentos com todas as dimensões resolvidas
  dw.v_comparativo_mensal     — realizado × orçado por mês/conta/CC/versão
  dw.v_evolucao_mensal        — totais mensais por tipo de conta (RECEITA/DESPESA)
  dw.v_dre_anual              — DRE com hierarquia, orcado e realizado por conta
  dw.v_workflow_resumo        — status dos workflows com nomes de versão e empresa

Revision ID: 003
Revises: 002
Create Date: 2026-05-01 00:00:00
"""

from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None

# ── helpers ───────────────────────────────────────────────────────────────────

_NOME_MES_CASE = """
    CASE mes_num
        WHEN  1 THEN 'Janeiro'   WHEN  2 THEN 'Fevereiro' WHEN  3 THEN 'Março'
        WHEN  4 THEN 'Abril'     WHEN  5 THEN 'Maio'      WHEN  6 THEN 'Junho'
        WHEN  7 THEN 'Julho'     WHEN  8 THEN 'Agosto'    WHEN  9 THEN 'Setembro'
        WHEN 10 THEN 'Outubro'   WHEN 11 THEN 'Novembro'  WHEN 12 THEN 'Dezembro'
    END
"""


def upgrade() -> None:

    # ── 1. v_lancamentos_detalhado ────────────────────────────────────────────
    op.execute("""
        CREATE OR REPLACE VIEW dw.v_lancamentos_detalhado AS
        SELECT
            lr.id,
            lr.sia_lancamento_id,
            dt.data                     AS data_referencia,
            dt.ano,
            dt.mes,
            dt.nome_mes,
            dt.trimestre,
            dt.semestre,
            e.id                        AS id_empresa,
            e.nome                      AS empresa,
            cs.conta_codigo             AS sia_conta_codigo,
            cs.conta_class              AS sia_conta_class,
            cs.conta_nome               AS sia_conta_nome,
            cg.id                       AS id_conta_gerencial,
            cg.codigo                   AS conta_gerencial_codigo,
            cg.nome                     AS conta_gerencial_nome,
            cg.tipo                     AS conta_tipo,
            cc.id                       AS id_centro_custo,
            cc.codigo                   AS cc_codigo,
            cc.nome                     AS cc_nome,
            lr.tipo_lancamento,
            lr.valor,
            lr.valor * CASE WHEN lr.tipo_lancamento = 'D' THEN 1 ELSE -1 END
                                        AS valor_liquido,
            lr.historico,
            lr.data_carga
        FROM dw.fato_lancamento_realizado lr
        JOIN  dw.dim_tempo           dt ON dt.id  = lr.id_tempo
        JOIN  dw.dim_empresa          e ON  e.id  = lr.id_empresa
        JOIN  dw.dim_conta_sia       cs ON cs.id  = lr.id_conta_sia
        LEFT JOIN dw.dim_conta_gerencial cg ON cg.id = lr.id_conta_gerencial
        LEFT JOIN dw.dim_centro_custo    cc ON cc.id = lr.id_centro_custo
    """)

    # ── 2. v_comparativo_mensal ───────────────────────────────────────────────
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
            fo.ano,
            fo.mes,
            CASE fo.mes
                WHEN  1 THEN 'Janeiro'   WHEN  2 THEN 'Fevereiro' WHEN  3 THEN 'Março'
                WHEN  4 THEN 'Abril'     WHEN  5 THEN 'Maio'      WHEN  6 THEN 'Junho'
                WHEN  7 THEN 'Julho'     WHEN  8 THEN 'Agosto'    WHEN  9 THEN 'Setembro'
                WHEN 10 THEN 'Outubro'   WHEN 11 THEN 'Novembro'  WHEN 12 THEN 'Dezembro'
            END                              AS nome_mes,
            v.id                             AS id_versao,
            v.nome                           AS versao_nome,
            v.tipo                           AS versao_tipo,
            e.id                             AS id_empresa,
            e.nome                           AS empresa_nome,
            cg.id                            AS id_conta_gerencial,
            cg.codigo                        AS conta_codigo,
            cg.nome                          AS conta_nome,
            cg.tipo                          AS conta_tipo,
            cg.natureza                      AS conta_natureza,
            cc.id                            AS id_centro_custo,
            cc.codigo                        AS cc_codigo,
            cc.nome                          AS cc_nome,
            fo.valor                         AS valor_orcado,
            COALESCE(r.valor_realizado, 0)   AS valor_realizado,
            COALESCE(r.valor_realizado, 0) - fo.valor AS variacao_absoluta,
            CASE
                WHEN fo.valor = 0 THEN NULL
                ELSE ROUND(
                    ((COALESCE(r.valor_realizado, 0) - fo.valor) / ABS(fo.valor) * 100)::numeric,
                    2
                )
            END                              AS variacao_percentual
        FROM dw.fato_orcamento fo
        JOIN dw.dim_versao_orcamento  v ON  v.id = fo.id_versao
        JOIN dw.dim_empresa            e ON  e.id = fo.id_empresa
        JOIN dw.dim_conta_gerencial   cg ON cg.id = fo.id_conta_gerencial
        JOIN dw.dim_centro_custo      cc ON cc.id = fo.id_centro_custo
        LEFT JOIN realizado_agg        r
            ON  r.id_empresa         = fo.id_empresa
            AND r.id_conta_gerencial = fo.id_conta_gerencial
            AND r.id_centro_custo    = fo.id_centro_custo
            AND r.ano                = fo.ano
            AND r.mes                = fo.mes
    """)

    # ── 3. v_evolucao_mensal ─────────────────────────────────────────────────
    op.execute("""
        CREATE OR REPLACE VIEW dw.v_evolucao_mensal AS
        SELECT
            dt.ano,
            dt.mes,
            dt.nome_mes,
            dt.trimestre,
            e.id                        AS id_empresa,
            e.nome                      AS empresa,
            cg.tipo                     AS conta_tipo,
            SUM(lr.valor * CASE WHEN lr.tipo_lancamento = 'D' THEN 1 ELSE -1 END)
                                        AS valor_realizado,
            COUNT(DISTINCT lr.sia_lancamento_id) AS qtd_lancamentos
        FROM dw.fato_lancamento_realizado lr
        JOIN dw.dim_tempo           dt ON dt.id = lr.id_tempo
        JOIN dw.dim_empresa          e ON  e.id = lr.id_empresa
        JOIN dw.dim_conta_gerencial cg ON cg.id = lr.id_conta_gerencial
        WHERE lr.id_conta_gerencial IS NOT NULL
        GROUP BY dt.ano, dt.mes, dt.nome_mes, dt.trimestre,
                 e.id, e.nome, cg.tipo
    """)

    # ── 4. v_dre_anual ───────────────────────────────────────────────────────
    op.execute("""
        CREATE OR REPLACE VIEW dw.v_dre_anual AS
        WITH realizado_anual AS (
            SELECT
                id_conta_gerencial,
                id_empresa,
                EXTRACT(YEAR FROM data_referencia)::int AS ano,
                SUM(valor * CASE WHEN tipo_lancamento = 'D' THEN 1 ELSE -1 END)
                    AS valor_realizado
            FROM dw.fato_lancamento_realizado
            WHERE id_conta_gerencial IS NOT NULL
            GROUP BY id_conta_gerencial, id_empresa,
                     EXTRACT(YEAR FROM data_referencia)
        ),
        orcado_anual AS (
            SELECT id_conta_gerencial, id_empresa, id_versao, ano,
                   SUM(valor) AS valor_orcado
            FROM dw.fato_orcamento
            GROUP BY id_conta_gerencial, id_empresa, id_versao, ano
        )
        SELECT
            cg.id                           AS id_conta_gerencial,
            cg.codigo,
            cg.nome,
            cg.tipo,
            cg.natureza,
            cg.nivel,
            cg.id_pai,
            pai.codigo                      AS codigo_pai,
            pai.nome                        AS nome_pai,
            v.id                            AS id_versao,
            v.nome                          AS versao_nome,
            v.ano,
            e.id                            AS id_empresa,
            e.nome                          AS empresa_nome,
            COALESCE(o.valor_orcado, 0)     AS valor_orcado,
            COALESCE(r.valor_realizado, 0)  AS valor_realizado,
            COALESCE(r.valor_realizado, 0) - COALESCE(o.valor_orcado, 0)
                                            AS variacao_absoluta,
            CASE
                WHEN COALESCE(o.valor_orcado, 0) = 0 THEN NULL
                ELSE ROUND(
                    ((COALESCE(r.valor_realizado, 0) - COALESCE(o.valor_orcado, 0))
                     / ABS(COALESCE(o.valor_orcado, 0)) * 100)::numeric,
                    2
                )
            END                             AS variacao_percentual
        FROM dw.dim_conta_gerencial cg
        LEFT JOIN dw.dim_conta_gerencial pai ON pai.id = cg.id_pai
        CROSS JOIN dw.dim_versao_orcamento v
        CROSS JOIN dw.dim_empresa e
        LEFT JOIN orcado_anual  o ON o.id_conta_gerencial = cg.id
                                 AND o.id_empresa         = e.id
                                 AND o.id_versao          = v.id
        LEFT JOIN realizado_anual r ON r.id_conta_gerencial = cg.id
                                   AND r.id_empresa         = e.id
                                   AND r.ano                = v.ano
        WHERE cg.ativa = true
          AND e.ativa  = true
          AND (o.valor_orcado IS NOT NULL OR r.valor_realizado IS NOT NULL)
    """)

    # ── 5. v_workflow_resumo ─────────────────────────────────────────────────
    op.execute("""
        CREATE OR REPLACE VIEW dw.v_workflow_resumo AS
        SELECT
            w.id,
            w.status,
            v.id                    AS id_versao,
            v.nome                  AS versao_nome,
            v.ano                   AS versao_ano,
            v.tipo                  AS versao_tipo,
            v.bloqueada             AS versao_bloqueada,
            e.id                    AS id_empresa,
            e.nome                  AS empresa_nome,
            w.criado_por,
            w.enviado_por,
            w.aprovado_por,
            w.reprovado_por,
            w.data_envio,
            w.data_decisao,
            w.comentario,
            w.criado_em,
            w.atualizado_em,
            CASE
                WHEN w.data_decisao IS NOT NULL AND w.data_envio IS NOT NULL
                THEN ROUND(
                    EXTRACT(EPOCH FROM (w.data_decisao - w.data_envio)) / 3600,
                    1
                )
                ELSE NULL
            END                     AS horas_para_decisao
        FROM dw.workflow_orcamento w
        JOIN dw.dim_versao_orcamento v ON v.id = w.id_versao
        JOIN dw.dim_empresa           e ON  e.id = w.id_empresa
    """)

    # Garante que o metabase_reader tem acesso às novas views
    op.execute("GRANT SELECT ON ALL TABLES IN SCHEMA dw TO metabase_reader")


def downgrade() -> None:
    for view in [
        "dw.v_workflow_resumo",
        "dw.v_dre_anual",
        "dw.v_evolucao_mensal",
        "dw.v_comparativo_mensal",
        "dw.v_lancamentos_detalhado",
    ]:
        op.execute(f"DROP VIEW IF EXISTS {view}")
