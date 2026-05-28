"""Usuarios RBAC — tabela app.usuario + admin inicial

Revision ID: 005
Revises: 004
Create Date: 2026-05-28
"""

from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None

# Hash bcrypt de "admin123" — troque a senha após o primeiro login
ADMIN_SENHA_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGKD9G5P6.1V.3rQoG9PGHNqiOC"


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS app")

    op.create_table(
        "usuario",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("nome", sa.String(150), nullable=False),
        sa.Column("email", sa.String(200), nullable=False),
        sa.Column("senha_hash", sa.String(200), nullable=False),
        sa.Column("perfil", sa.String(20), nullable=False, server_default="COLABORADOR"),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("criado_em", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime, server_default=sa.func.now(), nullable=False),
        schema="app",
    )
    op.create_unique_constraint("uq_usuario_email", "usuario", ["email"], schema="app")
    op.create_index("ix_usuario_email", "usuario", ["email"], schema="app")

    # Usuário admin inicial — senha: admin123 (TROQUE após o primeiro acesso)
    op.execute(
        f"""
        INSERT INTO app.usuario (nome, email, senha_hash, perfil, ativo)
        VALUES (
            'Administrador',
            'admin@philozon.com.br',
            '{ADMIN_SENHA_HASH}',
            'ADMIN',
            true
        )
        """
    )


def downgrade() -> None:
    op.drop_table("usuario", schema="app")
