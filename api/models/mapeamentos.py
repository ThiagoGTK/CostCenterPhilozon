"""
Tabelas de mapeamento SIA → Gerencial.
Schema: dw

Estas tabelas conectam o mundo contábil do SIA com o plano gerencial interno.
São preenchidas manualmente pelos usuários via API e usadas pelo ETL para
popular id_conta_gerencial e id_centro_custo em fato_lancamento_realizado.
"""

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.db.session import Base


class MapeamentoContaSia(Base):
    """
    De-para: conta contábil SIA → conta gerencial interna.
    Uma conta SIA pode mapear para apenas uma conta gerencial por empresa.
    """
    __tablename__ = "mapeamento_conta_sia_gerencial"
    __table_args__ = {"schema": "dw"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_conta_sia: Mapped[int] = mapped_column(
        Integer, ForeignKey("dw.dim_conta_sia.id"), nullable=False
    )
    id_conta_gerencial: Mapped[int] = mapped_column(
        Integer, ForeignKey("dw.dim_conta_gerencial.id"), nullable=False
    )
    id_empresa: Mapped[int] = mapped_column(
        Integer, ForeignKey("dw.dim_empresa.id"), nullable=False
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    observacao: Mapped[str | None] = mapped_column(Text)

    conta_sia: Mapped["DimContaSia"] = relationship("DimContaSia")  # type: ignore[name-defined]
    conta_gerencial: Mapped["DimContaGerencial"] = relationship("DimContaGerencial")  # type: ignore[name-defined]
    empresa: Mapped["DimEmpresa"] = relationship("DimEmpresa")  # type: ignore[name-defined]


class MapeamentoCentroCusto(Base):
    """
    De-para: centro de custo SIA (CTB_CCUSTOS) → CC gerencial interno.
    O cc_sia_codigo referencia CC_COD da CTB_CCUSTOS (como string).
    """
    __tablename__ = "mapeamento_centro_custo_sia_gerencial"
    __table_args__ = {"schema": "dw"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cc_sia_codigo: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="CC_COD do CTB_CCUSTOS"
    )
    cc_sia_nome: Mapped[str | None] = mapped_column(
        String(200), comment="CC_DESC — denormalizado para facilitar UI"
    )
    id_empresa: Mapped[int] = mapped_column(
        Integer, ForeignKey("dw.dim_empresa.id"), nullable=False
    )
    id_centro_custo_gerencial: Mapped[int] = mapped_column(
        Integer, ForeignKey("dw.dim_centro_custo.id"), nullable=False
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    observacao: Mapped[str | None] = mapped_column(Text)

    empresa: Mapped["DimEmpresa"] = relationship("DimEmpresa")  # type: ignore[name-defined]
    centro_custo: Mapped["DimCentroCusto"] = relationship("DimCentroCusto")  # type: ignore[name-defined]
