from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional
from src.core.database import get_db
from src.models.operadora import OperadoraCadastro, DespesaConsolidada
from src.api.schemas import (
    PaginatedResponse, 
    OperadoraResponse, 
    OperadoraDetalhe,
    DespesaResponse,
    DespesasPaginatedResponse
)
import math

router = APIRouter()


@router.get("/operadoras", response_model=PaginatedResponse)
def listar_operadoras(
    page: int = Query(1, ge=1, description="Número da página"),
    limit: int = Query(10, ge=1, le=100, description="Itens por página"),
    search: Optional[str] = Query(None, description="Busca por razão social ou CNPJ"),
    uf: Optional[str] = Query(None, description="Filtrar por UF"),
    db: Session = Depends(get_db)
):
    query = db.query(OperadoraCadastro)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                OperadoraCadastro.razao_social.ilike(search_term),
                OperadoraCadastro.cnpj.like(search_term)
            )
        )
    
    if uf:
        query = query.filter(OperadoraCadastro.uf == uf.upper())
    
    total = query.count()
    pages = math.ceil(total / limit) if total > 0 else 1
    
    offset = (page - 1) * limit
    operadoras = query.order_by(OperadoraCadastro.razao_social).offset(offset).limit(limit).all()
    
    return PaginatedResponse(
        data=[OperadoraResponse.model_validate(op) for op in operadoras],
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )


@router.get("/operadoras/{cnpj}", response_model=OperadoraDetalhe)
def obter_operadora(cnpj: str, db: Session = Depends(get_db)):
    cnpj_limpo = cnpj.replace(".", "").replace("/", "").replace("-", "")
    
    operadora = db.query(OperadoraCadastro).filter(
        OperadoraCadastro.cnpj == cnpj_limpo
    ).first()
    
    if not operadora:
        raise HTTPException(status_code=404, detail="Operadora não encontrada")
    
    despesas_stats = db.query(
        func.sum(DespesaConsolidada.valor_despesas).label("total"),
        func.count(DespesaConsolidada.id).label("num_trimestres")
    ).filter(DespesaConsolidada.cnpj == cnpj_limpo).first()
    
    return OperadoraDetalhe(
        id=operadora.id,
        cnpj=operadora.cnpj,
        razao_social=operadora.razao_social,
        registro_ans=operadora.registro_ans,
        modalidade=operadora.modalidade,
        uf=operadora.uf,
        total_despesas=despesas_stats.total if despesas_stats.total else 0,
        num_trimestres=despesas_stats.num_trimestres if despesas_stats.num_trimestres else 0
    )


@router.get("/operadoras/{cnpj}/despesas", response_model=DespesasPaginatedResponse)
def obter_despesas_operadora(
    cnpj: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    cnpj_limpo = cnpj.replace(".", "").replace("/", "").replace("-", "")
    
    operadora = db.query(OperadoraCadastro).filter(
        OperadoraCadastro.cnpj == cnpj_limpo
    ).first()
    
    if not operadora:
        raise HTTPException(status_code=404, detail="Operadora não encontrada")
    
    query = db.query(DespesaConsolidada).filter(DespesaConsolidada.cnpj == cnpj_limpo)
    
    total = query.count()
    pages = math.ceil(total / limit) if total > 0 else 1
    
    offset = (page - 1) * limit
    despesas = query.order_by(
        DespesaConsolidada.ano.desc(),
        DespesaConsolidada.trimestre.desc()
    ).offset(offset).limit(limit).all()
    
    return DespesasPaginatedResponse(
        data=[DespesaResponse(
            id=d.id,
            cnpj=d.cnpj,
            razao_social=d.razao_social,
            trimestre=d.trimestre,
            ano=d.ano,
            valor_despesas=d.valor_despesas
        ) for d in despesas],
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )
