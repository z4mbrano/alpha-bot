# Test DriveBot com ID de pasta simulado
$headers = @{
    "Content-Type" = "application/json"
}

$body = @{
    "bot_id" = "drivebot"
    "message" = "1hbWmhtJj2VwADiQbSELpxYTDs7Y8gJzb?hl"
} | ConvertTo-Json

try {
    Write-Host "Testando DriveBot com ID da pasta..."
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/chat" -Method POST -Headers $headers -Body $body
    
    Write-Host "Status: $($response.StatusCode)"
    Write-Host "Response:"
    $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 3
} catch {
    Write-Host "Erro: $($_.Exception.Message)"
}