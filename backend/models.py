from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
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
