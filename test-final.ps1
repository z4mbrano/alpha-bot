# Teste Final - Verificação das Especificações Exatas

Write-Host "=== TESTE FINAL DOS BOTS ATUALIZADOS ===" -ForegroundColor Green
Write-Host ""

# Teste DriveBot com pergunta normal (não ID)
Write-Host "1. Testando DriveBot com pergunta normal..." -ForegroundColor Yellow
$headers = @{ "Content-Type" = "application/json" }
$body = @{
    "bot_id" = "drivebot"
    "message" = "Como você pode me ajudar?"
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/chat" -Method POST -Headers $headers -Body $body
    $content = ($response.Content | ConvertFrom-Json).response
    Write-Host "Resposta DriveBot (pergunta normal):" -ForegroundColor Cyan
    Write-Host $content
    Write-Host ""
} catch {
    Write-Host "Erro: $($_.Exception.Message)" -ForegroundColor Red
}

# Teste DriveBot com ID válido
Write-Host "2. Testando DriveBot com ID da pasta..." -ForegroundColor Yellow
$body = @{
    "bot_id" = "drivebot"
    "message" = "1hbWmhtJj2VwADiQbSELpxYTDs7Y8gJzb"
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/chat" -Method POST -Headers $headers -Body $body
    $content = ($response.Content | ConvertFrom-Json).response
    Write-Host "Resposta DriveBot (ID detectado):" -ForegroundColor Cyan
    Write-Host $content
    Write-Host ""
} catch {
    Write-Host "Erro: $($_.Exception.Message)" -ForegroundColor Red
}

# Teste AlphaBot com pergunta normal
Write-Host "3. Testando AlphaBot com pergunta normal..." -ForegroundColor Yellow
$body = @{
    "bot_id" = "alphabot"
    "message" = "Oi, como você funciona?"
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/chat" -Method POST -Headers $headers -Body $body
    $content = ($response.Content | ConvertFrom-Json).response
    Write-Host "Resposta AlphaBot (pergunta normal):" -ForegroundColor Cyan
    Write-Host $content
    Write-Host ""
} catch {
    Write-Host "Erro: $($_.Exception.Message)" -ForegroundColor Red
}

# Teste AlphaBot com menção de anexos
Write-Host "4. Testando AlphaBot com anexos..." -ForegroundColor Yellow
$body = @{
    "bot_id" = "alphabot"
    "message" = "Acabei de anexar uma planilha xlsx"
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/chat" -Method POST -Headers $headers -Body $body
    $content = ($response.Content | ConvertFrom-Json).response
    Write-Host "Resposta AlphaBot (anexo detectado):" -ForegroundColor Cyan
    Write-Host $content
    Write-Host ""
} catch {
    Write-Host "Erro: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "=== TESTES CONCLUÍDOS ===" -ForegroundColor Green