-- Query 1: Top 5 operadoras com maior crescimento percentual
--
-- DESAFIO: Operadoras podem não ter todos os trimestres
--
-- SOLUÇÃO: Comparar primeiro vs último trimestre disponível
-- - Ignora trimestres faltantes no meio
-- - Requer mínimo 2 trimestres para calcular crescimento
-- - Alternativa rejeitada: Interpolar valores criaria dados fictícios
--
-- Usa ROW_NUMBER() para identificar primeiro e último registro por CNPJ

WITH periodos_operadora AS (
    SELECT 
        cnpj,
        razao_social,
        ano,
        trimestre,
        valor_despesas,
        ROW_NUMBER() OVER (PARTITION BY cnpj ORDER BY ano ASC, trimestre ASC) as rank_inicio,
        ROW_NUMBER() OVER (PARTITION BY cnpj ORDER BY ano DESC, trimestre DESC) as rank_fim,
        COUNT(*) OVER (PARTITION BY cnpj) as total_trimestres
    FROM despesas_consolidadas
),
valores_comparacao AS (
    SELECT 
        cnpj,
        MAX(razao_social) as razao_social,
        MAX(CASE WHEN rank_inicio = 1 THEN valor_despesas END) as valor_inicial,
        MAX(CASE WHEN rank_fim = 1 THEN valor_despesas END) as valor_final,
        MAX(total_trimestres) as total_trimestres
    FROM periodos_operadora
    GROUP BY cnpj
    HAVING MAX(total_trimestres) >= 2
)
SELECT 
    razao_social,
    cnpj,
    ROUND(valor_inicial::numeric, 2) as despesa_inicial,
    ROUND(valor_final::numeric, 2) as despesa_final,
    ROUND(((valor_final - valor_inicial) / NULLIF(valor_inicial, 0) * 100)::numeric, 2) as crescimento_percentual
FROM valores_comparacao
WHERE valor_inicial > 0 AND valor_final > 0
ORDER BY crescimento_percentual DESC
LIMIT 5;
