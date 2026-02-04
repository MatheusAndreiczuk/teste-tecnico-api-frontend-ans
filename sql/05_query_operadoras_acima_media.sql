-- Query 3: Operadoras acima da média em pelo menos 2 trimestres
--
-- ABORDAGEM: CTEs com agregações
--
-- VANTAGENS:
-- - Performance: Média calculada uma vez, não N vezes
-- - Legibilidade: Fluxo claro e modular
--
-- ALTERNATIVAS REJEITADAS:
-- - Subquery correlacionada: Recalcula média para cada linha
-- - Window functions: Menos claro para contar trimestres por operadora
-- - Self-JOIN: Muitos dados

WITH media_geral AS (
    SELECT AVG(valor_despesas) as media
    FROM despesas_consolidadas
),
operadoras_acima_media AS (
    SELECT 
        dc.cnpj,
        dc.razao_social,
        dc.ano || dc.trimestre as periodo,
        dc.valor_despesas,
        mg.media
    FROM despesas_consolidadas dc
    CROSS JOIN media_geral mg
    WHERE dc.valor_despesas > mg.media
),
contagem_trimestres AS (
    SELECT 
        cnpj,
        razao_social,
        COUNT(DISTINCT periodo) as trimestres_acima_media
    FROM operadoras_acima_media
    GROUP BY cnpj, razao_social
)
SELECT 
    COUNT(*) as total_operadoras,
    ROUND((SELECT media FROM media_geral)::numeric, 2) as media_geral_despesas
FROM contagem_trimestres
WHERE trimestres_acima_media >= 2;

