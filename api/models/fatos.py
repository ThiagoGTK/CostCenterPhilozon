"""
Tabelas de fato do Data Warehouse.
Regra: NUNCA usar float. Sempre NUMERIC(15,2).
Schema: dw
"""

from decimal import Decimal
from datetime import date, datetime
from sqlalchemy import Integer, NUMERIC, Date, DateTime, String, ForeignKey, Text, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from api.db.session import Base


class FatoLancamentoRealizado(Base):
    """
    Lançamentos contábeis realizados, extraídos do CTB_MOVIMENTOS do SIA.
    Nunca inserido manualmente — apenas via ETL.
    """
    __tablename__ = "fato_lancamento_realizado"
    __table_args__ = {"schema": "dw"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_empresa: Mapped[int] = mapped_column(Integer, ForeignKey("dw.dim_empresa.id"), nullable=False)
    id_tempo: Mapped[int] = mapped_column(Integer, ForeignKey("dw.dim_tempo.id"), nullable=False)
    id_conta_sia: Mapped[int] = mapped_column(Integer, ForeignKey("dw.dim_conta_sia.id"), nullable=False)
    id_conta_gerencial: Mapped[int | None] = mapped_column(Integer, ForeignKey("dw.dim_conta_gerencial.id"))
    id_centro_custo: Mapped[int | None] = mapped_column(Integer, ForeignKey("dw.dim_centro_custo.id"))

    # Chave de negócio para idempotência do ETL
    sia_lancamento_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True,
                                                     comment="ID único do lançamento no SIA (CODEMP+numero)")

    valor: Mapped[Decimal] = mapped_column(NUMERIC(15, 2), nullable=False)
    # D = Débito, C = Crédito
    tipo_lancamento: Mapped[str] = mapped_column(String(1), nullable=False)
    historico: Mapped[str | None] = mapped_column(String(500))

    data_referencia: Mapped[date] = mapped_column(Date, nullable=False)
    data_carga: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class FatoOrcamento(Base):
    """
    Lançamentos de orçamento inseridos pelos usuários via interface.
    Schema: dw (compartilhado com DW para facilitar queries no Metabase).
    """
    __tablename__ = "fato_orcamento"
    __table_args__ = {"schema": "dw"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_empresa: Mapped[int] = mapped_column(Integer, ForeignKey("dw.dim_empresa.id"), nullable=False)
    id_versao: Mapped[int] = mapped_column(Integer, ForeignKey("dw.dim_versao_orcamento.id"), nullable=False)
    id_conta_gerencial: Mapped[int] = mapped_column(Integer, ForeignKey("dw.dim_conta_gerencial.id"), nullable=False)
    id_centro_custo: Mapped[int] = mapped_column(Integer, ForeignKey("dw.dim_centro_custo.id"), nullable=False)

    ano: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    mes: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    valor: Mapped[Decimal] = mapped_column(NUMERIC(15, 2), nullable=False)
    observacao: Mapped[str | None] = mapped_column(Text)

    criado_por: Mapped[str | None] = mapped_column(String(100))
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    versao: Mapped["DimVersaoOrcamento"] = relationship("DimVersaoOrcamento")  # type: ignore[name-defined]
    conta_gerencial: Mapped["DimContaGerencial"] = relationship("DimContaGerencial")  # type: ignore[name-defined]
    centro_custo: Mapped["DimCentroCusto"] = relationship("DimCentroCusto")  # type: ignore[name-defined]


class FatoReceita(Base):
    """
    Receita bruta por período, extraída do EST_VENDA / FIS_MOVIMENTO.
    Agregação mensal para facilitar análise.
    """
    __tablename__ = "fato_receita"
    __table_args__ = {"schema": "dw"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_empresa: Mapped[int] = mapped_column(Integer, ForeignKey("dw.dim_empresa.id"), nullable=False)
    id_tempo: Mapped[int] = mapped_column(Integer, ForeignKey("dw.dim_tempo.id"), nullable=False)
    id_cliente: Mapped[int | None] = mapped_column(Integer, ForeignKey("dw.dim_cliente.id"))

    # Chave de idempotência: empresa + ano + mês + cliente
    chave_upsert: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    receita_bruta: Mapped[Decimal] = mapped_column(NUMERIC(15, 2), nullable=False, default=Decimal("0"))
    deducoes: Mapped[Decimal] = mapped_column(NUMERIC(15, 2), nullable=False, default=Decimal("0"))
    receita_liquida: Mapped[Decimal] = mapped_column(NUMERIC(15, 2), nullable=False, default=Decimal("0"))

    data_carga: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class FatoDespesa(Base):
    """
    Despesas agregadas por período e centro de custo.
    Fonte: CTB_MOVIMENTOS + mapeamento gerencial.
    """
    __tablename__ = "fato_despesa"
    __table_args__ = {"schema": "dw"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_empresa: Mapped[int] = mapped_column(Integer, ForeignKey("dw.dim_empresa.id"), nullable=False)
    id_tempo: Mapped[int] = mapped_column(Integer, ForeignKey("dw.dim_tempo.id"), nullable=False)
    id_conta_gerencial: Mapped[int] = mapped_column(Integer, ForeignKey("dw.dim_conta_gerencial.id"), nullable=False)
    id_centro_custo: Mapped[int | None] = mapped_column(Integer, ForeignKey("dw.dim_centro_custo.id"))

    chave_upsert: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)

    valor: Mapped[Decimal] = mapped_column(NUMERIC(15, 2), nullable=False)
    data_carga: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
