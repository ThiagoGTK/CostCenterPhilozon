"""
Tabelas de mapeamento entre SIA e gerencial.
Permitem traduzir o plano de contas contábil do SIA para o plano gerencial.
Schema: dw
"""

from sqlalchemy import Integer, String, ForeignKey, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from api.db.session import Base


class MapeamentoContaSiaGerencial(Base):
    """
    De-para entre conta contábil do SIA e conta gerencial.
    N:1 — várias contas SIA podem mapear para uma conta gerencial.
    """
    __tablename__ = "mapeamento_conta_sia_gerencial"
    __table_args__ = {"schema": "dw"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_conta_sia: Mapped[int] = mapped_column(Integer, ForeignKey("dw.dim_conta_sia.id"), nullable=False)
    id_conta_gerencial: Mapped[int] = mapped_column(Integer, ForeignKey("dw.dim_conta_gerencial.id"), nullable=False)
    id_empresa: Mapped[int] = mapped_column(Integer, ForeignKey("dw.dim_empresa.id"), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    observacao: Mapped[str | None] = mapped_column(Text)


class MapeamentoCentroCustoSiaGerencial(Base):
    """
    De-para entre centro de custo do SIA e centro de custo gerencial.
    """
    __tablename__ = "mapeamento_centro_custo_sia_gerencial"
    __table_args__ = {"schema": "dw"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Código do CC no SIA (CTB_CCUSTOS)
    cc_sia_codigo: Mapped[str] = mapped_column(String(50), nullable=False)
    cc_sia_nome: Mapped[str | None] = mapped_column(String(200))
    id_empresa: Mapped[int] = mapped_column(Integer, ForeignKey("dw.dim_empresa.id"), nullable=False)
    id_centro_custo_gerencial: Mapped[int] = mapped_column(Integer, ForeignKey("dw.dim_centro_custo.id"), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    observacao: Mapped[str | None] = mapped_column(Text)
