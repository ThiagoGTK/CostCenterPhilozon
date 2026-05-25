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
    """Plano de contas contábil extraído do SIA (CTB_CONTAS).

    CTB_CONTAS não tem CODEMP — isolamento por CON_CODPLA (plano da empresa).
    Philozon usa os planos 1 (2019) e 2 (2023).
    conta_codigo = CON_COD (inteiro, chave interna do SIA).
    conta_class  = CON_CLASS (código hierárquico legível, ex: "1.01.02.03").
    """
    __tablename__ = "dim_conta_sia"
    __table_args__ = {"schema": "dw"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codpla: Mapped[int] = mapped_column(Integer, nullable=False, comment="CON_CODPLA — plano de contas")
    conta_codigo: Mapped[str] = mapped_column(String(50), nullable=False, comment="CON_COD")
    conta_class: Mapped[str | None] = mapped_column(String(50), comment="CON_CLASS — código hierárquico")
    conta_codsup: Mapped[int | None] = mapped_column(Integer, comment="CON_CODSUP — conta pai")
    conta_nome: Mapped[str] = mapped_column(String(200), nullable=False, comment="CON_DESC")
    conta_tipo: Mapped[str | None] = mapped_column(String(10), comment="CON_TIPO")
    conta_nivel: Mapped[int | None] = mapped_column(SmallInteger, comment="CON_NIVEL")


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
    """Fornecedores extraídos do SIA (GER_EMITENTES).
    GER_EMITENTES não tem CODEMP — é um cadastro global (sem isolamento por empresa).
    """
    __tablename__ = "dim_fornecedor"
    __table_args__ = {"schema": "dw"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cod_sia: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, comment="EMI_COD")
    nome: Mapped[str] = mapped_column(String(200), nullable=False, comment="EMI_DESC")
    nome_fantasia: Mapped[str | None] = mapped_column(String(200), comment="EMI_FANT")
    cnpj_cpf: Mapped[str | None] = mapped_column(String(18), comment="EMI_CNPJCPF")
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, comment="EMI_ATIINA")


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
