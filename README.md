# Teste Técnico - Intuitive Care

Sistema de ETL e análise de dados de despesas de operadoras de planos de saúde (ANS).

## Requisitos

- Python 3.11+
- Node.js 18+
- Docker e Docker Compose

## Execução

```bash
# 1. Subir banco de dados
docker-compose up -d db

# 2. Instalar dependências e executar ETL
pip install -r requirements.txt
python run_etl.py

# 3. Importar dados no banco
.\migrate_data.ps1

# 4. Subir API (escolha uma opção)
docker-compose up -d app          # via Docker
# ou
uvicorn src.api.main:app --reload # local

# 5. Subir frontend
cd frontend
npm install
npm run dev
```

API: http://localhost:8000 (Swagger: /docs)
Frontend: http://localhost:3000

## Estrutura

```
├── src/
│   ├── api/           # FastAPI (rotas, schemas)
│   ├── core/          # Configuração e database
│   ├── etl/           # Download e processamento
│   └── models/        # SQLAlchemy
├── sql/               # DDL, importação e queries analíticas
├── frontend/          # Vue.js 3
├── data/processed/    # CSVs gerados
└── postman_collection.json
```

## Queries Analíticas (Teste 3)

```bash
# Top 5 operadoras com maior crescimento
Get-Content sql/03_query_crescimento.sql | docker-compose exec -T db psql -U postgres -d ans_data

# Distribuição por UF
Get-Content sql/04_query_distribuicao_uf.sql | docker-compose exec -T db psql -U postgres -d ans_data

# Operadoras acima da média
Get-Content sql/05_query_operadoras_acima_media.sql | docker-compose exec -T db psql -U postgres -d ans_data
```

## API Endpoints (Teste 4)

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | /api/operadoras | Lista paginada (page, limit, search, uf) |
| GET | /api/operadoras/{cnpj} | Detalhes da operadora |
| GET | /api/operadoras/{cnpj}/despesas | Histórico de despesas |
| GET | /api/estatisticas | Totais, top 5 e distribuição por UF |

## Trade-offs Técnicos Documentados

### Teste 1 - Integração com API Pública

**1.2 - Processamento de Arquivos: Memória vs Incremental**

**Escolha: Processar em memória com Pandas**

*Justificativa:*
- Volume atual: ~180k registros brutos → 827 registros úteis após filtros
- Memória necessária: < 50MB por trimestre
- Performance: Pandas permite operações vetorizadas rápidas
- Complexidade: Código mais simples sem gerenciamento de chunks

*Alternativa descartada:* Processamento incremental com chunks seria necessário apenas com datasets maiores ou ambientes com memória limitada (<2GB RAM).

**1.3 - Tratamento de Inconsistências**

| Inconsistência | Estratégia | Justificativa |
|----------------|------------|---------------|
| CNPJs com razões sociais diferentes | Usar primeira ocorrência | Operadoras mudam nome raramente. Prioritário: manter CNPJ válido |
| Valores zerados ou negativos | Excluir (175k de 178k) | Despesas devem ser positivas. Zero indica registro não aplicável |
| Formatos de data inconsistentes | Extração de trimestre de strings | Dados ANS usam formato `3T2025`. Regex garante parsing robusto |

### Teste 2 - Transformação e Validação

**2.1 - CNPJs Inválidos: Estratégias de Tratamento**

**Escolha: Excluir CNPJs inválidos**

*Justificativa:*
- 303 CNPJs inválidos removidos
- Manter dados incorretos compromete integridade
- Cenário real: operadora inativa ou erro de digitação na fonte

*Alternativas consideradas:*
- Marcar como suspeito: aumenta complexidade sem benefício (não há como validar depois)
- Tentar corrigir: arriscado, pode gerar CNPJ de outra empresa

**2.2 - Join entre Consolidado e Cadastro**

**Escolha: LEFT JOIN mantendo registros sem match**

*Justificativa:*
- 8 CNPJs sem match mantidos com dados de despesas
- Permite rastreabilidade: operadora pode ser ativada posteriormente
- Campos ausentes ficam NULL (UF, modalidade, registro ANS)

*Tratamento de múltiplos matches:*
- DROP DUPLICATES mantendo primeira ocorrência
- Cadastro ANS tem 1 registro por CNPJ (constraint de unicidade)

**Estratégia de Processamento: Pandas in-memory**

*Justificativa:*
- Consolidado: 827 registros (~100KB)
- Cadastro: 791 registros (~150KB)
- Join em memória é quase instantâneo 

**2.3 - Ordenação: Estratégia de Implementação**

**Escolha: sort_values() do Pandas**

