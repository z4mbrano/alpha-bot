# Teste DriveBot v3.0 - Validação do Manual de Operação

Write-Host "=== TESTE DRIVEBOT V3.0 ===" -ForegroundColor Green
Write-Host ""

$headers = @{ "Content-Type" = "application/json" }

# Teste 1: URL completa do Google Drive
Write-Host "1. Testando com URL completa do Google Drive..." -ForegroundColor Yellow
$body = @{
    "bot_id" = "drivebot"
    "message" = "https://drive.google.com/drive/folders/1hbWmhtJj2VwADiQbSELpxYTDs7Y8gJzb?usp=sharing"
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/chat" -Method POST -Headers $headers -Body $body
    $content = ($response.Content | ConvertFrom-Json).response
    Write-Host "Resposta (URL completa):" -ForegroundColor Cyan
    Write-Host $content
    Write-Host ""
} catch {
    Write-Host "Erro: $($_.Exception.Message)" -ForegroundColor Red
}

# Teste 2: ID direto
Write-Host "2. Testando com ID direto..." -ForegroundColor Yellow
$body = @{
    "bot_id" = "drivebot"
    "message" = "1hbWmhtJj2VwADiQbSELpxYTDs7Y8gJzb"
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/chat" -Method POST -Headers $headers -Body $body
    $content = ($response.Content | ConvertFrom-Json).response
    Write-Host "Resposta (ID direto):" -ForegroundColor Cyan
    Write-Host $content
    Write-Host ""
} catch {
    Write-Host "Erro: $($_.Exception.Message)" -ForegroundColor Red
}

# Teste 3: Pergunta após análise (simulando framework Analista-Crítico-Júri)
Write-Host "3. Testando pergunta analítica..." -ForegroundColor Yellow
$body = @{
    "bot_id" = "drivebot"
    "message" = "Qual foi o faturamento total em janeiro?"
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/chat" -Method POST -Headers $headers -Body $body
    $content = ($response.Content | ConvertFrom-Json).response
    Write-Host "Resposta (pergunta analítica):" -ForegroundColor Cyan
    Write-Host $content
    Write-Host ""
} catch {
    Write-Host "Erro: $($_.Exception.Message)" -ForegroundColor Red
}

# Teste 4: Pergunta impossível (para testar explicação clara)
Write-Host "4. Testando pergunta impossível..." -ForegroundColor Yellow
$body = @{
    "bot_id" = "drivebot"
    "message" = "Qual é a margem de lucro por produto?"
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/chat" -Method POST -Headers $headers -Body $body
    $content = ($response.Content | ConvertFrom-Json).response
    Write-Host "Resposta (pergunta impossível):" -ForegroundColor Cyan
    Write-Host $content
    Write-Host ""
} catch {
    Write-Host "Erro: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "=== TESTES CONCLUÍDOS ===" -ForegroundColor Green