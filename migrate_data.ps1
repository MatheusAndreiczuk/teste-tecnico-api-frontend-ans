Write-Host "`n=== Migracao de Dados para PostgreSQL ==="

$containerName = docker-compose ps -q db
if (-not $containerName) {
    Write-Host "Erro: Container do banco nao esta rodando." -ForegroundColor Red
    Write-Host "Execute primeiro: docker-compose up -d" -ForegroundColor Yellow
    exit 1
}

$csvPath = "data/processed"
if (-not (Test-Path "$csvPath/consolidado_despesas.csv")) {
    Write-Host "Erro: CSVs nao encontrados em $csvPath" -ForegroundColor Red
    Write-Host "Execute primeiro: python run_etl.py" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n[1/4] Copiando CSVs para o container..." -ForegroundColor Yellow
docker cp "$csvPath/consolidado_despesas.csv" "${containerName}:/tmp/consolidado_despesas.csv"
docker cp "$csvPath/operadoras_cadastro.csv" "${containerName}:/tmp/operadoras_cadastro.csv"

Write-Host "[2/4] Criando tabelas..." -ForegroundColor Yellow
Get-Content sql/01_create_tables.sql | docker-compose exec -T db psql -U postgres -d ans_data

Write-Host "[3/4] Importando dados..." -ForegroundColor Yellow
Get-Content sql/02_import_data.sql | docker-compose exec -T db psql -U postgres -d ans_data

Write-Host "[4/4] Verificando importacao..." -ForegroundColor Yellow
docker-compose exec -T db psql -U postgres -d ans_data -c "SELECT 'Operadoras' as tabela, COUNT(*) as registros FROM operadoras_cadastro UNION ALL SELECT 'Despesas', COUNT(*) FROM despesas_consolidadas UNION ALL SELECT 'Agregados', COUNT(*) FROM despesas_agregadas;"

Write-Host "`n=== Migracao concluida com sucesso! ===" -ForegroundColor Green
