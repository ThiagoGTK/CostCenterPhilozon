"""Fix dim_conta_sia (codemp→codpla, add conta_class) e dim_fornecedor (remove codemp)

CTB_CONTAS não tem CODEMP — usa CON_CODPLA (plano) como identificador de empresa.
GER_EMITENTES não tem CODEMP — cadastro global de fornecedores.

Revision ID: 002
Revises: 001
Create Date: 2026-05-25
"""

from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── dim_conta_sia ──────────────────────────────────────────────────────
    # CTB_CONTAS não tem CODEMP — o isolamento de empresa é feito por CON_CODPLA.
    # Renomear codemp → codpla e adicionar conta_class (CON_CLASS do SIA).
    op.drop_constraint("uq_dim_conta_sia", "dim_conta_sia", schema="dw", type_="unique")
    op.alter_column("dim_conta_sia", "codemp", new_column_name="codpla", schema="dw")
    op.add_column(
        "dim_conta_sia",
        sa.Column("conta_class", sa.String(50), nullable=True),
        schema="dw",
    )
    op.add_column(
        "dim_conta_sia",
        sa.Column("conta_codsup", sa.Integer, nullable=True, comment="CON_CODSUP — conta pai"),
        schema="dw",
    )
    op.create_unique_constraint(
        "uq_dim_conta_sia", "dim_conta_sia", ["codpla", "conta_codigo"], schema="dw"
    )

    # ── dim_fornecedor ─────────────────────────────────────────────────────
    # GER_EMITENTES não tem CODEMP — cadastro global.
    op.drop_column("dim_fornecedor", "codemp", schema="dw")
    op.add_column(
        "dim_fornecedor",
        sa.Column("nome_fantasia", sa.String(200), nullable=True, comment="EMI_FANT"),
        schema="dw",
    )
    op.create_unique_constraint(
        "uq_dim_fornecedor_cod_sia", "dim_fornecedor", ["cod_sia"], schema="dw"
    )

    # ── dim_cliente ────────────────────────────────────────────────────────
    # Adicionar unique constraint que faltou na migration 001
    op.create_unique_constraint(
        "uq_dim_cliente_emp_sia", "dim_cliente", ["codemp", "cod_sia"], schema="dw"
    )


def downgrade() -> None:
    op.drop_constraint("uq_dim_cliente_emp_sia", "dim_cliente", schema="dw", type_="unique")

    op.drop_constraint("uq_dim_fornecedor_cod_sia", "dim_fornecedor", schema="dw", type_="unique")
    op.drop_column("dim_fornecedor", "nome_fantasia", schema="dw")
    op.add_column(
        "dim_fornecedor",
        sa.Column("codemp", sa.Integer, nullable=False, server_default="1"),
        schema="dw",
    )

    op.drop_constraint("uq_dim_conta_sia", "dim_conta_sia", schema="dw", type_="unique")
    op.drop_column("dim_conta_sia", "conta_codsup", schema="dw")
    op.drop_column("dim_conta_sia", "conta_class", schema="dw")
    op.alter_column("dim_conta_sia", "codpla", new_column_name="codemp", schema="dw")
    op.create_unique_constraint(
        "uq_dim_conta_sia", "dim_conta_sia", ["codemp", "conta_codigo"], schema="dw"
    )
