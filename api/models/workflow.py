"""
Tabelas de controle de workflow do orçamento.
Schema: dw
"""

from decimal import Decimal
from datetime import datetime
from sqlalchemy import Integer, NUMERIC, DateTime, String, Text, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum
from api.db.session import Base


class StatusWorkflow(str, enum.Enum):
    RASCUNHO = "RASCUNHO"
    ENVIADO = "ENVIADO"
    APROVADO = "APROVADO"
    REPROVADO = "REPROVADO"


class WorkflowOrcamento(Base):
    """
    Registro do ciclo de aprovação de uma versão de orçamento.
    Uma versão por empresa/ano/versão.
    """
    __tablename__ = "workflow_orcamento"
    __table_args__ = {"schema": "dw"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_versao: Mapped[int] = mapped_column(Integer, ForeignKey("dw.dim_versao_orcamento.id"), nullable=False)
    id_empresa: Mapped[int] = mapped_column(Integer, ForeignKey("dw.dim_empresa.id"), nullable=False)

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=StatusWorkflow.RASCUNHO.value,
    )

    criado_por: Mapped[str] = mapped_column(String(100), nullable=False)
    enviado_por: Mapped[str | None] = mapped_column(String(100))
    aprovado_por: Mapped[str | None] = mapped_column(String(100))
    reprovado_por: Mapped[str | None] = mapped_column(String(100))

    data_envio: Mapped[datetime | None] = mapped_column(DateTime)
    data_decisao: Mapped[datetime | None] = mapped_column(DateTime)
    comentario: Mapped[str | None] = mapped_column(Text)

    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class JustificativaVariacao(Base):
    """
    Justificativa obrigatória para variações acima do threshold configurado.
    """
    __tablename__ = "justificativa_variacao"
    __table_args__ = {"schema": "dw"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_empresa: Mapped[int] = mapped_column(Integer, ForeignKey("dw.dim_empresa.id"), nullable=False)
    id_versao: Mapped[int] = mapped_column(Integer, ForeignKey("dw.dim_versao_orcamento.id"), nullable=False)
    id_conta_gerencial: Mapped[int] = mapped_column(Integer, ForeignKey("dw.dim_conta_gerencial.id"), nullable=False)
    id_centro_custo: Mapped[int] = mapped_column(Integer, ForeignKey("dw.dim_centro_custo.id"), nullable=False)

    ano: Mapped[int] = mapped_column(Integer, nullable=False)
    mes: Mapped[int] = mapped_column(Integer, nullable=False)

    valor_orcado: Mapped[Decimal] = mapped_column(NUMERIC(15, 2), nullable=False)
    valor_realizado: Mapped[Decimal] = mapped_column(NUMERIC(15, 2), nullable=False)
    variacao_absoluta: Mapped[Decimal] = mapped_column(NUMERIC(15, 2), nullable=False)
    variacao_percentual: Mapped[Decimal] = mapped_column(NUMERIC(8, 2), nullable=False)

    justificativa: Mapped[str] = mapped_column(Text, nullable=False)
    criado_por: Mapped[str] = mapped_column(String(100), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
