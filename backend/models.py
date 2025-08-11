from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship

from .db import Base


class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    cnpj = Column(String, unique=True, nullable=False)

    contratos = relationship("Contrato", back_populates="empresa")


class Contrato(Base):
    __tablename__ = "contratos"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    numero = Column(String, nullable=False)
    banco = Column(String, nullable=False)
    saldo = Column(Float, nullable=False)
    taxa_anual = Column(Float, nullable=False)
    data_inicio = Column(Date, nullable=False)

    empresa = relationship("Empresa", back_populates="contratos")
    extratos = relationship("Extrato", back_populates="contrato", cascade="all, delete-orphan")


class Extrato(Base):
    __tablename__ = "extratos"

    id = Column(Integer, primary_key=True, index=True)
    contrato_id = Column(Integer, ForeignKey("contratos.id"), nullable=True)
    filepath = Column(String, nullable=False)
    status = Column(String, nullable=False)
    meta = Column("metadata", JSON, nullable=True)

    contrato = relationship("Contrato", back_populates="extratos")
    movimentacoes = relationship("Movimentacao", back_populates="extrato", cascade="all, delete-orphan")


class Movimentacao(Base):
    __tablename__ = "movimentacoes"

    id = Column(Integer, primary_key=True, index=True)
    extrato_id = Column(Integer, ForeignKey("extratos.id"), nullable=False)
    data_ref = Column(Date)
    data_lanc = Column(Date)
    descricao = Column(String)
    valor_debito = Column(Float)
    valor_credito = Column(Float)
    saldo = Column(Float)

    extrato = relationship("Extrato", back_populates="movimentacoes")
