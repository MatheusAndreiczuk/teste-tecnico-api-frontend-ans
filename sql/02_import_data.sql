-- TESTE 3.3 - Importação dos Dados CSV
--
-- TRATAMENTO DE INCONSISTÊNCIAS:
--
-- 1. NULLs em campos obrigatórios: Rejeitar (NOT NULL constraints)
--    CNPJ e razão_social são essenciais. UF pode ser NULL.
--
-- 2. Strings em numéricos: PostgreSQL rejeita automaticamente na conversão
--    Força correção na fonte ao invés de mascarar erros.
--
-- 3. Formatos inconsistentes: CHECK constraints validam
--    Trimestre: 1T-4T, Ano: 2020-2030
--
-- 4. Encoding: UTF-8 para caracteres especiais
--
-- ORDEM: operadoras_cadastro -> despesas_consolidadas -> despesas_agregadas

\echo 'Importando cadastro de operadoras...'
\copy operadoras_cadastro(cnpj, registro_ans, razao_social, modalidade, uf) FROM '/tmp/operadoras_cadastro.csv' DELIMITER ',' CSV HEADER ENCODING 'UTF8'

\echo 'Importando despesas consolidadas...'
CREATE TEMP TABLE temp_despesas (
    "CNPJ" VARCHAR(14),
    "RazaoSocial" VARCHAR(255),
    "Trimestre" VARCHAR(2),
    "Ano" INTEGER,
    "ValorDespesas" NUMERIC(15,2)
);

\copy temp_despesas FROM '/tmp/consolidado_despesas.csv' DELIMITER ',' CSV HEADER ENCODING 'UTF8'

INSERT INTO despesas_consolidadas (cnpj, razao_social, trimestre, ano, valor_despesas)
SELECT "CNPJ", "RazaoSocial", "Trimestre", "Ano", "ValorDespesas"
FROM temp_despesas
WHERE "CNPJ" IS NOT NULL AND "RazaoSocial" IS NOT NULL;

DROP TABLE temp_despesas;

\echo 'Gerando dados agregados...'
INSERT INTO despesas_agregadas (razao_social, uf, total_despesas, media_despesas, desvio_padrao, num_registros)
SELECT 
    dc.razao_social,
    COALESCE(oc.uf, 'N/A') as uf,
    SUM(dc.valor_despesas) as total_despesas,
    AVG(dc.valor_despesas) as media_despesas,
    STDDEV(dc.valor_despesas) as desvio_padrao,
    COUNT(*) as num_registros
FROM despesas_consolidadas dc
LEFT JOIN operadoras_cadastro oc ON dc.cnpj = oc.cnpj
GROUP BY dc.razao_social, oc.uf
ORDER BY total_despesas DESC;

\echo 'Verificação pós-importação:'
SELECT 'Operadoras cadastradas:' as tabela, COUNT(*) as registros FROM operadoras_cadastro
UNION ALL
SELECT 'Despesas consolidadas:', COUNT(*) FROM despesas_consolidadas
UNION ALL
SELECT 'Registros agregados:', COUNT(*) FROM despesas_agregadas;
