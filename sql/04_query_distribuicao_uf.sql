-- Query 2: Distribuição de despesas por UF
--
-- DESAFIO: Calcular média por operadora, não apenas total
--
-- SOLUÇÃO:
-- - Total: SUM de todas as despesas
-- - Média por operadora: AVG das despesas individuais
-- - Total alto + média baixa = mercado pulverizado
-- - Total alto + média alta = mercado concentrado
--
-- Operadoras sem UF são filtradas (análise geográfica requer localização)

WITH despesas_por_uf AS (
    SELECT 
        oc.uf,
        SUM(dc.valor_despesas) as total_despesas,
        AVG(dc.valor_despesas) as media_por_operadora,
        COUNT(DISTINCT dc.cnpj) as num_operadoras,
        COUNT(*) as num_registros_trimestrais
    FROM despesas_consolidadas dc
    LEFT JOIN operadoras_cadastro oc ON dc.cnpj = oc.cnpj
    WHERE oc.uf IS NOT NULL
    GROUP BY oc.uf
)
SELECT 
    uf,
    ROUND(total_despesas::numeric, 2) as total_despesas,
    ROUND(media_por_operadora::numeric, 2) as media_por_operadora,
    num_operadoras,
    num_registros_trimestrais
FROM despesas_por_uf
ORDER BY total_despesas DESC
LIMIT 5;
