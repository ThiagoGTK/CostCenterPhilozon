"""
Tabelas de dimensão do Data Warehouse.
Schema: dw
"""

from datetime import date
from sqlalchemy import String, Integer, Boolean, Date, ForeignKey, Text, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.db.session import Base


class DimEmpresa(Base):
    __tablename__ = "dim_empresa"
    __table_args__ = {"schema": "dw"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codemp: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, comment="Código da empresa no SIA")
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    cnpj: Mapped[str | None] = mapped_column(String(18))
    ativa: Mapped[bool] = mapped_column(Boolean, default=True)


class DimTempo(Base):
    __tablename__ = "dim_tempo"
    __table_args__ = {"schema": "dw"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    data: Mapped[date] = mapped_column(Date, nullable=False, unique=True)
    ano: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    mes: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    trimestre: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    semestre: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    nome_mes: Mapped[str] = mapped_column(String(20), nullable=False)


class DimCentroCusto(Base):
    """Centro de custo gerencial — independente do SIA."""
    __tablename__ = "dim_centro_custo"
    __table_args__ = {"schema": "dw"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    id_pai: Mapped[int | None] = mapped_column(Integer, ForeignKey("dw.dim_centro_custo.id"))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    filhos: Mapped[list["DimCentroCusto"]] = relationship("DimCentroCusto", back_populates="pai")
    pai: Mapped["DimCentroCusto | None"] = relationship("DimCentroCusto", back_populates="filhos", remote_side="DimCentroCusto.id")


class DimContaGerencial(Base):
    """Plano de contas gerencial — separado do contábil SIA."""
    __tablename__ = "dim_conta_gerencial"
    __table_args__ = {"schema": "dw"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    # Tipo: RECEITA, DESPESA, ATIVO, PASSIVO, RESULTADO
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    # Natureza: DEVEDORA, CREDORA
    natureza: Mapped[str] = mapped_column(String(10), nullable=False)
    id_pai: Mapped[int | None] = mapped_column(Integer, ForeignKey("dw.dim_conta_gerencial.id"))
    nivel: Mapped[int] = mapped_column(SmallInteger, default=1)
    aceita_lancamento: Mapped[bool] = mapped_column(Boolean, default=True, comment="False para contas-grupo")
    ativa: Mapped[bool] = mapped_column(Boolean, default=True)

    filhos: Mapped[list["DimContaGerencial"]] = relationship("DimContaGerencial", back_populates="pai")
    pai: Mapped["DimContaGerencial | None"] = relationship("DimContaGerencial", back_populates="filhos", remote_side="DimContaGerencial.id")


class DimContaSia(Base):
    """Plano de contas contábil extraído do SIA (CTB_CONTAS)."""
    __tablename__ = "dim_conta_sia"
    __table_args__ = {"schema": "dw"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codemp: Mapped[int] = mapped_column(Integer, nullable=False)
    conta_codigo: Mapped[str] = mapped_column(String(50), nullable=False)
    conta_nome: Mapped[str] = mapped_column(String(200), nullable=False)
    conta_tipo: Mapped[str | None] = mapped_column(String(10))
    conta_nivel: Mapped[int | None] = mapped_column(SmallInteger)
    # TODO: validar campos reais na tabela CTB_CONTAS do SIA


class DimCliente(Base):
    """Clientes extraídos do SIA (GER_CLIDEST)."""
    __tablename__ = "dim_cliente"
    __table_args__ = {"schema": "dw"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codemp: Mapped[int] = mapped_column(Integer, nullable=False)
    cod_sia: Mapped[int] = mapped_column(Integer, nullable=False)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    cnpj_cpf: Mapped[str | None] = mapped_column(String(18))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    # TODO: adicionar campos após análise do GER_CLIDEST


class DimFornecedor(Base):
    """Fornecedores extraídos do SIA (GER_EMITENTES)."""
    __tablename__ = "dim_fornecedor"
    __table_args__ = {"schema": "dw"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codemp: Mapped[int] = mapped_column(Integer, nullable=False)
    cod_sia: Mapped[int] = mapped_column(Integer, nullable=False)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    cnpj_cpf: Mapped[str | None] = mapped_column(String(18))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    # TODO: adicionar campos após análise do GER_EMITENTES


class DimVersaoOrcamento(Base):
    """Versões do orçamento: Original, Revisão 1, Forecast Q3, etc."""
    __tablename__ = "dim_versao_orcamento"
    __table_args__ = {"schema": "dw"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ano: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    # Tipo: ORIGINAL, REVISAO, FORECAST
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    data_criacao: Mapped[date] = mapped_column(Date, nullable=False)
    bloqueada: Mapped[bool] = mapped_column(Boolean, default=False, comment="True após aprovação final")