*Justificativa:*
- Dataset agregado: 370 registros
- Pandas usa Timsort otimizado
- Performance: pouco tempo para ordenar
- Alternativas como heapsort só fariam sentido com milhões de registros

### Teste 3 - Banco de Dados e Análise

**3.2 - Normalização: Tabelas Separadas vs Desnormalizada**

**Escolha: 3 tabelas normalizadas**

```
operadoras_cadastro (791 registros)
despesas_consolidadas (827 registros) → FK: cnpj
despesas_agregadas (370 registros) → sem FK (agregação pré-calculada)
```

*Justificativa:*
- **Atualizações:** Operadoras mudam raramente, despesas são trimestrais
- **Volume:** <2k registros total, JOINs são rápidos com índices
- **Queries:** Maioria acessa apenas despesas ou apenas operadoras
- **Manutenção:** Separação facilita ETL incremental (adicionar novo trimestre sem duplicar cadastro)

*Contra desnormalização:*
- Duplicaria razão_social/UF em 827 registros
- Atualização de cadastro exigiria UPDATE em massa
- Economia de espaço irrelevante

**3.2 - Tipos de Dados Monetários: DECIMAL vs FLOAT vs INTEGER**

**Escolha: NUMERIC(15,2)**

*Justificativa:*
- **DECIMAL/NUMERIC:** Precisão exata para cálculos financeiros
- **Contra FLOAT:** Erros de arredondamento acumulam
- **Contra INTEGER (centavos):** Dificulta leitura e requer conversões constantes
- **Escala 15,2:** Suporta até 999 trilhões com centavos (máximo valor: R$ 24 bilhões)

**3.2 - Tipos de Dados para Datas: DATE vs VARCHAR vs TIMESTAMP**

**Escolha: Separar em VARCHAR(2) trimestre + VARCHAR(4) ano**

*Justificativa:*
- Dados ANS são trimestrais, não diários (não há dia específico)
- Formato original: "3T", "2025"
- Queries analíticas agrupam por trimestre/ano
- Facilita filtros: `WHERE ano = '2025' AND trimestre = '3T'`

*Alternativa descartada:*
- DATE: Forçaria escolha arbitrária de dia (01/07/2025 para 3T2025?)
- TIMESTAMP: Desnecessário para granularidade trimestral

**3.3 - Tratamento de Inconsistências na Importação**

| Problema | Estratégia | Implementação |
|----------|------------|---------------|
| NULLs em campos obrigatórios | Rejeitar linha | Constraints NOT NULL em CNPJ e razao_social |
| Strings em campos numéricos | Rejeitar automaticamente | PostgreSQL falha na conversão (behavior desejado) |
| Formatos de data inconsistentes | Validação com CHECK | `CHECK (trimestre IN ('1T','2T','3T','4T'))` |

*Filosofia:* Falha rápida é melhor que dados corrompidos. Fonte ANS é confiável, erros indicam problema no ETL.

**3.4 - Query 1 (Crescimento): Operadoras sem Dados em Todos Trimestres**

**Escolha: Considerar apenas operadoras com dados no primeiro E último trimestre**

*Justificativa:*
- Crescimento % = (último - primeiro) / primeiro × 100
- Operadora sem primeiro trimestre: divisão por zero
- Operadora sem último trimestre: crescimento incalculável
- Filtro: `HAVING COUNT(*) >= 2` garante pelo menos 2 pontos de comparação

*Resultado:* 5 operadoras com crescimento válido (de 370 possíveis)

**3.4 - Query 3 (Acima da Média): Abordagem de Implementação**

**Escolha: CTE (Common Table Expression) para calcular média global**

```sql
WITH media_geral AS (
    SELECT AVG(valor_despesas) as media
    FROM despesas_consolidadas
)
SELECT COUNT(DISTINCT cnpj) ...
WHERE valor_despesas > (SELECT media FROM media_geral)
GROUP BY cnpj
HAVING COUNT(*) >= 2
```

*Justificativa:*
- **Legibilidade:** CTE deixa lógica explícita (calcular média → filtrar → contar)
- **Performance:** PostgreSQL otimiza CTE automaticamente (não recalcula)
- **Manutenibilidade:** Fácil adicionar outras métricas (mediana, desvio padrão)

*Alternativas descartadas:*
- Subconsulta no WHERE: menos legível
- JOIN com agregação: mais complexo sem benefício
- Tabela temporária: overhead desnecessário

### Teste 4 - API e Interface Web

**4.2.1 - Framework Backend: Flask vs FastAPI**

**Escolha: FastAPI**

*Vantagens:*
- Documentação OpenAPI automática (/docs)
- Validação de tipos com Pydantic (reduz bugs)
- Async/await nativo (preparado para escalabilidade)
- Dependency injection (get_db) facilita testes

