# Teste DriveBot v4.0 - Data-Agnostic
# Script para validar o novo comportamento do DriveBot v4.0

Write-Host "🚀 TESTE DRIVEBOT V4.0 - ABORDAGEM DATA-AGNOSTIC" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

$headers = @{
    "Content-Type" = "application/json"
}

$baseUrl = "http://localhost:5000/api/chat"

# Teste 1: Mensagem inicial data-agnostic
Write-Host "`n1️⃣ TESTE: Mensagem inicial do DriveBot v4.0" -ForegroundColor Yellow

$payload1 = @{
    bot_id = "drivebot"
    message = "Olá"
} | ConvertTo-Json

try {
    $response1 = Invoke-RestMethod -Uri $baseUrl -Method POST -Body $payload1 -Headers $headers
    Write-Host "✅ RESPOSTA RECEBIDA:" -ForegroundColor Green
    Write-Host $response1.response -ForegroundColor White
} catch {
    Write-Host "❌ ERRO: $($_.Exception.Message)" -ForegroundColor Red
}

# Teste 2: Envio de ID para descoberta
Write-Host "`n2️⃣ TESTE: Envio de ID da pasta para descoberta dos dados" -ForegroundColor Yellow

$payload2 = @{
    bot_id = "drivebot"
    message = "1A2B3C4D5E6F7G8H9I0J"
} | ConvertTo-Json

try {
    $response2 = Invoke-RestMethod -Uri $baseUrl -Method POST -Body $payload2 -Headers $headers
    Write-Host "✅ RESPOSTA RECEBIDA:" -ForegroundColor Green
    Write-Host $response2.response -ForegroundColor White
} catch {
    Write-Host "❌ ERRO: $($_.Exception.Message)" -ForegroundColor Red
}

# Teste 3: Pergunta usando campos descobertos
Write-Host "`n3️⃣ TESTE: Pergunta baseada na estrutura descoberta" -ForegroundColor Yellow

$payload3 = @{
    bot_id = "drivebot"
    message = "Qual é o valor_venda total por regiao_venda?"
} | ConvertTo-Json

try {
    $response3 = Invoke-RestMethod -Uri $baseUrl -Method POST -Body $payload3 -Headers $headers
    Write-Host "✅ RESPOSTA RECEBIDA:" -ForegroundColor Green
    Write-Host $response3.response -ForegroundColor White
} catch {
    Write-Host "❌ ERRO: $($_.Exception.Message)" -ForegroundColor Red
}

# Teste 4: Pergunta com campo inexistente (teste de limitações)
Write-Host "`n4️⃣ TESTE: Pergunta com campo não descoberto (teste de limitações)" -ForegroundColor Yellow

$payload4 = @{
    bot_id = "drivebot"
    message = "Qual é o lucro líquido por trimestre?"
} | ConvertTo-Json

try {
    $response4 = Invoke-RestMethod -Uri $baseUrl -Method POST -Body $payload4 -Headers $headers
    Write-Host "✅ RESPOSTA RECEBIDA:" -ForegroundColor Green
    Write-Host $response4.response -ForegroundColor White
} catch {
    Write-Host "❌ ERRO: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n🎯 ANÁLISE DOS TESTES:" -ForegroundColor Cyan
Write-Host "- Teste 1: Verifica se a mensagem inicial reflete a filosofia data-agnostic" -ForegroundColor White
Write-Host "- Teste 2: Valida o processo de descoberta e mapeamento dos dados" -ForegroundColor White  
Write-Host "- Teste 3: Confirma uso da terminologia descoberta nos campos" -ForegroundColor White
Write-Host "- Teste 4: Testa resposta a limitações baseadas na estrutura descoberta" -ForegroundColor White

Write-Host "`n🚀 DRIVEBOT V4.0 - FILOSOFIA DATA-AGNOSTIC IMPLEMENTADA!" -ForegroundColor Green