"""
Tabela de usuários do sistema FP&A.
Schema: app (tabelas de suporte da aplicação).
"""

from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from api.db.session import Base


class PerfilUsuario:
    ADMIN = "ADMIN"
    GESTOR = "GESTOR"
    COLABORADOR = "COLABORADOR"

    TODOS = (ADMIN, GESTOR, COLABORADOR)


class Usuario(Base):
    __tablename__ = "usuario"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    senha_hash: Mapped[str] = mapped_column(String(200), nullable=False)

    # Perfil: ADMIN | GESTOR | COLABORADOR (padrão seguro = COLABORADOR)
    perfil: Mapped[str] = mapped_column(String(20), nullable=False, default=PerfilUsuario.COLABORADOR)

    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
