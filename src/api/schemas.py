from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal


class OperadoraBase(BaseModel):
    cnpj: str
    razao_social: Optional[str] = None
    registro_ans: Optional[str] = None
    modalidade: Optional[str] = None
    uf: Optional[str] = None

    class Config:
        from_attributes = True


class OperadoraResponse(OperadoraBase):
    id: int


class DespesaBase(BaseModel):
    trimestre: str
    ano: int
    valor_despesas: Decimal

    class Config:
        from_attributes = True


class DespesaResponse(DespesaBase):
    id: int
    cnpj: str
    razao_social: str


class OperadoraDetalhe(OperadoraBase):
    id: int
    total_despesas: Optional[Decimal] = None
    num_trimestres: Optional[int] = None


class PaginatedResponse(BaseModel):
    data: List[OperadoraResponse]
    total: int
    page: int
    limit: int
    pages: int


class DespesasPaginatedResponse(BaseModel):
    data: List[DespesaResponse]
    total: int
    page: int
    limit: int
    pages: int


class EstatisticasGerais(BaseModel):
    total_operadoras: int
    total_despesas: Decimal
    media_despesas: Decimal
    total_registros: int


class TopOperadora(BaseModel):
    cnpj: str
    razao_social: str
    total_despesas: Decimal
    uf: Optional[str] = None


class DistribuicaoUF(BaseModel):
    uf: str
    total_despesas: Decimal
    num_operadoras: int
    percentual: float


class EstatisticasResponse(BaseModel):
    gerais: EstatisticasGerais
    top_operadoras: List[TopOperadora]
    distribuicao_uf: List[DistribuicaoUF]
