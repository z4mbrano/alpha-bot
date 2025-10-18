# Test AlphaBot com menção de arquivos anexados
$headers = @{
    "Content-Type" = "application/json"
}

$body = @{
    "bot_id" = "alphabot"
    "message" = "Acabei de enviar 3 planilhas xlsx com dados de vendas. Pode analisar?"
} | ConvertTo-Json

try {
    Write-Host "Testando AlphaBot com anexos..."
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/chat" -Method POST -Headers $headers -Body $body
    
    Write-Host "Status: $($response.StatusCode)"
    Write-Host "Response:"
    $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 3
} catch {
    Write-Host "Erro: $($_.Exception.Message)"
}