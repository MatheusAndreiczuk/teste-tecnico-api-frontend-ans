from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.core.database import get_db
from src.models.operadora import OperadoraCadastro, DespesaConsolidada, DespesaAgregada
from src.api.schemas import (
    EstatisticasResponse,
    EstatisticasGerais,
    TopOperadora,
    DistribuicaoUF
)
from decimal import Decimal
from functools import lru_cache
from datetime import datetime, timedelta

router = APIRouter()

_cache = {}
_cache_ttl = timedelta(minutes=5)


def get_cached_stats(db: Session):
    cache_key = "estatisticas"
    now = datetime.now()
    
    if cache_key in _cache:
        cached_data, cached_time = _cache[cache_key]
        if now - cached_time < _cache_ttl:
            return cached_data
    
    stats = compute_estatisticas(db)
    _cache[cache_key] = (stats, now)
    return stats


def compute_estatisticas(db: Session) -> EstatisticasResponse:
    total_operadoras = db.query(func.count(OperadoraCadastro.id)).scalar() or 0
    
    despesas_stats = db.query(
        func.sum(DespesaConsolidada.valor_despesas).label("total"),
        func.avg(DespesaConsolidada.valor_despesas).label("media"),
        func.count(DespesaConsolidada.id).label("count")
    ).first()
    
    total_despesas = despesas_stats.total or Decimal(0)
    media_despesas = despesas_stats.media or Decimal(0)
    total_registros = despesas_stats.count or 0
    
    top_5 = db.query(
        DespesaConsolidada.cnpj,
        DespesaConsolidada.razao_social,
        func.sum(DespesaConsolidada.valor_despesas).label("total")
    ).group_by(
        DespesaConsolidada.cnpj,
        DespesaConsolidada.razao_social
    ).order_by(
        func.sum(DespesaConsolidada.valor_despesas).desc()
    ).limit(5).all()
    
    top_operadoras = []
    for item in top_5:
        operadora = db.query(OperadoraCadastro).filter(
            OperadoraCadastro.cnpj == item.cnpj
        ).first()
        top_operadoras.append(TopOperadora(
            cnpj=item.cnpj,
            razao_social=item.razao_social,
            total_despesas=item.total,
            uf=operadora.uf if operadora else None
        ))
    
    distribuicao = db.query(
        OperadoraCadastro.uf,
        func.sum(DespesaConsolidada.valor_despesas).label("total"),
        func.count(func.distinct(DespesaConsolidada.cnpj)).label("num_ops")
    ).join(
        DespesaConsolidada,
        OperadoraCadastro.cnpj == DespesaConsolidada.cnpj
    ).filter(
        OperadoraCadastro.uf.isnot(None)
    ).group_by(
        OperadoraCadastro.uf
    ).order_by(
        func.sum(DespesaConsolidada.valor_despesas).desc()
    ).all()
    
    distribuicao_uf = []
    for item in distribuicao:
        percentual = float(item.total / total_despesas * 100) if total_despesas > 0 else 0
        distribuicao_uf.append(DistribuicaoUF(
            uf=item.uf or "N/A",
            total_despesas=item.total,
            num_operadoras=item.num_ops,
            percentual=round(percentual, 2)
        ))
    
    return EstatisticasResponse(
        gerais=EstatisticasGerais(
            total_operadoras=total_operadoras,
            total_despesas=total_despesas,
            media_despesas=media_despesas,
            total_registros=total_registros
        ),
        top_operadoras=top_operadoras,
        distribuicao_uf=distribuicao_uf
    )


@router.get("/estatisticas", response_model=EstatisticasResponse)
def obter_estatisticas(db: Session = Depends(get_db)):
    return get_cached_stats(db)
