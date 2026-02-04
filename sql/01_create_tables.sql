-- TESTE 3.2 - DDL: Estruturação das Tabelas
--
-- NORMALIZAÇÃO: Opção B (tabelas separadas)
-- Razão: Operadoras mudam raramente, despesas são atualizadas trimestralmente.
--        Evita duplicação de dados cadastrais a cada registro de despesa.
--        JOINs com índices são eficientes para o volume esperado.
--
-- TIPOS DE DADOS:
-- - NUMERIC(15,2): Valores monetários precisos, sem erros de arredondamento do FLOAT
-- - INTEGER + VARCHAR(2): Ano e trimestre separados (ex: 2024 + 'Q1')
--   Mais natural para dados trimestrais do que TIMESTAMP
--
-- ÍNDICES:
-- - CNPJ, ano/trimestre: JOINs e filtros frequentes
-- - valor_despesas DESC: Queries de ranking
-- - UF, razao_social: Agregações e buscas

CREATE TABLE IF NOT EXISTS operadoras_cadastro (
    id SERIAL PRIMARY KEY,
    cnpj VARCHAR(14) NOT NULL UNIQUE,
    registro_ans VARCHAR(50),
    razao_social VARCHAR(255) NOT NULL,
    modalidade VARCHAR(100),
    uf VARCHAR(2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_cnpj_formato CHECK (cnpj ~ '^[0-9]{14}$'),
    CONSTRAINT check_uf_formato CHECK (uf IS NULL OR LENGTH(uf) = 2)
);

CREATE INDEX idx_cadastro_cnpj ON operadoras_cadastro(cnpj);
CREATE INDEX idx_cadastro_uf ON operadoras_cadastro(uf);
CREATE INDEX idx_cadastro_razao_social ON operadoras_cadastro(razao_social);

CREATE TABLE IF NOT EXISTS despesas_consolidadas (
    id SERIAL PRIMARY KEY,
    cnpj VARCHAR(14) NOT NULL,
    razao_social VARCHAR(255) NOT NULL,
    trimestre VARCHAR(2) NOT NULL,
    ano INTEGER NOT NULL,
    valor_despesas NUMERIC(15, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_trimestre_valido CHECK (trimestre IN ('1T', '2T', '3T', '4T')),
    CONSTRAINT check_ano_valido CHECK (ano BETWEEN 2020 AND 2030),
    CONSTRAINT check_valor_positivo CHECK (valor_despesas > 0),
    CONSTRAINT unique_despesa_periodo UNIQUE (cnpj, ano, trimestre),
    CONSTRAINT fk_despesas_operadora 
        FOREIGN KEY (cnpj) 
        REFERENCES operadoras_cadastro(cnpj)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE INDEX idx_despesas_cnpj ON despesas_consolidadas(cnpj);
CREATE INDEX idx_despesas_ano_trimestre ON despesas_consolidadas(ano, trimestre);
CREATE INDEX idx_despesas_valor ON despesas_consolidadas(valor_despesas DESC);

CREATE TABLE IF NOT EXISTS despesas_agregadas (
    id SERIAL PRIMARY KEY,
    razao_social VARCHAR(255) NOT NULL,
    uf VARCHAR(2),
    total_despesas NUMERIC(20, 2) NOT NULL,
    media_despesas NUMERIC(15, 2),
    desvio_padrao NUMERIC(15, 2),
    num_registros INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_totais_positivos CHECK (total_despesas > 0),
    CONSTRAINT check_num_registros CHECK (num_registros > 0)
);

CREATE INDEX idx_agregadas_razao_uf ON despesas_agregadas(razao_social, uf);
CREATE INDEX idx_agregadas_uf ON despesas_agregadas(uf);
CREATE INDEX idx_agregadas_total ON despesas_agregadas(total_despesas DESC);

