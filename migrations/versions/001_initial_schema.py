"""Initial schema — schemas dw e app, todas as tabelas do MVP

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00
"""

from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Garantir que os schemas existem
    op.execute("CREATE SCHEMA IF NOT EXISTS dw")
    op.execute("CREATE SCHEMA IF NOT EXISTS app")

    # ── dim_empresa ────────────────────────────────────────────────────────
    op.create_table(
        "dim_empresa",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("codemp", sa.Integer, nullable=False),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("cnpj", sa.String(18)),
        sa.Column("ativa", sa.Boolean, default=True),
        schema="dw",
    )
    op.create_unique_constraint("uq_dim_empresa_codemp", "dim_empresa", ["codemp"], schema="dw")

    # ── dim_tempo ──────────────────────────────────────────────────────────
    op.create_table(
        "dim_tempo",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("data", sa.Date, nullable=False),
        sa.Column("ano", sa.SmallInteger, nullable=False),
        sa.Column("mes", sa.SmallInteger, nullable=False),
        sa.Column("trimestre", sa.SmallInteger, nullable=False),
        sa.Column("semestre", sa.SmallInteger, nullable=False),
        sa.Column("nome_mes", sa.String(20), nullable=False),
        schema="dw",
    )
    op.create_unique_constraint("uq_dim_tempo_data", "dim_tempo", ["data"], schema="dw")

    # ── dim_centro_custo ───────────────────────────────────────────────────
    op.create_table(
        "dim_centro_custo",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("codigo", sa.String(50), nullable=False),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("descricao", sa.Text),
        sa.Column("id_pai", sa.Integer, sa.ForeignKey("dw.dim_centro_custo.id")),
        sa.Column("ativo", sa.Boolean, default=True),
        schema="dw",
    )
    op.create_unique_constraint("uq_dim_cc_codigo", "dim_centro_custo", ["codigo"], schema="dw")

    # ── dim_conta_gerencial ────────────────────────────────────────────────
    op.create_table(
        "dim_conta_gerencial",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("codigo", sa.String(50), nullable=False),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("tipo", sa.String(30), nullable=False),
        sa.Column("natureza", sa.String(10), nullable=False),
        sa.Column("id_pai", sa.Integer, sa.ForeignKey("dw.dim_conta_gerencial.id")),
        sa.Column("nivel", sa.SmallInteger, default=1),
        sa.Column("aceita_lancamento", sa.Boolean, default=True),
        sa.Column("ativa", sa.Boolean, default=True),
        schema="dw",
    )
    op.create_unique_constraint("uq_dim_cg_codigo", "dim_conta_gerencial", ["codigo"], schema="dw")

    # ── dim_conta_sia ──────────────────────────────────────────────────────
    op.create_table(
        "dim_conta_sia",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("codemp", sa.Integer, nullable=False),
        sa.Column("conta_codigo", sa.String(50), nullable=False),
        sa.Column("conta_nome", sa.String(200), nullable=False),
        sa.Column("conta_tipo", sa.String(10)),
        sa.Column("conta_nivel", sa.SmallInteger),
        schema="dw",
    )
    op.create_unique_constraint("uq_dim_conta_sia", "dim_conta_sia", ["codemp", "conta_codigo"], schema="dw")

    # ── dim_cliente ────────────────────────────────────────────────────────
    op.create_table(
        "dim_cliente",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("codemp", sa.Integer, nullable=False),
        sa.Column("cod_sia", sa.Integer, nullable=False),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("cnpj_cpf", sa.String(18)),
        sa.Column("ativo", sa.Boolean, default=True),
        schema="dw",
    )

    # ── dim_fornecedor ─────────────────────────────────────────────────────
    op.create_table(
        "dim_fornecedor",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("codemp", sa.Integer, nullable=False),
        sa.Column("cod_sia", sa.Integer, nullable=False),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("cnpj_cpf", sa.String(18)),
        sa.Column("ativo", sa.Boolean, default=True),
        schema="dw",
    )

    # ── dim_versao_orcamento ───────────────────────────────────────────────
    op.create_table(
        "dim_versao_orcamento",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ano", sa.SmallInteger, nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("nome", sa.String(100), nullable=False),
        sa.Column("descricao", sa.Text),
        sa.Column("data_criacao", sa.Date, nullable=False),
        sa.Column("bloqueada", sa.Boolean, default=False),
        schema="dw",
    )

    # ── fato_lancamento_realizado ──────────────────────────────────────────
    op.create_table(
        "fato_lancamento_realizado",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("id_empresa", sa.Integer, sa.ForeignKey("dw.dim_empresa.id"), nullable=False),
        sa.Column("id_tempo", sa.Integer, sa.ForeignKey("dw.dim_tempo.id"), nullable=False),
        sa.Column("id_conta_sia", sa.Integer, sa.ForeignKey("dw.dim_conta_sia.id"), nullable=False),
        sa.Column("id_conta_gerencial", sa.Integer, sa.ForeignKey("dw.dim_conta_gerencial.id")),
        sa.Column("id_centro_custo", sa.Integer, sa.ForeignKey("dw.dim_centro_custo.id")),
        sa.Column("sia_lancamento_id", sa.String(100), nullable=False),
        sa.Column("valor", sa.NUMERIC(15, 2), nullable=False),
        sa.Column("tipo_lancamento", sa.String(1), nullable=False),
        sa.Column("historico", sa.String(500)),
        sa.Column("data_referencia", sa.Date, nullable=False),
        sa.Column("data_carga", sa.DateTime, server_default=sa.func.now()),
        schema="dw",
    )
    op.create_unique_constraint(
        "uq_fato_lanc_sia_id", "fato_lancamento_realizado", ["sia_lancamento_id"], schema="dw"
    )
    op.create_index(
        "ix_fato_lanc_data", "fato_lancamento_realizado", ["data_referencia"], schema="dw"
    )

    # ── fato_orcamento ─────────────────────────────────────────────────────
    op.create_table(
        "fato_orcamento",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("id_empresa", sa.Integer, sa.ForeignKey("dw.dim_empresa.id"), nullable=False),
        sa.Column("id_versao", sa.Integer, sa.ForeignKey("dw.dim_versao_orcamento.id"), nullable=False),
        sa.Column("id_conta_gerencial", sa.Integer, sa.ForeignKey("dw.dim_conta_gerencial.id"), nullable=False),
        sa.Column("id_centro_custo", sa.Integer, sa.ForeignKey("dw.dim_centro_custo.id"), nullable=False),
        sa.Column("ano", sa.SmallInteger, nullable=False),
        sa.Column("mes", sa.SmallInteger, nullable=False),
        sa.Column("valor", sa.NUMERIC(15, 2), nullable=False),
        sa.Column("observacao", sa.Text),
        sa.Column("criado_por", sa.String(100)),
        sa.Column("criado_em", sa.DateTime, server_default=sa.func.now()),
        sa.Column("atualizado_em", sa.DateTime, server_default=sa.func.now()),
        schema="dw",
    )

    # ── fato_receita ───────────────────────────────────────────────────────
    op.create_table(
        "fato_receita",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("id_empresa", sa.Integer, sa.ForeignKey("dw.dim_empresa.id"), nullable=False),
        sa.Column("id_tempo", sa.Integer, sa.ForeignKey("dw.dim_tempo.id"), nullable=False),
        sa.Column("id_cliente", sa.Integer, sa.ForeignKey("dw.dim_cliente.id")),
        sa.Column("chave_upsert", sa.String(100), nullable=False),
        sa.Column("receita_bruta", sa.NUMERIC(15, 2), nullable=False, server_default="0"),
        sa.Column("deducoes", sa.NUMERIC(15, 2), nullable=False, server_default="0"),
        sa.Column("receita_liquida", sa.NUMERIC(15, 2), nullable=False, server_default="0"),
        sa.Column("data_carga", sa.DateTime, server_default=sa.func.now()),
        schema="dw",
    )
    op.create_unique_constraint("uq_fato_receita_chave", "fato_receita", ["chave_upsert"], schema="dw")

    # ── fato_despesa ───────────────────────────────────────────────────────
    op.create_table(
        "fato_despesa",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("id_empresa", sa.Integer, sa.ForeignKey("dw.dim_empresa.id"), nullable=False),
        sa.Column("id_tempo", sa.Integer, sa.ForeignKey("dw.dim_tempo.id"), nullable=False),
        sa.Column("id_conta_gerencial", sa.Integer, sa.ForeignKey("dw.dim_conta_gerencial.id"), nullable=False),
        sa.Column("id_centro_custo", sa.Integer, sa.ForeignKey("dw.dim_centro_custo.id")),
        sa.Column("chave_upsert", sa.String(200), nullable=False),
        sa.Column("valor", sa.NUMERIC(15, 2), nullable=False),
        sa.Column("data_carga", sa.DateTime, server_default=sa.func.now()),
        schema="dw",
    )
    op.create_unique_constraint("uq_fato_despesa_chave", "fato_despesa", ["chave_upsert"], schema="dw")

    # ── workflow_orcamento ─────────────────────────────────────────────────
    op.create_table(
        "workflow_orcamento",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("id_versao", sa.Integer, sa.ForeignKey("dw.dim_versao_orcamento.id"), nullable=False),
        sa.Column("id_empresa", sa.Integer, sa.ForeignKey("dw.dim_empresa.id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="RASCUNHO"),
        sa.Column("criado_por", sa.String(100), nullable=False),
        sa.Column("enviado_por", sa.String(100)),
        sa.Column("aprovado_por", sa.String(100)),
        sa.Column("reprovado_por", sa.String(100)),
        sa.Column("data_envio", sa.DateTime),
        sa.Column("data_decisao", sa.DateTime),
        sa.Column("comentario", sa.Text),
        sa.Column("criado_em", sa.DateTime, server_default=sa.func.now()),
        sa.Column("atualizado_em", sa.DateTime, server_default=sa.func.now()),
        schema="dw",
    )

    # ── justificativa_variacao ─────────────────────────────────────────────
    op.create_table(
        "justificativa_variacao",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("id_empresa", sa.Integer, sa.ForeignKey("dw.dim_empresa.id"), nullable=False),
        sa.Column("id_versao", sa.Integer, sa.ForeignKey("dw.dim_versao_orcamento.id"), nullable=False),
        sa.Column("id_conta_gerencial", sa.Integer, sa.ForeignKey("dw.dim_conta_gerencial.id"), nullable=False),
        sa.Column("id_centro_custo", sa.Integer, sa.ForeignKey("dw.dim_centro_custo.id"), nullable=False),
        sa.Column("ano", sa.Integer, nullable=False),
        sa.Column("mes", sa.Integer, nullable=False),
        sa.Column("valor_orcado", sa.NUMERIC(15, 2), nullable=False),
        sa.Column("valor_realizado", sa.NUMERIC(15, 2), nullable=False),
        sa.Column("variacao_absoluta", sa.NUMERIC(15, 2), nullable=False),
        sa.Column("variacao_percentual", sa.NUMERIC(8, 2), nullable=False),
        sa.Column("justificativa", sa.Text, nullable=False),
        sa.Column("criado_por", sa.String(100), nullable=False),
        sa.Column("criado_em", sa.DateTime, server_default=sa.func.now()),
        schema="dw",
    )

    # ── mapeamentos ────────────────────────────────────────────────────────
    op.create_table(
        "mapeamento_conta_sia_gerencial",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("id_conta_sia", sa.Integer, sa.ForeignKey("dw.dim_conta_sia.id"), nullable=False),
        sa.Column("id_conta_gerencial", sa.Integer, sa.ForeignKey("dw.dim_conta_gerencial.id"), nullable=False),
        sa.Column("id_empresa", sa.Integer, sa.ForeignKey("dw.dim_empresa.id"), nullable=False),
        sa.Column("ativo", sa.Boolean, default=True),
        sa.Column("observacao", sa.Text),
        schema="dw",
    )

    op.create_table(
        "mapeamento_centro_custo_sia_gerencial",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("cc_sia_codigo", sa.String(50), nullable=False),
        sa.Column("cc_sia_nome", sa.String(200)),
        sa.Column("id_empresa", sa.Integer, sa.ForeignKey("dw.dim_empresa.id"), nullable=False),
        sa.Column("id_centro_custo_gerencial", sa.Integer, sa.ForeignKey("dw.dim_centro_custo.id"), nullable=False),
        sa.Column("ativo", sa.Boolean, default=True),
        sa.Column("observacao", sa.Text),
        schema="dw",
    )


def downgrade() -> None:
    # Remove tudo na ordem inversa (respeita FKs)
    tables = [
        "mapeamento_centro_custo_sia_gerencial",
        "mapeamento_conta_sia_gerencial",
        "justificativa_variacao",
        "workflow_orcamento",
        "fato_despesa",
        "fato_receita",
        "fato_orcamento",
        "fato_lancamento_realizado",
        "dim_versao_orcamento",
        "dim_fornecedor",
        "dim_cliente",
        "dim_conta_sia",
        "dim_conta_gerencial",
        "dim_centro_custo",
        "dim_tempo",
        "dim_empresa",
    ]
    for table in tables:
        op.drop_table(table, schema="dw")
