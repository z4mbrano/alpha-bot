# Test script para testar a API do chat
$headers = @{
    "Content-Type" = "application/json"
}

$body = @{
    "bot_id" = "alphabot"
    "message" = "Olá! Como você pode me ajudar com análises de vendas?"
} | ConvertTo-Json

try {
    Write-Host "Testando endpoint /api/chat..."
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/chat" -Method POST -Headers $headers -Body $body
    
    Write-Host "Status: $($response.StatusCode)"
    Write-Host "Response:"
    $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 3
} catch {
    Write-Host "Erro: $($_.Exception.Message)"
}