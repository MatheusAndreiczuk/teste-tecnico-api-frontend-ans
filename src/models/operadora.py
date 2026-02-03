from sqlalchemy import Column, String, Integer, Numeric, DateTime, Index
from sqlalchemy.sql import func
from src.core.database import Base


class DespesaConsolidada(Base):
    __tablename__ = "despesas_consolidadas"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cnpj = Column(String(14), nullable=False, index=True)
    razao_social = Column(String(255), nullable=False)
    trimestre = Column(String(10), nullable=False)
    ano = Column(String(4), nullable=False)
    valor_despesas = Column(Numeric(15, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_cnpj_ano_trimestre', 'cnpj', 'ano', 'trimestre'),
    )


class OperadoraCadastro(Base):
    __tablename__ = "operadoras_cadastro"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cnpj = Column(String(14), nullable=False, unique=True, index=True)
    registro_ans = Column(String(50))
    razao_social = Column(String(255))
    modalidade = Column(String(100))
    uf = Column(String(2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DespesaAgregada(Base):
    __tablename__ = "despesas_agregadas"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    razao_social = Column(String(255), nullable=False)
    uf = Column(String(2))
    total_despesas = Column(Numeric(20, 2), nullable=False)
    media_despesas = Column(Numeric(15, 2))
    desvio_padrao = Column(Numeric(15, 2))
    num_registros = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_razao_social_uf', 'razao_social', 'uf'),
    )