*Contra Flask:*
- Flask é mais simples, mas exigiria bibliotecas adicionais para validação e docs
- FastAPI oferece melhor DX (developer experience) para APIs REST modernas

**4.2.2 - Paginação: Offset vs Cursor vs Keyset**

**Escolha: Offset-based (page/limit)**

*Justificativa:*
- Volume: 791 operadoras → offset de até 79 (com limit=10)
- Performance: `OFFSET` em 800 registros é extremamente rápido
- UX: Usuário pode pular para página específica
- Simplicidade: Frontend não precisa gerenciar cursores

*Quando usar alternativas:*
- **Cursor-based:** Necessário para feeds infinitos (scroll infinito)
- **Keyset:** Necessário para milhões de registros com atualizações frequentes

**4.2.3 - Cache para /api/estatisticas**

**Escolha: Cache in-memory com TTL de 5 minutos**

*Justificativa:*
- Dados mudam trimestralmente (não em tempo real)
- Cálculo de agregações: ~50ms (3 queries com JOINs)
- Simplicidade: dicionário Python `{cache_key: (data, timestamp)}`
- Evita overhead de Redis/Memcached

*TTL de 5 minutos:*
- Balanceia consistência vs performance
- Mesmo com importação nova, 5min de defasagem é aceitável

*Alternativa descartada:*
- Pré-calcular em tabela: adiciona complexidade de sincronização
- Sem cache: desperdício recalcular mesma agregação a cada request

**4.2.4 - Estrutura de Resposta da API**

**Escolha: Envelope com metadados `{data, total, page, limit, pages}`**

*Justificativa:*
- Frontend precisa de `total` e `pages` para construir paginação
- Evita múltiplas requisições (uma para contar, outra para dados)
- Padrão comum em APIs REST (GitHub, Stripe, etc usam)

*Exemplo:*
```json
{
  "data": [...],
  "total": 791,
  "page": 1,
  "limit": 10,
  "pages": 80
}
```

**4.3.1 - Busca/Filtro: Servidor vs Cliente vs Híbrido**

**Escolha: Server-side (busca na API)**

*Justificativa:*
- Dataset pode crescer (hoje 791, futuro pode ter 5k+ operadoras)
- Aproveita índices do banco (BTREE em razao_social e cnpj)
- Reduz tráfego de rede (evita enviar 791 registros)
- Permite busca case-insensitive com ILIKE do PostgreSQL

*Contra client-side:*
- Carregar 791 registros no frontend: ~100KB + renderização lenta
- Sem índices, busca seria O(n) linear

**4.3.2 - Gerenciamento de Estado**

**Escolha: Props/Events + Composables Vue 3**

*Justificativa:*
- Aplicação simples: 4 views, estado não compartilhado entre rotas
- Composables para lógica reutilizável (ex: usePagination)
- Props/Events suficiente para comunicação pai-filho

*Contra Vuex/Pinia:*
- Overhead desnecessário (store global não traz benefício)
- Estado é efêmero: não precisa persistir entre navegações
- Adicionaria ~20% mais código sem ganho funcional

**4.3.3 - Performance da Tabela**

**Escolha: Paginação server-side (10-50 itens por página)**

*Justificativa:*
- Renderizar 10-20 linhas é instantâneo (<16ms)
- Virtual scrolling só faz sentido para milhares de itens visíveis
- Simplicidade: tabela HTML padrão do Bootstrap

*Alternativa descartada:*
- Virtual scrolling (vue-virtual-scroller): complexidade desnecessária
- Client-side pagination: exigiria carregar todos os dados primeiro

**4.3.4 - Tratamento de Erros e Loading**

**Estratégia Implementada:**

| Situação | Tratamento | Justificativa |
|----------|------------|---------------|
| Loading | Spinner + mensagem | Feedback visual claro durante requisição |
| Erro de rede | Alert vermelho + botão "Tentar novamente" | Permite retry sem reload da página |
| Dados vazios | Alert azul "Nenhum resultado" | Distingue erro de ausência de dados |
| Erro 404 | Mensagem específica "Operadora não encontrada" | Guia usuário (pode ter digitado CNPJ errado) |

*Mensagens específicas vs genéricas:*
- **Escolha:** Mensagens específicas
- **Justificativa:** Usuário técnico (analista de dados) precisa entender o problema
- Captura `error.response.data.detail` da API FastAPI

## Arquivos Gerados

- `consolidado_despesas.csv` - 827 registros de despesas
- `despesas_agregadas.csv` - 370 agregações por operadora/UF
- `operadoras_cadastro.csv` - 791 operadoras ativas
