# Teste simples do DriveBot v4.0
Start-Sleep 2

$headers = @{
    "Content-Type" = "application/json"
}

# Teste 1: Mensagem inicial
$payload1 = @{
    bot_id = "drivebot"
    message = "Olá"
} | ConvertTo-Json

Write-Host "Testando DriveBot v4.0..." -ForegroundColor Yellow

try {
    $response1 = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/chat" -Method POST -Body $payload1 -Headers $headers
    Write-Host "RESPOSTA RECEBIDA:" -ForegroundColor Green
    Write-Host $response1.response -ForegroundColor White
} catch {
    Write-Host "ERRO:" $_.Exception.Message -ForegroundColor Red
}

# Teste 2: Envio de ID
Write-Host "`nTestando descoberta de dados..." -ForegroundColor Yellow

$payload2 = @{
    bot_id = "drivebot"
    message = "1A2B3C4D5E6F7G8H9I0J"
} | ConvertTo-Json

try {
    $response2 = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/chat" -Method POST -Body $payload2 -Headers $headers
    Write-Host "RESPOSTA DESCOBERTA:" -ForegroundColor Green
    Write-Host $response2.response -ForegroundColor White
} catch {
    Write-Host "ERRO:" $_.Exception.Message -ForegroundColor Red
}